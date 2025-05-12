import asyncio
import time
from rich.console import Console
from extract_and_save_player_stats import extract_players
from transform_raw_to_staging import transform_players
from load_to_production_folder import load_to_production

console = Console()

if __name__ == "__main__":
    start_time = time.time()
    console.rule("[bold blue]Extract Step")
    asyncio.run(extract_players())

    console.rule("[bold yellow]Transform Step")
    transform_players()

    console.rule("[bold green]Load Step")
    load_to_production()

    total_duration = time.time() - start_time
    console.print(f"[bold white on black]🏁 Full ETL completed in {total_duration:.2f} seconds!")

