from numpy.ma.core import minimum

from scraper_news_agent.prompts import build_link_filter_prompt
from scraper_news_agent.config import TEAM_NEWS_SOURCES
from utils import Website
from openai import OpenAI
import toml
import json
import os
import re
import time

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, ".."))
secrets_path = os.path.join(root_dir, "secrets", "openAI.toml")
config = toml.load(secrets_path)

OPENAI_API_KEY = config["openai"]["api_key"]
OPENAI_MODEL = config["openai"]["model"]

openai_client = OpenAI(api_key=OPENAI_API_KEY)

def _extract_json_block(text):
    # Remove markdown ``` wrappers if present
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    return match.group(1) if match else text.strip()

def get_relevant_links(url:str, team:str):
    website = Website(url)
    if not website.links:
        print(f"No links found at {url}")
        return {}

    # Construct LLM messages
    prompts = build_link_filter_prompt(team=team, links=website.links)

    try:
        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": prompts["system"]},
                {"role": "user", "content": prompts["user"]}
            ],
            temperature=0.3
        )
        result = response.choices[0].message.content
        result_clean = _extract_json_block(result)
        return json.loads(result_clean)

    except Exception as e:
        print(f"❌ Error calling OpenAI: {e}")
        return {}

def get_article_contents_from_links(team: str, article_urls: list[str]) -> list[str]:
    """
    Extracts and returns the cleaned text content of each article URL for a team.
    Skips empty pages or failed loads.
    """
    minimum_required_characters = 250
    article_blobs = []

    for url in article_urls:
        try:
            article = Website(url)
            content = article.get_contents()
            if "Webpage Contents:\n" in content and len(article.text.strip()) > minimum_required_characters:
                article_blobs.append(content)
            else:
                print(f"⚠️ Skipping short or empty article for {team}: {url}")
        except Exception as e:
            print(f"❌ Failed to scrape article for {team}: {url}\n{e}")
            continue

    return article_blobs

def main_scraper():
    for team, sources in TEAM_NEWS_SOURCES.items():
        print(f"\n🔎 Scraping team: {team}")

        for url in sources:
            print(f"🌐 Site: {url}")
            relevant_links = get_relevant_links(url, team)

            if not relevant_links:
                print("⚠️ No relevant links found.")
                continue

            # Extract the list of URLs from the dict
            article_urls = relevant_links.get("links", [])

            # print("\n🔗 RELEVANT LINKS:")
            # print(json.dumps(relevant_links, indent=2))

            all_articles = get_article_contents_from_links(team, article_urls)

            if not all_articles:
                print("⚠️ No article content extracted.")
                return

            print(all_articles)

            time.sleep(1)  # avoid hammering sites or OpenAI


if __name__ == "__main__":
    main_scraper()

