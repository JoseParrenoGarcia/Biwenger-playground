import json
import os
import asyncio
from playwright.async_api import async_playwright, Page
import pandas as pd

# Load player JSON file with relative path
script_dir = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(script_dir, "config", "players.json")
with open(json_path, "r") as f:
    data = json.load(f)

players = [p for p in data["players"] if p.get("to_scrape", False)]

# === GENERAL STATS ===
async def scrape_general_stats(page: Page) -> pd.DataFrame:
    await page.wait_for_selector(".Box.feDCzw.crsNnE", timeout=10000)

    # === Step 1: Extract years ===
    year_spans = await page.query_selector_all(".Box.feDCzw.crsNnE .Box.gQIPzn.fRroAj span")
    years = []
    for y in year_spans:
        text = await y.inner_text()
        if "/" in text:
            years.append(text)

    # === Step 2: Extract stat rows ===
    stat_rows = await page.query_selector_all(".Box.hMcCqO.sc-c2c19408-0.cFPbZB .Box.ggRYVx.iWGVcA .Box.cQgcrM")
    data = []

    for row in stat_rows:
        stat_cells = await row.query_selector_all(".Box.jNHkiI.kFvGEE span")
        stats = [await cell.inner_text() for cell in stat_cells]
        data.append(stats)

    # === Step 3: Combine (only first 2, drop 5th item)
    years_subset = years[:2]
    stats_subset = [row[:4] + row[5:] for row in data[:2]]  # Drop 5th item
    columns = ["Year", "MP", "MIN", "GLS", "AST", "ASR"]
    combined_rows = [[year] + stat_row for year, stat_row in zip(years_subset, stats_subset)]
    df = pd.DataFrame(combined_rows, columns=columns)

    return df


# === MAIN SCRAPER FOR ONE PLAYER ===
async def scrape_player_stats(sofascore_name, player_id):
    url = f"https://www.sofascore.com/player/{sofascore_name}/{player_id}"
    print(url)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto(url)

        # Handle consent popup
        try:
            await page.wait_for_selector("button:has-text('Consent')", timeout=5000)
            await page.click("button:has-text('Consent')")
            print("✅ Cookie consent accepted.")
            await page.wait_for_timeout(1000)
        except:
            print("⚠️ No cookie popup appeared or button not found.")

        # ⬇️ Smooth scroll to bottom using JS with animation
        await page.evaluate("""
            () => {
                window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
            }
        """)
        await page.wait_for_timeout(3000)
        print("📜 Smooth-scrolled to bottom to trigger section rendering")

        # ⬇️ Scroll to and click the 'General' tab to ensure it's visible
        try:
            general_tab = await page.wait_for_selector("button:has-text('General')", timeout=5000)
            await general_tab.scroll_into_view_if_needed()
            await page.wait_for_timeout(500)
            await general_tab.click()
            print("🔍 'General' stats tab clicked and visible.")
        except Exception as e:
            print(f"❌ Failed to locate or click 'General' tab: {e}")

        # Collapse the first season row (if expanded)
        try:
            expand_arrow = await page.query_selector(".Box.Flex.jBQtbp.cQgcrM")
            if expand_arrow:
                await expand_arrow.click()
                print("⬇️ Collapsed first season row to get aggregate stats")
                await page.wait_for_timeout(1000)  # Wait for collapse animation
        except Exception as e:
            print(f"⚠️ Failed to collapse first row: {e}")

        # I NEED TO BUILD THE SCRAPING FOR THE TABLE
        df = await scrape_general_stats(page)
        print(df)

        await asyncio.sleep(2)
        await browser.close()

# Run the scraper
asyncio.run(scrape_player_stats(
    sofascore_name=players[0]['sofascore_name'],
    player_id=players[0]['id']
))