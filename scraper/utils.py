from playwright.async_api import async_playwright, Page

# ---------- browser context ----------
async def open_sofascore(url: str) -> Page:
    p = await async_playwright().start()
    browser = await p.chromium.launch(headless=True, args=["--disable-gpu"])
    page = await browser.new_page()
    await page.goto(url)
    # Accept cookies if present
    try:
        await page.click("button:has-text('Consent')", timeout=4000)
    except:
        pass
    return page

# ---------- ui helpers ----------
async def click_tab(page: Page, name: str):
    btn = await page.wait_for_selector(f"button:has-text('{name}')", timeout=6000)
    await btn.scroll_into_view_if_needed()
    await btn.click()

async def collapse_first_season_row(page: Page):
    try:
        expand_arrow = await page.query_selector(".Box.Flex.jBQtbp.cQgcrM")
        if expand_arrow:
            await expand_arrow.click()
            await page.wait_for_timeout(1000)
    except Exception as e:
        print(f"⚠️ Failed to collapse first row: {e}")

