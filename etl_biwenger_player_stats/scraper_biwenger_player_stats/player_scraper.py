from etl_biwenger_player_stats.scraper_biwenger_player_stats.utils import (
    perform_login,
    load_credentials,
    save_players_to_json,
)
from playwright.sync_api import sync_playwright
import time
from rich.console import Console

console = Console()

def scrape_stats(page) -> dict:
    """
    Extracts stats from a single player's profile page.
    Assumes the page is already navigated to the player's detail view.
    Returns a dict of extracted stats.
    """
    def safe_get_attr(selector, attr):
        try:
            return page.locator(selector).first.get_attribute(attr)
        except:
            return None

    def safe_text(selector):
        try:
            return page.locator(selector).first.inner_text().strip()
        except:
            return None

    def safe_stat(label_text):
        try:
            return page.locator('div.stat', has_text=label_text).locator('div').first.inner_text().strip()
        except:
            return None

    def safe_table_value(label_text):
        try:
            return page.locator('tr', has_text=label_text).locator('td').nth(1).inner_text().strip()
        except:
            return None

    raw_name = safe_text('h1')


    stats = {
        "name": raw_name.split("\n")[0].strip() if raw_name else None,  # or a more specific selector
        "team": safe_get_attr('team-link a[title]', 'title'),
        "position": safe_get_attr('player-position', 'title'),
        "total_points": safe_stat("Points"),
        "current_value": safe_table_value("Value"),
        "min_value_1y": safe_table_value("Min"),
        "max_value_1y": safe_table_value("Max"),
        "games_played": safe_stat("Games played"),
        "avg_points_per_game": safe_stat("Average")
    }

    return stats

def scrape_all_players(page, max_players=500):
    player_data = []

    # ✅ Step 1: Click first player (ensure we're on the detail page)
    console.log("[bold cyan]🔎 Clicking first player...")
    page.locator('table a[role="button"][href^="/la-liga/players/"]').first.click()
    page.wait_for_timeout(1000)  # Wait for page to load

    for i in range(max_players):
        stats = scrape_stats(page)
        console.log(f"✅ Scraped {i+1}: [bold]{stats['name']}[/]")
        player_data.append(stats)

        # Check for next arrow
        next_button = page.locator('a.navigation.next')
        if next_button.count() == 0:
            console.log("🚨 [bold red]No next player button found. End of list.[/]")
            break

        try:
            next_button.click()
            page.wait_for_timeout(1000)
        except Exception as e:
            console.log(f"❌ [bold red]Failed to click next:[/] {e}")
            break

    return player_data


def scraper():
    console.rule("[bold blue]Starting Biwenger Scraper")
    start = time.time()
    creds = load_credentials()

    with sync_playwright() as p:
        # browser = p.chromium.launch(headless=False)
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-gpu", "--no-sandbox"],
        )
        context = browser.new_context()
        page = context.new_page()

        # Now you're logged in: do scraping here
        perform_login(page, creds["biwenger_email"], creds["biwenger_password"])
        page.goto("https://biwenger.as.com/app")

        # Click players tab
        page.click('a[href="/players"]')

        # Click view as list
        page.get_by_role("button", name="Table").click()

        # Scrape player stats
        # all_stats = scrape_all_players(page, max_players=4)
        all_stats = scrape_all_players(page)

        # Store to raw data
        save_players_to_json(all_stats, filename="biwenger_players_raw.json")

        time.sleep(5)
        browser.close()
        console.log(f"[bold cyan]⏱️ Finished scraping in {(time.time() - start):.2f} seconds.")


if __name__ == "__main__":
    scraper()
