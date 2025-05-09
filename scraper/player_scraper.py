import os
import json
import asyncio
from playwright.async_api import async_playwright, Page
import pandas as pd
from functools import reduce

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 0)

# === TAB CONFIGURATION ===
TAB_RATING = {
    "General": {
        "columns": ["Year", "MP", "MIN", "GLS", "AST", "ASR"],
        "drop_index": None
    },
}

TAB_GK_RATING = {
    "General": {
        "columns": ["Year", "MP", "MIN", "CLS", "GC", "ASR"],
        "drop_index": None
    },
}

TAB_CONFIG_OUTFIELD = {
    "General": {
        "columns": ["Year", "MP", "MIN", "GLS", "AST", "ASR"],
        "drop_index": None
    },
    "Shooting": {
        "columns": ["Year", "MP", "GLS", "TOS", "SOT", "BCM"],
        "drop_index": None
    },
    # "Team play": {
    #     "columns": ["Year", "MP", "AST", "KEYP", "BCC", "SDR"],
    #     "drop_index": None
    # },
    # "Passing": {
    #     "columns": ["Year", "APS", "APS%", "ALB", "LBA%", "ACR", "CA%"],
    #     "drop_index": 0
    # },
    # "Defending": {
    #     "columns": ["Year", "CLS", "YC", "RC", "ELTG", "DRP", "TACK", "INT", "BLS", "ADW"],
    #     "drop_index": 0
    # },
    # "Additional": {
    #     "columns": ["Year", "GLS", "xG", "AST", "XA", "GI", "XGI"],
    #     "drop_index": 0
    # },
}

TAB_CONFIG_GOALKEEPER = {
    "General": {
        "columns": ["Year", "MP", "MIN", "CLS", "GC", "ASR"],
        "drop_index": None
    },
    # "Goalkeeping": {
    #     "columns": ["Year", "MP", "SAV", "SAV%", "PS", "PS%"],
    #     "drop_index": None
    # },
    # "Passing": {
    #     "columns": ["Year", "APS", "APS%", "ALB", "LBA%"],
    #     "drop_index": 0
    # },
    # "Defending": {
    #     "columns": ["Year", "CLS", "YC", "RC", "ELTG", "DRP", "TACK", "INT", "ADW"],
    #     "drop_index": 0
    # },
    # "Additional": {
    #     "columns": ["Year", "GC", "xGC", "GP"],
    #     "drop_index": 0
    # },
}

# === HELPER: Click a tab by name ===
async def click_tab(page: Page, tab_name: str):
    try:
        tab = await page.wait_for_selector(f"button:has-text('{tab_name}')", timeout=5000)
        await tab.scroll_into_view_if_needed()
        await page.wait_for_timeout(500)
        await tab.click()
    except Exception as e:
        print(f"⚠️ Could not click tab '{tab_name}': {e}")

# === HELPER: Collapse first season row ===
async def collapse_first_season_row(page: Page):
    try:
        expand_arrow = await page.query_selector(".Box.Flex.jBQtbp.cQgcrM")
        if expand_arrow:
            await expand_arrow.click()
            await page.wait_for_timeout(1000)
    except Exception as e:
        print(f"⚠️ Failed to collapse first row: {e}")

# === HELPER: Combine tables ===
def combine_stat_tables(all_dataframes: dict[str, pd.DataFrame], position: str) -> pd.DataFrame:
    """
    Merge all tab-specific DataFrames on 'Year', renaming columns to avoid collisions.
    Handles ASR from 'General_rating' by merging into 'General'.
    """
    suffix = "GK" if position == "Goalkeeper" else "OF"

    # Step 1: If 'General_rating' exists, merge its ASR column into 'General'
    if "General_rating" in all_dataframes:
        df_rating = all_dataframes["General_rating"]
        if "ASR" in df_rating.columns and df_rating["ASR"].notna().any():
            if "General" in all_dataframes:
                df_general = all_dataframes["General"]
                if "ASR" in df_general.columns:
                    df_general = df_general.drop(columns=["ASR"])
                df_general = pd.merge(df_general, df_rating[["Year", "ASR"]], on="Year", how="outer")
                all_dataframes["General"] = df_general
            else:
                all_dataframes["General"] = df_rating
        del all_dataframes["General_rating"]

    # Step 2: Rename columns for each tab
    renamed_dfs = []
    for tab_name, df in all_dataframes.items():
        if df.empty:
            continue
        renamed = df.copy()
        renamed.columns = [
            f"{tab_name}_{suffix}_{col}" if col != "Year" else "Year"
            for col in df.columns
        ]
        renamed_dfs.append(renamed)

    # Step 3: Outer join across all tabs
    if not renamed_dfs:
        return pd.DataFrame()

    df_final = reduce(lambda left, right: pd.merge(left, right, on="Year", how="outer"), renamed_dfs)
    return df_final

# === GENERIC TABLE SCRAPER ===
async def scrape_stat_table(
    page: Page,
    columns: list[str],
    tab_name: str,
    mode: str = "default",
    position: str = "",
    drop_index: int | None = None,
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

    # ---------- SPECIAL CASE: rating column ------------------------------
    if mode == "rating":
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
    # ---------------------------------------------------------------------

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


# === MAIN SCRAPER ===
async def scrape_player_stats(sofascore_name, player_id, position):
    url = f"https://www.sofascore.com/player/{sofascore_name}/{player_id}"
    print(f"🔗 Opening: {url}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            # args=["--disable-gpu", "--no-sandbox"]
        )
        # browser = await p.chromium.launch(
        #     headless=True,
        #     args=["--disable-gpu", "--no-sandbox"]
        # )

        page = await browser.new_page()
        await page.goto(url)

        # Cookie consent
        try:
            await page.wait_for_selector("button:has-text('Consent')", timeout=5000)
            await page.click("button:has-text('Consent')")
            await page.wait_for_timeout(1000)
        except:
            print("⚠️ No cookie popup.")

        await click_tab(page, "General")
        await collapse_first_season_row(page)

        # Loop through stat tabs
        all_dataframes = {}
        TAB_CONFIG = TAB_CONFIG_GOALKEEPER if position == "Goalkeeper" else TAB_CONFIG_OUTFIELD
        for tab_name, config in TAB_CONFIG.items():
            await click_tab(page, tab_name)
            df = await scrape_stat_table(
                page=page,
                columns=config["columns"],
                tab_name=tab_name,
                mode="default",
                position=position,
                drop_index=config.get("drop_index"),
                n_rows=2
            )
            all_dataframes[tab_name] = df

        # Rating tab (deep nested span)
        TAB_RATING_ACTIVE = TAB_GK_RATING if position == "Goalkeeper" else TAB_RATING
        for tab_name, config in TAB_RATING_ACTIVE.items():
            df = await scrape_stat_table(
                page=page,
                columns=config["columns"],
                tab_name=tab_name,
                mode="rating",
                position=position,
                drop_index=config.get("drop_index"),
                n_rows=2
            )
            all_dataframes[f"{tab_name}_rating"] = df

        df_merged = combine_stat_tables(all_dataframes, position)

        await asyncio.sleep(2)
        await browser.close()

        return df_merged

# === ENTRY POINT ===
if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, "config", "players.json")
    with open(json_path, "r") as f:
        data = json.load(f)
    players = [p for p in data["players"] if p.get("to_scrape", False)]

    for player in players:
        print(f"\n🚀 Scraping stats for {player['sofascore_name']} (ID: {player['id']})")
        df = asyncio.run(
            scrape_player_stats(
                sofascore_name=player['sofascore_name'],
                player_id=player['id'],
                position=player['position'],
            )
        )
        print('--------------------------------')
        print(df)