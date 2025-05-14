import time
from rich.console import Console
from etl_biwenger_player_stats.scraper_biwenger_player_stats.player_scraper import scraper

console = Console()

if __name__ == "__main__":
    start_time = time.time()
    console.rule("[bold blue]Extract Step")
    scraper(hardcoded_pages=2)

    # console.rule("[bold yellow]Transform Step")
    # transform_players()
    #
    # console.rule("[bold green]Load Step")
    # load_to_production()
    #
    # total_duration = time.time() - start_time
    # console.print(f"[bold white on black]🏁 Full ETL completed in {total_duration:.2f} seconds!")

