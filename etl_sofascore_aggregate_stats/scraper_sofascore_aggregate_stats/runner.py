import asyncio
from etl_sofascore_aggregate_stats.scraper_sofascore_aggregate_stats.utils import load_players_from_team_files
from etl_sofascore_aggregate_stats.scraper_sofascore_aggregate_stats.gk_scraper import scrape_goalkeeper
from etl_sofascore_aggregate_stats.scraper_sofascore_aggregate_stats.non_gk_scraper import scrape_outfield_player

async def run_player(p):
    if p["position"] == "Goalkeeper":
        df = await scrape_goalkeeper(p["sofascore_name"], p["id"])
    else:
        df = await scrape_outfield_player(p["sofascore_name"], p["id"])

    return df

if __name__ == "__main__":
    players = load_players_from_team_files()

    if not players:
        print("No players marked with 'to_scrape': true")
        raise SystemExit

    # --- Scrape each player using run_player() ---
    for p in players[0:1]:
        print(f"\n🚀 Scraping stats for {p['name']} ({p['sofascore_name']}, ID: {p['id']})")

        df = asyncio.run(run_player(p))

        print("-" * 40)
        print(df)
