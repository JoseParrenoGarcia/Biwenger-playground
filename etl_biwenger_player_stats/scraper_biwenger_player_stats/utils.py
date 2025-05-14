from playwright.sync_api import sync_playwright
import json
import os

def load_credentials(filepath="secrets/credentials.json") -> dict:
    current_dir = os.path.dirname(os.path.abspath(__file__))  # /.../etl_biwenger_player_stats/scraper_biwenger_player_stats
    root_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))  # go up two levels
    secrets_path = os.path.join(root_dir, "secrets", "credentials.json")

    with open(secrets_path, "r") as f:
        return json.load(f)

def perform_login(page, email: str, password: str):
    page.goto("https://biwenger.as.com/")
    page.get_by_role("button", name="Agree").click()
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

    print(f"✅ Saved {len(players)} players to {file_path}")


