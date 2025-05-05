import json
import os
import asyncio
from playwright.async_api import async_playwright, Page
import pandas as pd

# Load player json file with relative path
script_dir = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(script_dir, "config", "players.json")
with open(json_path, "r") as f:
    data = json.load(f)

players = [p for p in data["players"] if p.get("to_scrape", False)]

# === HELPER: Collapse All Sections First ===
async def collapse_all_sections(page: Page, section_titles: list[str]):
    for title in section_titles:
        try:
            button = page.locator(f"button:has-text('{title}')").first
            aria_expanded = await button.get_attribute("aria-expanded")
            if aria_expanded == "true":
                await button.click()
                await page.wait_for_timeout(200)
                print(f"🔻 '{title}' section collapsed (init).")
        except:
            continue

# === HELPER: Scrape One Stat Section ===
async def scrape_stat_section(page: Page, section_title: str) -> pd.DataFrame | None:
    print(f"\n🔍 Scraping section: {section_title}")

    try:
        # Locate button by visible text
        section_button = page.locator(f"button:has-text('{section_title}')").first
        await section_button.wait_for(state="visible", timeout=5000)

        # If already expanded, collapse it
        if await section_button.get_attribute("aria-expanded") == "true":
            await section_button.click()
            await page.wait_for_timeout(300)
            print(f"🔻 '{section_title}' collapsed first")

        # Expand it
        await section_button.click()
        await page.wait_for_timeout(1000)
        print(f"✅ '{section_title}' expanded")

        # Locate content using aria-controls
        aria_controls = await section_button.get_attribute("aria-controls")
        if not aria_controls:
            print(f"⚠️ No aria-controls found for '{section_title}'")
            return None

        content = page.locator(f"#{aria_controls}")

        # Try extracting d_flex rows
        rows = await content.locator("div.d_flex").all()
        print(f"🔍 Found {len(rows)} stat rows in '{section_title}'")

        data = {}
        for row in rows:
            spans = await row.locator("span").all()
            if len(spans) >= 2:
                key = await spans[0].inner_text()
                value = await spans[1].inner_text()
                data[key.strip()] = value.strip()

        if data:
            return pd.DataFrame(data.items(), columns=["Metric", "Value"])

        # Fallback to table
        try:
            table = content.locator("table").first
            html = await table.inner_html()
            return pd.read_html(f"<table>{html}</table>")[0]
        except:
            print(f"⚠️ No table fallback in '{section_title}'")
            return None

    except Exception as e:
        print(f"❌ Failed to scrape '{section_title}': {e}")
        return None

# === MAIN SCRAPER FOR ONE PLAYER ===
async def scrape_player_stats(sofascore_name, player_id):
    url = f"https://www.sofascore.com/player/{sofascore_name}/{player_id}"
    print(url)

    async with async_playwright() as p:
        # Launch the browser
        browser = await p.chromium.launch(headless=False)  # Turn off for debugging
        page = await browser.new_page()
        await page.goto(url)

        # Clear consent pop up
        try:
            # Wait for the consent popup to appear (adjust selector as needed)
            await page.wait_for_selector("button:has-text('Consent')", timeout=5000)
            await page.click("button:has-text('Consent')")
            print("✅ Cookie consent accepted.")
            await page.wait_for_timeout(1000)  # give it a moment to disappear
        except:
            print("⚠️ No cookie popup appeared or button not found.")

        # Scroll to bottom to force-load all sections
        await page.evaluate("""() => {
            window.scrollTo(0, document.body.scrollHeight);
        }""")
        await page.wait_for_timeout(2000)
        print("📜 Scrolled to bottom to trigger section rendering")

        # Collapse all sections first
        await collapse_all_sections(page, ["Matches", "Attacking", "Passing", "Defending", "Other", "Cards"])

        # Collect stats
        df_matches = await scrape_stat_section(page, "Matches")
        print(df_matches)

        df_attacking = await scrape_stat_section(page, "Attacking")
        print(df_attacking)

        # df_passing = await scrape_stat_section(page, "Passing")
        # print(df_passing)

        # df_defending = await scrape_stat_section(page, "Defending")
        # print(df_defending)

        await asyncio.sleep(100)  # Keep the browser open for 10 seconds so you can see it
        # await browser.close()

        # print(f"Visiting {url}")

asyncio.run(scrape_player_stats(sofascore_name=players[0]['sofascore_name'],
                                player_id=players[0]['id']))


