from etl_biwenger_player_stats.scraper_biwenger_player_stats.utils import (
    perform_login,
    load_credentials
)
from playwright.sync_api import sync_playwright
import time

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


def scrape_players():
    creds = load_credentials()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        # browser = p.chromium.launch(
        #     headless=True,
        #     args=["--disable-gpu", "--no-sandbox"],
        # )
        context = browser.new_context()
        page = context.new_page()

        # Now you're logged in: do scraping here
        perform_login(page, creds["biwenger_email"], creds["biwenger_password"])
        page.goto("https://biwenger.as.com/app")

        # Click players tab
        page.click('a[href="/players"]')

        # Click view as list
        page.get_by_role("button", name="Table").click()

        # Click the very first player in the list
        page.locator('table a[role="button"][href^="/la-liga/players/"]').first.click()

        # Scrape player stats
        player_stats = scrape_stats(page)
        print(player_stats)

        time.sleep(5)
        browser.close()


if __name__ == "__main__":
    scrape_players()
