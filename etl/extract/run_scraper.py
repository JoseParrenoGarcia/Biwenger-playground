import asyncio
import os
import json
from rich.console import Console
from scraper.player_scraper import scrape_player_stats

console = Console()

# Adjust this path to your raw data directory
RAW_DATA_DIR = os.path.join(os.path.dirname(__file__), "../data/raw")
os.makedirs(RAW_DATA_DIR, exist_ok=True)

async def extract_players():
    # Load players to scrape
    config_path = os.path.join(os.path.dirname(__file__), "../../scraper/config/players.json")
    with open(config_path, "r") as f:
        players = [p for p in json.load(f)["players"] if p.get("to_scrape", False)]

    console.print(f"📋 [bold cyan]Found {len(players)} players to scrape[/bold cyan]")

    async def scrape_and_save(player):
        try:
            console.print(f"🔍 Scraping [bold]{player['sofascore_name']}[/bold] (ID: {player['id']})")
            df = await scrape_player_stats(player["sofascore_name"], player["id"])

            # Add player metadata as new columns
            df.insert(0, "id", player["id"])
            df.insert(0, "sofascore_name", player["sofascore_name"])
            df.insert(0, "name", player["name"])

            # Save to raw data path
            out_path = os.path.join(RAW_DATA_DIR, f"{player['sofascore_name']}.csv")
            df.to_csv(out_path, index=False)
            console.print(f"✅ Saved to [green]{out_path}[/green]")

        except Exception as e:
            console.print(f"[red]❌ Error scraping {player['sofascore_name']}: {e}[/red]")

    # Run all player scrapes in parallel
    await asyncio.gather(*(scrape_and_save(p) for p in players))

if __name__ == "__main__":
    console.rule("[bold blue]Extract Step")
    asyncio.run(extract_players())
    console.print("[bold green]🏁 Extraction complete!")
