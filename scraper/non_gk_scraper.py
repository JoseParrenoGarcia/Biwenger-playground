# of_scraper.py
TAB_MAP = {
    "General":  ["Year", "MP", "MIN", "GLS", "AST", "ASR"],
    "Shooting": ["Year", "MP", "GLS", "TOS", "SOT", "BCM"],
    # …
}

# _extract_simple_table identical to GK version
# _extract_rating identical too – works for all positions
# scrape_outfielder (…) loops TAB_MAP like GK version
