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

def _get_relevant_links(url:str, team:str):
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

def main_scraper():
    for team, sources in TEAM_NEWS_SOURCES.items():
        print(f"\n🔎 Scraping team: {team}")

        for url in sources:
            print(f"🌐 Site: {url}")
            relevant_links = _get_relevant_links(url, team)

            if not relevant_links:
                print("⚠️ No relevant links found.")
                continue

            print("\n🔗 RELEVANT LINKS:")
            print(json.dumps(relevant_links, indent=2))

            time.sleep(1)  # avoid hammering sites or OpenAI


if __name__ == "__main__":
    main_scraper()

