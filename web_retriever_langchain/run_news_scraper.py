import os
import datetime
import json
from web_retriever_langchain.config.team_sources import team_sources
from web_retriever_langchain.agent.retriever_agent import build_agent

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

    print(f"[+] Found {len(urls)} sources for team '{team}'")


if __name__ == "__main__":
    # Example: scrape Valencia CF
    run_scraper("valencia_cf")
