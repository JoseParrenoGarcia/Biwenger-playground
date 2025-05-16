from etl_biwenger_player_stats.scraper_biwenger_player_stats.utils import (
    perform_login,
    load_credentials,
    save_players_to_json,
    click_return_to_list,
    get_total_pages,
    click_next_pagination_arrow,
    scroll_into_view
)
from playwright.sync_api import sync_playwright
import time
from rich.console import Console

console = Console()

def scraper(hardcoded_pages: int = None):
    console.rule("[bold blue]Starting Biwenger Scraper")
    start = time.time()
    creds = load_credentials()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        b = True
        # browser = p.chromium.launch(
        #     headless=True,
        #     args=["--disable-gpu", "--no-sandbox"],
        # )
        # b = False

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

        

        time.sleep(5)
        browser.close()
        console.log(f"[bold cyan]⏱️ Finished scraping in {(time.time() - start):.2f} seconds.")


if __name__ == "__main__":
    scraper()
