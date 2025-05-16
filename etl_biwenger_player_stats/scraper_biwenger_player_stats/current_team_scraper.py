from etl_biwenger_player_stats.scraper_biwenger_player_stats.utils import (
    perform_login,
    load_credentials,
    save_players_to_csv,
    click_return_to_list,
    get_total_pages,
    click_next_pagination_arrow,
    scroll_into_view
)
import pandas as pd
from playwright.sync_api import sync_playwright
import time
from rich.console import Console

console = Console()

def scrape_basic_team_table(page) -> pd.DataFrame:
    """
    Scrapes player name, total points, market value, and last 5 match fitness scores
    from the Biwenger Team tab table.

    Args:
        page (playwright.sync_api.Page): Playwright page on the Team tab with table view loaded.

    Returns:
        pd.DataFrame: DataFrame with columns: name, points, market_value, fitness (list of last 5 match scores)
    """
    players = []

    rows = page.locator("table.table.no-swipe tbody tr.ng-star-inserted")
    row_count = rows.count()
    console.log(f"[bold blue]📄 Found {row_count} player rows")

    for i in range(row_count):
        try:
            row = rows.nth(i)

            # 1. Player name
            name = row.locator("th.text-left a").inner_text().strip()

            # 2. Total points (first <td> after name column)
            points_text = row.locator("td").nth(2).inner_text().strip()
            points = int(points_text)

            # 3. Market value – first <td> with class 'tr' after points
            market_value_raw = row.locator("td.tr").first.inner_text().strip()

            # 4. Fitness – get text of all <player-points> under <player-fitness>
            fitness_cells = row.locator("player-fitness player-points")
            fitness = [cell.inner_text().strip() for cell in fitness_cells.all()]

            # Create player data with standard fields
            player_data = {
                "name": name,
                "current_season_points": points,
                "market_value": market_value_raw,
            }

            # Add fitness values as individual columns
            # Pad with None if there are fewer than 5 values
            for j in range(5):
                column_name = f"game_t-{j + 1}"
                player_data[column_name] = fitness[j] if j < len(fitness) else None

            players.append(player_data)

        except Exception as e:
            console.log(f"[bold red]❌ Error scraping row {i}: {e}")

    return pd.DataFrame(players).replace("-", 0).fillna(0)

def scraper(hardcoded_pages: int = None):
    console.rule("[bold blue]Starting Biwenger Scraper")
    start = time.time()
    creds = load_credentials()

    with sync_playwright() as p:
        # browser = p.chromium.launch(headless=False)
        # b = True
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-gpu", "--no-sandbox"],
        )
        b = False

        context = browser.new_context()
        page = context.new_page()

        # Now you're logged in: do scraping here
        perform_login(page, creds["biwenger_email"], creds["biwenger_password"], browser=b)
        page.goto("https://biwenger.as.com/app")

        # Click players tab
        page.click('a[href="/team"]')

        # Click view as list
        page.get_by_role("button", name="Table").click()

        # Scroll to list section
        scroll_into_view(page, "segmented-control button[aria-label='Squad']")

        # Scrape players
        df = scrape_basic_team_table(page)
        df['season'] = 24

        # Store to raw data
        save_players_to_csv(df, filename="current_team.csv")

        time.sleep(5)
        browser.close()
        console.log(f"[bold cyan]⏱️ Finished scraping in {(time.time() - start):.2f} seconds.")


if __name__ == "__main__":
    scraper()
