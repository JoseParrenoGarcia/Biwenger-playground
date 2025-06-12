import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging
import os

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/117.0.0.0 Safari/537.36"
    )
}


class Website:
    """
    A utility class to represent a Website that we have scraped,
    with methods to extract and normalize visible text and hyperlinks.
    """

    def __init__(self, url: str, timeout: int = 10):
        self.url = url
        self.text = ""
        self.title = ""
        self.links = []

        try:
            response = requests.get(url, headers=HEADERS, timeout=timeout)
            response.raise_for_status()
        except Exception as e:
            logging.error(f"Failed to fetch {url}: {e}")
            return

        content_type = response.headers.get("Content-Type", "")
        if "html" not in content_type:
            logging.warning(f"Skipped non-HTML content: {content_type}")
            return

        self.body = response.content
        self._parse()

    def _parse(self):
        soup = BeautifulSoup(self.body, "html.parser")

        self.title = soup.title.string.strip() if soup.title else "No title found"

        if soup.body:
            for tag in soup.body(["script", "style", "img", "input"]):
                tag.decompose()
            self.text = soup.body.get_text(separator="\n", strip=True)
        else:
            self.text = ""

        raw_links = soup.find_all("a", href=True)
        self.links = self._normalize_links([a.get("href") for a in raw_links])

    def _normalize_links(self, hrefs):
        clean_links = []
        for href in hrefs:
            href = href.strip()
            if not href or href.startswith("#") or href.lower().startswith("javascript"):
                continue
            full_url = urljoin(self.url, href)
            clean_links.append(full_url)
        return clean_links

    def get_contents(self):
        return f"Webpage Title:\n{self.title}\n\nWebpage Contents:\n{self.text}\n"

    def get_links(self):
        return self.links

def write_summary_to_file(team: str, content: str, out_dir: str = "summaries") -> str:
    """
    Writes markdown summary content to a file: summaries/{team}-{date}.md

    Parameters:
    - team: team name (will be lowercased and spaces replaced)
    - date: ISO date string (e.g., "2025-06-12")
    - content: markdown content to write
    - out_dir: output folder (default: 'summaries')

    Returns:
    - Full path to the written file
    """
    # Normalize filename
    safe_team = team.lower().replace(" ", "-")
    filename = f"{safe_team}.md"
    full_path = os.path.join(out_dir, filename)

    # Ensure directory exists
    os.makedirs(out_dir, exist_ok=True)

    try:
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\n")
        print(f"✅ Summary written to: {full_path}")
    except Exception as e:
        print(f"❌ Failed to write summary to {full_path}: {e}")
        return ""

    return full_path