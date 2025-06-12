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
        
        - Try to include links that fall under the 4 key categories: injuries, transfers, lineups, and previews.
        - Do not include unrelated links (e.g., fan polls, merchandise, ads, navigation or calendar pages).
        - Where possible, return around 10 relevant article URLs. Fewer is fine if fewer are available.
        """

    user_prompt = f"The list of links is:\n" + "\n".join(links)
    
    return {
        "system": system_prompt,
        "user": user_prompt
    }

