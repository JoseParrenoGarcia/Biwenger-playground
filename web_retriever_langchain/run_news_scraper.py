import os
import datetime
import json
from web_retriever_langchain.config.team_sources import team_sources
from web_retriever_langchain.agent.retriever_agent import build_agent
from web_retriever_langchain.utils.link_utils import extract_links_from_text
from web_retriever_langchain.agent.tools_setup import get_browser_tools

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def get_today_str():
    return datetime.datetime.now().strftime("%Y-%m-%d")

def save_article_links(team: str, urls: list[str]):
    team_dir = os.path.join("data", team)
    os.makedirs(team_dir, exist_ok=True)
    filename = os.path.join(team_dir, f"{get_today_str()}_links.json")

    with open(filename, "w") as f:
        json.dump(urls, f, indent=2, ensure_ascii=False)

    print(f"[✓] Saved links to {filename}")


def run_scraper(team: str):
    urls = team_sources.get(team, [])
    if not urls:
        print(f"[!] No sources found for team '{team}'")
        return

    print(f"[+] Found {len(urls)} source(s) for team '{team}'")

    tools = get_browser_tools(mode="discovery")
    agent = build_agent(tools=tools, verbose=True)

    all_extracted_links = []

    for url in urls:
        print(f"[→] Visiting: {url}")
        try:
            result = agent.run(f"Go to {url} and return the full HTML or visible text of the page.")
            print("[✓] Page fetched.")

            # Extract links from returned text
            links = extract_links_from_text(result)
            all_extracted_links.extend(links)

        except Exception as e:
            print(f"[!] Error visiting {url}: {e}")

    print(f"[+] Found {len(all_extracted_links)} raw links total.")
    save_article_links(team, all_extracted_links)

if __name__ == "__main__":
    # Example: scrape Valencia CF
    run_scraper("valencia_cf")
