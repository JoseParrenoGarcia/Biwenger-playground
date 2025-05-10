import json, asyncio
from gk_scraper import scrape_goalkeeper
from non_gk_scraper import scrape_outfielder

async def run_player(p):
    if p["position"] == "Goalkeeper":
        df = await scrape_goalkeeper(p["sofascore_name"], p["id"])
    else:
        df = await scrape_outfielder(p["sofascore_name"], p["id"])
    print(df)

if __name__ == "__main__":
    with open("config/players.json") as f:
        players = [p for p in json.load(f)["players"] if p.get("to_scrape")]
    asyncio.run(asyncio.gather(*(run_player(p) for p in players)))
