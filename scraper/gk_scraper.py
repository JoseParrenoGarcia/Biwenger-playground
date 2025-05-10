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
import os
import json
import pandas as pd
from utils import combine_stat_tables, click_tab, collapse_first_season_row
from playwright.async_api import async_playwright, Page

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
    await page.wait_for_selector(".Box.feDCzw.crsNnE", timeout=10000)

    # ---- Step 1: seasons (years) – used by both modes --------------------
    year_spans = await page.query_selector_all(
        ".Box.feDCzw.crsNnE .Box.gQIPzn.fRroAj span"
    )
    years = [await y.inner_text() for y in year_spans if "/" in await y.inner_text()]
    years = years[:n_rows]                                   # keep ≤ n_rows

    # Wait until at least one rating pill is rendered
    await page.wait_for_selector("span[role='meter']", timeout=5000)

    # Pull every aria-valuenow in DOM order (top season ➜ bottom season)
    asr_values = await page.eval_on_selector_all(
        "span[role='meter']",
        "els => els.map(e => e.getAttribute('aria-valuenow') || "
        "                     (e.innerText.trim() || null))"
    )
    # Trim / pad to match number of seasons we captured
    asr_values = (asr_values + [None] * len(years))[:len(years)]

    rows = [[y, v] for y, v in zip(years, asr_values)]
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
        await click_tab(page, "Goalkeeping")
        await click_tab(page, "Attacking")


        # --- scrape every tab defined for goalkeepers ----------------------
        all_dataframes: dict[str, pd.DataFrame] = {}

        for tab_name, cfg in TAB_CONFIG_GOALKEEPER.items():
            await click_tab(page, tab_name)
            df = await scrape_stat_table(
                page=page,
                columns=cfg["columns"],
                drop_index=cfg.get("drop_index"),
                n_rows=2,
            )
            all_dataframes[tab_name] = df

        # --- rating column (ASR) ------------------------------------------
        for tab_name, cfg in TAB_GK_RATING.items():
            df_rating = await scrape_rating_table(
                page=page,
                n_rows=2,
            )
            all_dataframes[f"{tab_name}_rating"] = df_rating

        # --- merge & return -----------------------------------------------
        df_merged = combine_stat_tables(all_dataframes, position="Goalkeeper")

        await asyncio.sleep(4)
        await browser.close()
        return df_merged




# ------------------------------------------------------------------ #
#  4 · Test hook (run this file directly)                            #
# ------------------------------------------------------------------ #
if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, "config", "players.json")
    with open(json_path, "r") as f:
        data = json.load(f)

    # --- subset to goalkeepers flagged for scraping -------------------------
    goalkeepers = [
        p for p in data["players"]
        if p.get("to_scrape", False) and p.get("position") == "Goalkeeper"
    ]

    if not goalkeepers:
        print("No goalkeepers marked with 'to_scrape': true")
        raise SystemExit

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

