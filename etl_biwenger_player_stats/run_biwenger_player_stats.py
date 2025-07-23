import time
from rich.console import Console
from etl_biwenger_player_stats.scraper_biwenger_player_stats.player_scraper import scraper
from etl_biwenger_player_stats.transform_biwenger import transform_players
from etl_biwenger_player_stats.scraper_biwenger_player_stats.utils import (calculate_season)
from etl_biwenger_player_stats.scraper_biwenger_player_stats.current_team_scraper import team_scraper


console = Console()

if __name__ == "__main__":
    # start_time = time.time()
    # console.rule("[bold blue]Player Extract Step")
    # scraper(season_tag=calculate_season())

    console.rule("[bold yellow]Player Transform Step")
    transform_players()

    # console.rule("[bold green]Player Load Step")
    # load_to_production()

    # total_duration = time.time() - start_time
    # console.print(f"[bold white on black]🏁 Full ETL completed in {total_duration:.2f} seconds!")

    # start_time = time.time()
    # console.rule("[bold blue]Team Extract Step")
    # team_scraper()
    # total_duration = time.time() - start_time
    # console.print(f"[bold white on black]🏁 Full Team ETL completed in {total_duration:.2f} seconds!")

