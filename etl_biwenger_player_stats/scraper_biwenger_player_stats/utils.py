import json
import os
from rich.console import Console
import math

console = Console()

def load_credentials(filepath="secrets/credentials.json") -> dict:
    current_dir = os.path.dirname(os.path.abspath(__file__))  # /.../etl_biwenger_player_stats/scraper_biwenger_player_stats
    root_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))  # go up two levels
    secrets_path = os.path.join(root_dir, "secrets", "credentials.json")

    with open(secrets_path, "r") as f:
        return json.load(f)

def perform_login(page, email: str, password: str, browser: bool = False) -> None:
    page.goto("https://biwenger.as.com/")

    if browser:
        page.get_by_role("button", name="Agree").click()
    # try:
    #     page.wait_for_selector('button:has-text("Agree")', timeout=1000)
    #     page.get_by_role("button", name="Agree").click()
    # except:
    #     pass
        # print("⚠️ 'Agree' button not found — continuing.")

    page.get_by_role("link", name="Play now!").click()
    page.get_by_role("button", name="Already have an account").click()
    page.get_by_role("textbox", name="Email").fill(email)
    page.get_by_role("textbox", name="Password").fill(password)
    page.get_by_role("button", name="Log in").click()
    page.wait_for_timeout(5000)

def save_players_to_json(players, filename="players_raw.json"):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(current_dir, ".."))
    data_dir = os.path.join(root_dir, "data", "raw")

    os.makedirs(data_dir, exist_ok=True)  # Create folder if it doesn't exist

    file_path = os.path.join(data_dir, filename)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(players, f, indent=2, ensure_ascii=False)

    console.log(f"[bold green]✅ Saved {len(players)} players to {file_path}")

def go_to_pagination_page(page, n):
    try:
        page.locator(f'ul.pagination li >> text="{n}"').click()
        page.wait_for_timeout(1500)
        return True
    except:
        return False

def click_return_to_list(page):
    try:
        console.log("[bold cyan]⬅️ Returning to player list")
        page.locator('i.icon-arrow-left').click()
        page.wait_for_timeout(1000)
    except Exception as e:
        console.log(f"❌ [bold red]Could not return to list:[/] {e}")

def get_total_pages(page, per_page=9):
    summary = page.locator("pagination span.summary").inner_text().strip()  # e.g., "1 - 9 of 499"
    total = int(summary.split("of")[-1].strip())
    return math.ceil(total / per_page)

def click_next_pagination_arrow(page):
    next_arrow = page.locator('ul li >> text="›"')
    if next_arrow.count() == 0 or "disabled" in next_arrow.first.evaluate("el => el.parentElement.className"):
        return False
    next_arrow.first.click()
    page.wait_for_timeout(1500)
    return True


