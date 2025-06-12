from scraper_news_agent.prompts import build_link_filter_prompt, build_summary_prompt
from scraper_news_agent.config import TEAM_NEWS_SOURCES
from utils import Website, write_summary_to_file, call_llm
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

def get_relevant_links(url:str, team:str, model: str, client=None):
    website = Website(url)
    if not website.links:
        print(f"No links found at {url}")
        return {}

    # Construct LLM messages
    prompts = build_link_filter_prompt(team=team, links=website.links)

    try:
        result = call_llm(prompts["system"], prompts["user"], model=model, client=client)
        # print(result)
        result_clean = _extract_json_block(result)
        return json.loads(result_clean)
    except Exception as e:
        print(f"❌ Error parsing JSON from LLM for {team}: {e}")
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

        time.sleep(0.5) # gentle scraping

    return article_blobs


def get_summary_from_site(team: str, article_blobs: list[str], model: str, client=None) -> str:
    """
    Given a list of full article contents, returns a markdown summary
    grouped into Injuries, Transfers, Lineups, and Previews.

    Parameters:
    - team: the name of the football team
    - date: the date string used for context
    - article_blobs: list of raw article contents (from Website.get_contents())
    - client: an instantiated OpenAI client (OpenAI(api_key=...))
    - model: OpenAI model name (default: gpt-4o)

    Returns:
    - Markdown summary string
    """
    if not article_blobs:
        print(f"⚠️ No articles to summarize for {team}.")
        return ""

    prompts = build_summary_prompt(team=team, articles=article_blobs)

    try:
        return call_llm(prompts["system"], prompts["user"], model=model, client=client)

    except Exception as e:
        print(f"❌ Failed to generate summary for {team}: {e}")
        return ""


def main_scraper():
    for team, sources in TEAM_NEWS_SOURCES.items():
        print(f"\n🔎 Scraping team: {team}")

        team_article_urls = []

        # Step 1: Gather relevant links from all sources
        for url in sources:
            print(f"🌐 Site: {url}")
            model = OPENAI_MODEL
            client = openai_client
            relevant_links = get_relevant_links(url, team, model=model, client=client)

            if not relevant_links:
                print("⚠️ No relevant links found.")
                continue

            urls = relevant_links.get("links", [])
            team_article_urls.extend(urls)

            time.sleep(1)  # gentle scraping

        if not team_article_urls:
            print(f"⚠️ No relevant article URLs found for {team}. Skipping.")
            continue

        # Step 2: Extract article contents
        article_blobs = get_article_contents_from_links(team, team_article_urls)

        if not article_blobs:
            print(f"⚠️ No article content extracted for {team}. Skipping.")
            continue

        # Step 3: Generate single summary per team
        # model = "gemma3:4b"
        # client = None
        model = OPENAI_MODEL
        client = openai_client
        summary_md = get_summary_from_site(team=team, article_blobs=article_blobs, model=model, client=client)

        # Step 4: Write summary to file
        if summary_md:
            write_summary_to_file(team, summary_md)

if __name__ == "__main__":
    main_scraper()

