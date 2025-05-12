import asyncio, os, json
from rich.console import Console
from scraper_sofascore_aggregate_stats.runner import run_player

console = Console()
BATCH_SIZE = 5

RAW_DATA_DIR = os.path.join(os.path.dirname(__file__), "data/raw")
os.makedirs(RAW_DATA_DIR, exist_ok=True)

PLAYERS_TO_SCRAPE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "scraper_sofascore_aggregate_stats", "config", "villareal.json")
)

def chunked(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]


async def extract_players():
    with open(PLAYERS_TO_SCRAPE_PATH, "r") as f:
        players = [p for p in json.load(f)["players"] if p.get("to_scrape", False)]

    console.print(f"📋 [cyan]Extracting stats for {len(players)} players[/cyan]")

    async def scrape_and_save(p):
        try:
            df = await run_player(p)
            df.insert(0, "id", p["id"])
            df.insert(0, "sofascore_name", p["sofascore_name"])
            df.insert(0, "name", p["name"])
            df.insert(0, "position", p["position"])
            df.insert(0, "current_team", p["team"])

            # Save to raw data path
            out_path = os.path.join(RAW_DATA_DIR, f"{p['sofascore_name']}.csv")
            df.to_csv(out_path, index=False)
            console.print(f"✅ Saved {p["name"]} to raw")

        except Exception as e:
            console.print(f"[red]❌ Error scraping {p['sofascore_name']}: {e}[/red]")

    for i, batch in enumerate(chunked(players, BATCH_SIZE), 1):
        console.rule(f"[bold magenta]🚀 Batch {i} ({len(batch)} players)")
        await asyncio.gather(*(scrape_and_save(p) for p in batch))
