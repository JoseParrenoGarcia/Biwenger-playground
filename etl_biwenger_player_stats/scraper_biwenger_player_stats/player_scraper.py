from etl_biwenger_player_stats.scraper_biwenger_player_stats.utils import (
    perform_login,
    load_credentials,
    save_players_to_json,
    click_return_to_list,
    get_total_pages,
    click_next_pagination_arrow,
    scroll_into_view,
    calculate_season
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

    def extract_with_attempts(extract_func, max_attempts=5, delay=1):
        for attempt in range(max_attempts):
            value = extract_func()

            if value is not None and value != "":
                return value

            if attempt < max_attempts - 1:  # Don't sleep on the last attempt
                console.log(f"[bold yellow]🔁 Extraction attempt {attempt + 1} failed, retrying...")
                time.sleep(delay)

        console.log("[bold red]❌ All extraction attempts failed")
        return None

    hold = 0.5

    # 👇 Scroll to and extract key stats
    raw_name = extract_with_attempts(lambda: safe_text('h1'))
    team = extract_with_attempts(lambda: safe_get_attr('team-link a[title]', 'title'))
    position = extract_with_attempts(lambda: safe_get_attr('div.wrapper player-position', 'title'))

    scroll_into_view(page, 'h4:has-text("Statistics")', hold=hold)

    scroll_into_view(page, 'div.stat:has-text("Points")')
    total_points = extract_with_attempts(lambda: safe_stat("Points"))

    scroll_into_view(page, 'div.stat:has-text("Games played")')
    games_played = extract_with_attempts(lambda: safe_stat("Games played"))

    scroll_into_view(page, 'table.table', hold=hold)

    scroll_into_view(page, 'tr:has-text("Value")')
    current_value = extract_with_attempts(lambda: safe_table_value("Value"))

    scroll_into_view(page, 'tr:has-text("Max")')
    max_value = extract_with_attempts(lambda: safe_table_value("Max"))

    stats = {
        "name": raw_name.split("\n")[0].strip() if raw_name else None,  # or a more specific selector
        "current_team": team,
        "position": position,
        "total_points": total_points,
        "games_played": games_played,
        "current_value": current_value,
        "max_value_1y": max_value,
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
            click_return_to_list(page)
            break

        try:
            next_button.click()
            page.wait_for_timeout(1000)
        except Exception as e:
            console.log(f"❌ [bold red]Failed to click next:[/] {e}")
            break

    return player_data


def scraper(season_tag, hardcoded_pages: int = None, ):
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
        page.click('a[href="/players"]')

        # Click view as list
        page.get_by_role("button", name="Table").click()

        # Pagination loop
        all_stats = []
        total_pages = get_total_pages(page)

        if hardcoded_pages:
            total_pages = hardcoded_pages

        console.log(f"📄 Total pages: {total_pages}")

        for page_number in range(1, total_pages - 5):
            console.rule(f"[bold blue]📄 Scraping Page {page_number}")

            if page_number > 1:
                success = click_next_pagination_arrow(page)
                if not success:
                    console.log(f"❌ [bold red]Next page button disabled or missing at page {page_number}")
                    break

            stats = scrape_all_players(page)
            all_stats.extend(stats)

        # Store to raw data
        save_players_to_json(all_stats, filename=f"biwenger_players_raw_{season_tag}.json")

        time.sleep(5)
        browser.close()
        console.log(f"[bold cyan]⏱️ Finished scraping in {(time.time() - start):.2f} seconds.")


if __name__ == "__main__":
    scraper(season_tag=calculate_season())
