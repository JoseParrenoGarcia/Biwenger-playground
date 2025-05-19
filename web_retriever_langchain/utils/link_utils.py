import re

def extract_links_from_text(text: str) -> list[str]:
    return re.findall(r'https?://[^\s"\'>]+', text)
