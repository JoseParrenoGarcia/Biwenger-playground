from scraper_news_agent.prompts import build_link_filter_prompt
from utils import Website
from openai import OpenAI
import toml
import json
import os
import re

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


if __name__ == "__main__":
    team = "Valencia"
    url = "https://www.superdeporte.es/valencia-cf/"

    relevant_links = _get_relevant_links(url, team)
    print("\n🔗 RELEVANT LINKS:")
    print(json.dumps(relevant_links, indent=2))

    # # Step 1: Scrape the landing page
    # site = Website(url)
    # print(f"\n✅ Loaded: {site.title}\n")
    #
    # # Step 2: Get extracted links (already cleaned & normalized)
    # links = site.get_links()
    # print(f"Found {len(links)} links.\n")
    #
    # # Step 3: Build prompt messages
    # prompts = build_link_filter_prompt(team=team, links=links)
    # print(type(prompts["system"]))
    # print(type(prompts["user"]))
    # print('-----')
    # print(prompts["system"])
    # print('-----')
    # print(prompts["user"])

