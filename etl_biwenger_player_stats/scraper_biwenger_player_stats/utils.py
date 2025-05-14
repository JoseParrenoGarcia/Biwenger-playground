from playwright.sync_api import sync_playwright

def login_and_save_session(email: str, password: str, storage_path: str = "biwenger_storage.json"):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto("https://biwenger.as.com/")
        page.get_by_role("button", name="Agree").click()
        page.get_by_role("link", name="Play now!").click()
        page.get_by_role("button", name="Already have an account").click()
        page.get_by_role("textbox", name="Email").fill(email)
        page.get_by_role("textbox", name="Password").fill(password)
        page.get_by_role("button", name="Log in").click()

        page.wait_for_timeout(5000)  # Allow redirects/login to complete

        context.storage_state(path=storage_path)
        print(f"✅ Session saved to {storage_path}")

        browser.close()
