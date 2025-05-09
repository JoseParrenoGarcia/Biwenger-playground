import json
import os
import asyncio
from playwright.async_api import async_playwright, Page
import pandas as pd
from functools import reduce

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 0)

# === TAB CONFIGURATION ===
TAB_CONFIG_OUTFIELD = {
    "General": {
        "columns": ["Year", "MP", "MIN", "GLS", "AST", "ASR"],
        "drop_index": None
    },
    "Shooting": {
        "columns": ["Year", "MP", "GLS", "TOS", "SOT", "BCM"],
        "drop_index": None
    },
    "Team play": {
        "columns": ["Year", "MP", "AST", "KEYP", "BCC", "SDR"],
        "drop_index": None
    },
    "Passing": {
        "columns": ["Year", "APS", "APS%", "ALB", "LBA%", "ACR", "CA%"],
        "drop_index": 0
    },
    "Defending": {
        "columns": ["Year", "CLS", "YC", "RC", "ELTG", "DRP", "TACK", "INT", "BLS", "ADW"],
        "drop_index": 0
    },
    "Additional": {
        "columns": ["Year", "GLS", "xG", "AST", "XA", "GI", "XGI"],
        "drop_index": 0
    },
}

TAB_CONFIG_GOALKEEPER = {
    "General": {
        "columns": ["Year", "MP", "MIN", "CLS", "GC", "ASR"],
        "drop_index": None
    },
    "Goalkeeping": {
        "columns": ["Year", "MP", "SAV", "SAV%", "PS", "PS%"],
        "drop_index": None
    },
}

# === HELPER: Click a tab by name ===
async def click_tab(page: Page, tab_name: str):
    try:
        tab = await page.wait_for_selector(f"button:has-text('{tab_name}')", timeout=5000)
        await tab.scroll_into_view_if_needed()
        await page.wait_for_timeout(500)
        await tab.click()
        # print(f"📌 Clicked '{tab_name}' tab.")
    except Exception as e:
        print(f"⚠️ Could not click tab '{tab_name}': {e}")

# === HELPER: Collapse first season row ===
async def collapse_first_season_row(page: Page):
    try:
        expand_arrow = await page.query_selector(".Box.Flex.jBQtbp.cQgcrM")
        if expand_arrow:
            await expand_arrow.click()
            # print("⬇️ Collapsed first season row")
            await page.wait_for_timeout(1000)
    except Exception as e:
        print(f"⚠️ Failed to collapse first row: {e}")

# === HELPER: Combine tables ===
def combine_stat_tables(all_dataframes: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Merge all tab-specific DataFrames on 'Year', renaming columns to avoid collisions.
    Example:
        {"General": df1, "Shooting": df2} → merged DataFrame with columns like 'MP_General', 'MP_Shooting', etc.
    """
    renamed_dfs = []
    for tab_name, df in all_dataframes.items():
        renamed = df.copy()
        renamed.columns = [f"{tab_name}_{col}" if col != "Year" else "Year" for col in df.columns]
        renamed_dfs.append(renamed)

    if not renamed_dfs:
        return pd.DataFrame()

    df_final = reduce(lambda left, right: pd.merge(left, right, on="Year", how="outer"), renamed_dfs)
    return df_final

# === GENERIC TABLE SCRAPER ===
async def scrape_stat_table(page: Page, columns: list[str], drop_index: int | None = None, n_rows: int = 100) -> pd.DataFrame:
    await page.wait_for_selector(".Box.feDCzw.crsNnE", timeout=10000)

    # Step 1: Extract years
    year_spans = await page.query_selector_all(".Box.feDCzw.crsNnE .Box.gQIPzn.fRroAj span")
    years = []
    for y in year_spans:
        text = await y.inner_text()
        if "/" in text:
            years.append(text)

    # Step 2: Extract stat rows
    stat_rows = await page.query_selector_all(".Box.hMcCqO.sc-c2c19408-0.cFPbZB .Box.ggRYVx.iWGVcA .Box.cQgcrM")
    data = []
    for idx, row in enumerate(stat_rows):
        stat_cells = await row.query_selector_all(".Box.jNHkiI.kFvGEE")
        stats = []

        for cell in stat_cells:
            inner_span = await cell.query_selector("span")
            if inner_span:
                val = await inner_span.inner_text()
                stats.append(val.strip())
            else:
                stats.append(None)  # Placeholder/dash cell

        if drop_index is not None and len(stats) > drop_index:
            stats = stats[:drop_index] + stats[drop_index + 1:]

        data.append(stats)

    # print(data)

    # Step 3: Combine into DataFrame
    years_subset = years[:n_rows]
    stats_subset = data[:n_rows]
    combined_rows = [[year] + stat_row for year, stat_row in zip(years_subset, stats_subset)]
    df = pd.DataFrame(combined_rows, columns=columns)

    # print(df)

    return df

# === MAIN SCRAPER ===
async def scrape_player_stats(sofascore_name, player_id, position):
    url = f"https://www.sofascore.com/player/{sofascore_name}/{player_id}"
    print(f"🔗 Opening: {url}")

    async with async_playwright() as p:
        # browser = await p.chromium.launch(headless=False)

        browser = await p.chromium.launch(
            headless=True,  # ← no window will open
            args=[
                "--disable-gpu",  # (optional) quieter logs on some servers
                "--no-sandbox"  # (optional) needed inside Docker/GitHub CI
            ],
            # viewport={"width": 1280, "height": 800}  # keep a desktop layout
        )

        page = await browser.new_page()
        await page.goto(url)

        # Cookie consent
        try:
            await page.wait_for_selector("button:has-text('Consent')", timeout=5000)
            await page.click("button:has-text('Consent')")
            # print("✅ Cookie consent accepted.")
            await page.wait_for_timeout(1000)
        except:
            print("⚠️ No cookie popup.")

        # # Scroll to bottom to load dynamic elements
        # await page.evaluate("() => window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });")
        # await page.wait_for_timeout(3000)

        # Click first tab (General) and collapse
        await click_tab(page, "General")
        await collapse_first_season_row(page)

        # Loop through all configured tabs
        all_dataframes = {}
        TAB_CONFIG = TAB_CONFIG_GOALKEEPER if position == "Goalkeeper" else TAB_CONFIG_OUTFIELD
        for tab_name, config in TAB_CONFIG.items():
            await click_tab(page, tab_name)
            # print(tab_name)
            df = await scrape_stat_table(
                page=page,
                columns=config["columns"],
                drop_index=config.get("drop_index"),
                n_rows=2
            )

            all_dataframes[tab_name] = df

        df_merged = combine_stat_tables(all_dataframes)

        await asyncio.sleep(2)
        await browser.close()

        return df_merged


# === ENTRY POINT ===
if __name__ == "__main__":
    # Load player list
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, "config", "players.json")
    with open(json_path, "r") as f:
        data = json.load(f)
    players = [p for p in data["players"] if p.get("to_scrape", False)]

    # Loop through each player
    for player in players:
        print(f"\n🚀 Scraping stats for {player['sofascore_name']} (ID: {player['id']})")
        df = asyncio.run(
            scrape_player_stats(
                sofascore_name=player['sofascore_name'],
                player_id=player['id'],
                position=player['position'],
            )
        )
        print(df)
