from playwright.async_api import async_playwright, Page
import os
import json

# ---------- browser context ----------
async def open_sofascore(url: str) -> Page:
    p = await async_playwright().start()
    browser = await p.chromium.launch(headless=True, args=["--disable-gpu"])
    page = await browser.new_page()
    await page.goto(url)
    # Accept cookies if present
    try:
        await page.click("button:has-text('Consent')", timeout=4000)
    except:
        pass
    return page

# ---------- ui helpers ----------
async def click_tab(page: Page, name: str):
    btn = await page.wait_for_selector(f"button:has-text('{name}')", timeout=6000)
    await btn.scroll_into_view_if_needed()
    await btn.click()

async def collapse_first_season_row(page: Page):
    try:
        expand_arrow = await page.query_selector(".Box.Flex.jBQtbp.cQgcrM")
        if expand_arrow:
            await expand_arrow.click()
            await page.wait_for_timeout(1000)
    except Exception as e:
        print(f"⚠️ Failed to collapse first row: {e}")

from functools import reduce
import pandas as pd

def combine_stat_tables(
    all_dataframes: dict[str, pd.DataFrame],
    position: str = "Goalkeeper",
) -> pd.DataFrame:
    """
    Merge tab-specific DataFrames on 'Year', adding a suffix (GK/OF) to every
    stat column to avoid name collisions.

    Parameters
    ----------
    all_dataframes : {"tab name": DataFrame}
        Output of the scraping loop, e.g. {"General": df_gen, "Shooting": df_shoot}
    position : {"Goalkeeper", "Outfield"}
        Used only to choose the suffix for column names.

    Returns
    -------
    pd.DataFrame
        One row per season, outer-joined across all tabs.
    """
    suffix = "GK" if position == "Goalkeeper" else "OF"

    # ── 1 · Rename columns per tab ───────────────────────────────────────
    renamed_dfs: list[pd.DataFrame] = []
    for tab_name, df in all_dataframes.items():
        if df.empty:
            continue

        renamed = df.copy()
        renamed.columns = [
            f"{tab_name}_{suffix}_{col}" if col != "Year" else "Year"
            for col in df.columns
        ]
        renamed_dfs.append(renamed)

    if not renamed_dfs:
        return pd.DataFrame()

    # ── 2 · Outer-join on Year ───────────────────────────────────────────
    df_final = reduce(
        lambda left, right: pd.merge(left, right, on="Year", how="outer"),
        renamed_dfs,
    )

    # ── 3 · Drop duplicate columns (can happen if two tabs both have 'ASR_GK') ──
    df_final = df_final.loc[:, ~df_final.columns.duplicated()]

    # ── 4 · Drop empty rating column ──
    df_final = df_final.loc[:, ~df_final.columns.duplicated()]

    if position == "Goalkeeper":
        col_main = "General_GK_ASR"
        col_rating = "General_rating_GK_ASR"
    else:
        col_main = "General_OF_ASR"
        col_rating = "General_rating_OF_ASR"

    if col_main in df_final.columns and col_rating in df_final.columns:
        df_final.drop(columns=[col_main], inplace=True)

    return df_final


def load_players_from_team_files():
    """
    Load player data from individual team JSON files in the config/teams directory.
    Returns a list of all players with to_scrape=True.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    teams_dir = os.path.join(script_dir, "config")

    # Create the teams directory if it doesn't exist
    if not os.path.exists(teams_dir):
        os.makedirs(teams_dir)

    all_players = []

    # Get all JSON files in the teams directory
    for filename in os.listdir(teams_dir):
        if filename.endswith('.json'):
            team_file_path = os.path.join(teams_dir, filename)

            with open(team_file_path, 'r') as f:
                try:
                    team_data = json.load(f)
                    # Add players with to_scrape=True to our list
                    all_players.extend([
                        p for p in team_data.get("players", [])
                        if p.get("to_scrape", False)
                    ])
                except json.JSONDecodeError:
                    print(f"Error: Could not parse JSON in {filename}")

    return all_players