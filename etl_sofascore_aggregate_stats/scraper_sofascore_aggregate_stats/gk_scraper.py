"""
gk_scraper.py
=============
Scrapes Sofascore season statistics for **goalkeepers** only.

Assumes the following helpers exist in utils.py
------------------------------------------------
async def open_sofascore(url: str) -> playwright.async_api.Page
async def click_tab(page: Page, name: str)
async def collapse_first_row_if_open(page: Page)
"""

import asyncio
import pandas as pd
from etl_sofascore_aggregate_stats.scraper_sofascore_aggregate_stats.utils import combine_stat_tables, click_tab, collapse_first_season_row
from playwright.async_api import async_playwright, Page
from etl_sofascore_aggregate_stats.scraper_sofascore_aggregate_stats.utils import load_players_from_team_files

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 0)

# ------------------------------------------------------------------ #
#  1 · TAB CONFIG                                                    #
# ------------------------------------------------------------------ #
TAB_CONFIG_GOALKEEPER = {
    "General": {
        "columns": ["Year", "MP", "MIN", "CLS", "GC", "ASR"],
        "drop_index": None
    },
    "Goalkeeping": {
        "columns": ["Year", "MP", "SAV", "SAV%", "PS", "PS%"],
        "drop_index": None
    },
    "Passing": {
        "columns": ["Year", "APS", "APS%", "ALB", "LBA%"],
        "drop_index": 0
    },
    "Defending": {
        "columns": ["Year", "CLS", "YC", "RC", "ELTG", "DRP", "TACK", "INT", "ADW"],
        "drop_index": 0
    },
    "Additional": {
        "columns": ["Year", "GC", "xGC", "GP"],
        "drop_index": 0
    },
}

TAB_GK_RATING = {
    "General": {
        "columns": ["Year", "MP", "MIN", "CLS", "GC", "ASR"],
        "drop_index": None,
    },
}

# ------------------------------------------------------------------ #
#  2 · LOW-LEVEL EXTRACTORS                                          #
# ------------------------------------------------------------------ #
async def scrape_stat_table(
    page: Page,
    columns: list[str],
    drop_index: int | None = None,
    n_rows: int = 100
) -> pd.DataFrame:
    await page.wait_for_selector(".Box.feDCzw.crsNnE", timeout=10000)

    # ---- Step 1: seasons (years) – used by both modes --------------------
    year_spans = await page.query_selector_all(
        ".Box.feDCzw.crsNnE .Box.gQIPzn.fRroAj span"
    )
    years = [await y.inner_text() for y in year_spans if "/" in await y.inner_text()]
    years = years[:n_rows]                                   # keep ≤ n_rows

    # ---- Step 2 & 3: normal stat rows -----------------------------------
    stat_rows = await page.query_selector_all(
        ".Box.hMcCqO.sc-c2c19408-0.cFPbZB .Box.ggRYVx.iWGVcA .Box.cQgcrM"
    )
    data: list[list[str | None]] = []

    for row in stat_rows[:n_rows]:
        stat_cells = await row.query_selector_all(".Box.jNHkiI.kFvGEE")
        stats: list[str | None] = []

        for cell in stat_cells:
            val = None
            span = await cell.query_selector("span")
            if span:
                txt = (await span.inner_text()).strip()
                if txt not in {"", "-"}:
                    val = txt
            stats.append(val)

        if drop_index is not None and len(stats) > drop_index:
            stats = stats[:drop_index] + stats[drop_index + 1:]

        data.append(stats)

    combined_rows = [[year] + stat_row for year, stat_row in zip(years, data)]
    df = pd.DataFrame(combined_rows, columns=columns)
    return df

async def scrape_rating_table(
    page: Page,
    n_rows: int = 100
) -> pd.DataFrame:
    """
    When mode == "default": identical behaviour as before.
    When mode == "rating":  ignore the per-cell loop and pull the ASR column
                            directly with span[role='meter'] selector. Works
                            for every position because the rating pill is
                            rendered the same way for all players.
    """
    """Scrapes the rating table, ensuring we only get season-level ratings."""
    await page.wait_for_selector(".Box.feDCzw.crsNnE", timeout=10_000)

    # First get all the years/seasons
    year_spans = await page.query_selector_all(
        ".Box.feDCzw.crsNnE .Box.gQIPzn.fRroAj span"
    )
    years = [await y.inner_text() for y in year_spans if "/" in await y.inner_text()]
    years = years[:n_rows]

    # Get rating elements using the selector that we know works
    rating_elements = await page.query_selector_all(
        "div.Box.Flex.ggRYVx.iWGVcA > div.Box.Flex.ggRYVx.cQgcrM > div.Box.Flex.jNHkiI.kFvGEE span[role='meter']"
    )

    # Extract the rating values
    ratings = []
    for el in rating_elements[:len(years)]:
        value = await el.get_attribute("aria-valuenow")
        ratings.append(value)

    # Create rows combining years and ratings
    rows = [[year, rating] for year, rating in zip(years, ratings)]

    # Add None for any missing ratings
    while len(rows) < len(years):
        rows.append([years[len(rows)], None])

    return pd.DataFrame(rows, columns=["Year", "ASR"])


# ------------------------------------------------------------------ #
#  3 · PUBLIC ENTRY POINT                                            #
# ------------------------------------------------------------------ #
# === MAIN SCRAPER : goalkeeper-only =======================================
async def scrape_goalkeeper(sofascore_name: str, player_id: int) -> pd.DataFrame:
    """
    Scrapes season-level stats for a goalkeeper using the tab/column definitions
    in TAB_CONFIG_GOALKEEPER and TAB_GK_RATING.
    """
    url = f"https://www.sofascore.com/player/{sofascore_name}/{player_id}"
    print(f"🔗 Opening: {url}")

    async with async_playwright() as p:
        # browser = await p.chromium.launch(headless=False,)
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-gpu", "--no-sandbox"],
        )

        page = await browser.new_page()
        await page.goto(url)

        # --- cookie banner --------------------------------------------------
        try:
            await page.wait_for_selector("button:has-text('Consent')", timeout=5000)
            await page.click("button:has-text('Consent')")
            await page.wait_for_timeout(1000)
        except:
            print("⚠️ No cookie popup.")

        # --- navigate to the General tab -----------------------------------
        await click_tab(page, "General")
        await collapse_first_season_row(page)

        # --- scrape every tab defined for goalkeepers ----------------------
        all_dataframes: dict[str, pd.DataFrame] = {}

        # --- rating column (ASR) ------------------------------------------
        for tab_name, cfg in TAB_GK_RATING.items():
            df_rating = await scrape_rating_table(
                page=page,
                n_rows=100,
            )

            all_dataframes[f"{tab_name}_rating"] = df_rating

        for tab_name, cfg in TAB_CONFIG_GOALKEEPER.items():
            await click_tab(page, tab_name)
            df = await scrape_stat_table(
                page=page,
                columns=cfg["columns"],
                drop_index=cfg.get("drop_index"),
                n_rows=100,
            )
            all_dataframes[tab_name] = df


        # # --- merge & return -----------------------------------------------
        df_merged = combine_stat_tables(all_dataframes, position="Goalkeeper")

        await browser.close()
        return df_merged

# ------------------------------------------------------------------ #
#  4 · Test hook (run this file directly)                            #
# ------------------------------------------------------------------ #
if __name__ == "__main__":
    players = load_players_from_team_files()

    if not players:
        print("No players marked with 'to_scrape': true")
        raise SystemExit

    # --- subset to goalkeepers flagged for scraping -------------------------
    goalkeepers = [
        p for p in players
        if p.get("to_scrape", False) and p.get("position") == "Goalkeeper"
    ]

    # --- scrape each keeper -------------------------------------------------
    for p in goalkeepers:
        print(f"\n🚀 Scraping GK stats for {p['sofascore_name']} (ID: {p['id']})")

        df = asyncio.run(
            scrape_goalkeeper(
                sofascore_name=p["sofascore_name"],
                player_id=p["id"],
            )
        )

        print("-" * 32)
        print(df)

