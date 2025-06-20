def build_link_filter_prompt(team: str, links: list[str]) -> dict:
    """
    Builds the system and user messages for selecting relevant article links.
    """
    system_prompt = \
        f"""You are a news intelligence agent helping analyze football news articles.
        You are given a list of URLs extracted from a webpage that focuses on team "{team}". 
        Your task is to identify which of these links are likely to contain relevant news related to one or more of the following categories:

        1. Injuries: updates on players who are injured or returning from injury.
        2. Transfers: rumors, confirmed signings, or departures involving the team.
        3. Lineups: articles discussing potential starting elevens or tactical previews.
        4. Previews: analysis or news about upcoming matches (e.g. opponents, kickoff time, squad rotation).
        5. Match reports: summaries or analyses of recent matches involving the team.
        
        ### Prioritization Guidelines:

        - Prefer links that look like full articles — especially if the URL includes a date (e.g. `/2025/06/11/`)
        - However, **do not skip valid-looking links just because they lack a date**.
          - If the link appears to point to a news article (based on the URL text), you can include it.
          - Use your best judgment to avoid junk like navigation pages, homepages, or schedule-only links.
        
        ### Exclude:
        
        - Landing pages (e.g. ending in `/valencia-cf/`)
        - Generic index pages (e.g. `/calendario/`, `/jugadores/`)
        - URLs that look like sections, tags, ads, or login/subscribe pages


        Respond ONLY with a JSON object in the following format:
        
        {{
          "links": [
            "https://example.com/article-with-date.html",
            "https://example.com/valencia/injury-update",
            "https://example.com/article-about-transfer-rumours",
            "https://example.com/article-about-lineups-or-previews-of-upcoming-matches",
          ]
        }}
        
        - Try to include links that fall under the 5 key categories: injuries, transfers, lineups, previews and past match reports.
        - Do not include unrelated links (e.g., fan polls, merchandise, ads, navigation or calendar pages).
        - Where possible, return around 10 relevant article URLs. Fewer is fine if fewer are available.
        """

    user_prompt = f"The list of links is:\n" + "\n".join(links)
    
    return {
        "system": system_prompt,
        "user": user_prompt
    }

def build_summary_prompt(team: str, articles: list[str]) -> dict:
    """
    Returns system + user prompt to generate markdown summary of full articles for a team.
    """

    system_prompt = f"""You are a football news summarizer.

    Given a set of news articles about the football team "{team}", your task is to extract relevant information and generate a summary in markdown format, grouped into the following categories:
    - Injuries
    - Transfers
    - Lineups
    - Previews of upcoming matches
    - Match reports (if applicable)

    ### Requirements:
    - Include all key details: player names, timelines (e.g. “out for two weeks”), match or training context, and quotes when relevant.
    - For lineups, feel free to include **predicted starting elevens**, **convocatoria** (squad call-ups), or tactical formations if mentioned.
    - For previews, include opponent names, dates, competition, key player matchups, and any notable quotes from coaches or players.
    - Bullet points or short paragraphs per item are preferred.
    - If a section has no content, include the header and say "No major updates."
    - Be factual. Only include information supported by the text. Do not speculate.
    
    - For lineups:
      - Try to synthesize likely starting elevens for the next match.
      - If multiple sources suggest different players for a position, include both to indicate possible ambiguity or rotations (e.g., “Mosquera or Paulista”, “Foulquier or Thierry Correia”).
      - Optionally add confidence notes like “(likely)” or “(uncertain)” next to each player if such signals exist.
      - You may use either bullet points or a markdown table to show the lineup.
      - Include any quotes or notes on tactics (e.g., formation changes, player roles) if mentioned.

    ### Output Format:
    Return a markdown document starting with a level-1 heading with the team, followed by clearly separated sections for each category.
    Do not include any explanation or commentary outside the summary itself."""


    article_blobs = "\n\n---\n\n".join(articles)

    user_prompt = f"""Summarize the following articles about {team}:{article_blobs}"""

    return {
        "system": system_prompt,
        "user": user_prompt
    }
