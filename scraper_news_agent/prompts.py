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
        
        You must **only include links that likely point to full articles**, not:
        - Generic landing pages (e.g. ending in `/valencia-cf/`)
        - Static pages like calendars or match schedules
        - Pages with no date (e.g. no `/2025/06/11/` or similar)
        
        ### Strong preference: include URLs that contain a date (e.g. `/2025/06/11/`) as they are more likely to be individual news articles.

        Respond ONLY with a JSON object in the following format:
        
        {{
          "links": [
            {{"type": "injuries", "url": "https://full.url/related-to-injuries"}},
            {{"type": "transfers", "url": "https://full.url/related-to-transfers"}},
            {{"type": "lineups", "url": "https://full.url/lineup-discussion"}},
            {{"type": "preview", "url": "https://full.url/match-preview"}}
          ]
        }}
        
        Only include links you are reasonably confident belong to one of the categories. If a link fits more than one category, choose the most specific one. Do not include unrelated links (e.g., fan polls, merchandise, ads). Be concise."""

    user_prompt = f"The list of links is:\n" + "\n".join(links)
    
    return {
        "system": system_prompt,
        "user": user_prompt
    }

