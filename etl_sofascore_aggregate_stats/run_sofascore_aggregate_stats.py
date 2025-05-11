import asyncio
from rich.console import Console
from extract_and_save_player_stats import extract_players
from transform_raw_to_staging import transform_players
from load_to_production_folder import load_to_production

console = Console()

if __name__ == "__main__":
    # console.rule("[bold blue]Extract Step")
    # asyncio.run(extract_players())

    console.rule("[bold yellow]Transform Step")
    transform_players()

    console.rule("[bold green]Load Step")
    load_to_production()

    console.print("[bold white on black]🏁 Full ETL completed!")