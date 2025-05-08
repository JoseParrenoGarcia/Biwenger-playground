import asyncio
import os
import json
from rich.console import Console
from scraper.player_scraper import scrape_player_stats
from itertools import islice
import pandas as pd

BATCH_SIZE = 3

console = Console()

# Adjust this path to your raw data directory
RAW_DATA_DIR = os.path.join(os.path.dirname(__file__), "../data/raw")
os.makedirs(RAW_DATA_DIR, exist_ok=True)

def chunked(iterable, size):
    it = iter(iterable)
    while True:
        batch = list(islice(it, size))
        if not batch:
            break
        yield batch

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

    # Run player scraping in batches
    for i, batch in enumerate(chunked(players, BATCH_SIZE), 1):
        console.rule(f"[bold magenta]🚀 Batch {i} ({len(batch)} players)")
        await asyncio.gather(*(scrape_and_save(p) for p in batch))

def transform_players():
    console.rule("[bold yellow]🔄 Transform Step: Collate Raw CSVs")

    all_dfs = []

    for filename in os.listdir(RAW_DATA_DIR):
        if filename.endswith(".csv"):
            filepath = os.path.join(RAW_DATA_DIR, filename)
            try:
                df = pd.read_csv(filepath)
                all_dfs.append(df)
                console.print(f"📥 Loaded [green]{filename}[/green] with {len(df)} rows")
            except Exception as e:
                console.print(f"[red]❌ Failed to load {filename}: {e}[/red]")

    if not all_dfs:
        console.print("[red]⚠️ No data files found. Nothing to transform.[/red]")
        return

    df_all = pd.concat(all_dfs, ignore_index=True)
    console.print(f"📊 Total rows after concat: [bold]{len(df_all)}[/bold]")

    # --- Step 1: Drop unwanted columns ---
    columns_to_drop = [
        "Shooting_MP",
        "Shooting_GLS",
        "Team play_MP",
        "Team play_AST",
        "Additional_GLS",
        "Additional_AST",
    ]

    df_all.drop(columns=[col for col in columns_to_drop if col in df_all.columns], inplace=True)
    console.print(f"🧹 Dropped columns: {columns_to_drop}")

    # --- Step 2: Define column rename mapping ---
    rename_dict = {
        "Year": "season",
        "General_MP": "matches",
        "General_MIN": "minutes",
        "General_GLS": "goals",
        "General_AST": "assists",
        "Shooting_TOS": "total_shots",
        "Shooting_SOT": "shots_on_target",
        "Shooting_BCM": "big_chances_missed",
        "Team play_KEYP": "key_passes",
        "Team play_BCC": "big_chances_created",
        "Team play_SDR": "dribbles",
        "Passing_APS": "accurate_passes",
        "Passing_APS %": "passing_accuracy",
        "Passing_ALB": "accurate_long_balls",
        "Passing_LBA %": "long_ball_accuracy",
        "Passing_ACR": "accurate_crosses",
        "Passing_CA %": "crossing_accuracy",
        "Defending_CLS": "clean_sheets",
        "Defending_YC": "yellow_cards",
        "Defending_RC": "red_cards",
        "Defending_ELTG": "errors_leading_to_goal",
        "Defending_DRP": "dribbled_past",
        "Defending_TACK": "tackles",
        "Defending_INT": "interceptions",
        "Defending_BLS": "blocked_shots",
        "Defending_ADW": "aerial_duels_won",
        "Additional_xG": "xGoals",
        "Additional_XA": "xAssists",
        "Additional_GI": "goal_involvements",
        "Additional_XGI": "expected_goal_involvements",

    }


    staging_dir = os.path.join(os.path.dirname(__file__), "../data/staging")
    os.makedirs(staging_dir, exist_ok=True)
    out_path = os.path.join(staging_dir, "all_players.csv")

    df_all.to_csv(out_path, index=False)
    console.print("✅ Saved to staging director")


if __name__ == "__main__":
    console.rule("[bold blue]Extract Step")
    asyncio.run(extract_players())

    console.rule("[bold yellow]Transform Step")
    transform_players()

    console.print("[bold green]🏁 ETL complete!")