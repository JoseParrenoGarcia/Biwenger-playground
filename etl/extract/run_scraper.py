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
            df.insert(0, "position", player["position"])

            # Save to raw data path
            out_path = os.path.join(RAW_DATA_DIR, f"{player['sofascore_name']}.csv")
            df.to_csv(out_path, index=False)
            # console.print(f"✅ Saved to [green]{out_path}[/green]")
            console.print(f"✅ Saved {player["name"]} to raw")

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
    # console.print(f"🧹 Dropped columns: {columns_to_drop}")

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
        "Additional_XGI": "expected_goal_involvements"
    }

    # --- Step 3: Rename columns ---
    df_all.rename(columns=rename_dict, inplace=True)
    # console.print(f"📝 Renamed columns: {list(rename_dict.keys())}")

    # --- Save to staging ---
    staging_dir = os.path.join(os.path.dirname(__file__), "../data/staging")
    os.makedirs(staging_dir, exist_ok=True)
    out_path = os.path.join(staging_dir, "all_players.csv")

    df_all.to_csv(out_path, index=False)
    console.print("✅ Saved to staging directory")

def load_to_production():
    console.rule("[bold green]📦 Load Step: Move to Production")

    staging_path = os.path.join(os.path.dirname(__file__), "../data/staging/all_players.csv")
    production_dir = os.path.join(os.path.dirname(__file__), "../data/production")
    production_path = os.path.join(production_dir, "all_players.csv")
    os.makedirs(production_dir, exist_ok=True)

    if not os.path.exists(staging_path):
        console.print("[red]❌ Staging file not found. Cannot proceed.[/red]")
        return

    df_staging = pd.read_csv(staging_path)

    # Case 1: Production is empty → just copy
    if not os.path.exists(production_path):
        df_staging.to_csv(production_path, index=False)
        console.print("[green]✅ Production was empty. File copied successfully.[/green]")
        return

    # Case 2: Production exists → compare sums
    df_prod = pd.read_csv(production_path)

    columns_to_check = [
        "matches", "minutes", "total_shots", "accurate_passes",  # Replace with real ones
    ]

    failed_checks = []
    for col in columns_to_check:
        if col not in df_staging.columns or col not in df_prod.columns:
            console.print(f"[yellow]⚠️ Skipping column '{col}' (missing in one of the files)[/yellow]")
            continue
        try:
            sum_staging = pd.to_numeric(df_staging[col], errors="coerce").sum()
            sum_prod = pd.to_numeric(df_prod[col], errors="coerce").sum()
            if sum_staging <= sum_prod:
                failed_checks.append((col, sum_staging, sum_prod))
        except Exception as e:
            console.print(f"[red]❌ Error comparing column '{col}': {e}[/red]")

    if failed_checks:
        console.print("[red]🚫 Validation failed. Not copying to production.[/red]")
        for col, s_new, s_old in failed_checks:
            console.print(f"  ➤ [bold]{col}[/bold]: staging={s_new:.2f}, prod={s_old:.2f}")
    else:
        df_staging.to_csv(production_path, index=False)
        console.print("[green]✅ Validation passed. Staging file copied to production.[/green]")


if __name__ == "__main__":
    console.rule("[bold blue]Extract Step")
    asyncio.run(extract_players())

    console.rule("[bold yellow]Transform Step")
    transform_players()

    console.rule("[bold green]Load Step")
    load_to_production()

    console.print("[bold white on black]🏁 Full ETL completed!")
