import json, asyncio, os
from scraper.gk_scraper import scrape_goalkeeper
from scraper.non_gk_scraper import scrape_outfield_player

async def run_player(p):
    if p["position"] == "Goalkeeper":
        df = await scrape_goalkeeper(p["sofascore_name"], p["id"])
    else:
        df = await scrape_outfield_player(p["sofascore_name"], p["id"])

    return df

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, "config", "players.json")

    with open(json_path, "r") as f:
        players = [
            p for p in json.load(f)["players"]
            if p.get("to_scrape", False)
        ]

    if not players:
        print("No players marked with 'to_scrape': true")
        raise SystemExit

    # --- Scrape each player using run_player() ---
    for p in players:
        print(f"\n🚀 Scraping stats for {p['name']} ({p['sofascore_name']}, ID: {p['id']})")

        df = asyncio.run(run_player(p))

        print("-" * 40)
        print(df)
