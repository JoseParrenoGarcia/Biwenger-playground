import pandas as pd
import os
from rich.console import Console
console = Console()


STAGING_DATA_DIR = os.path.join(os.path.dirname(__file__), "data/staging/all_players.csv")
PRODUCTION_DATA_DIR = os.path.join(os.path.dirname(__file__), "data/production")


def load_to_production():
    production_path = os.path.join(PRODUCTION_DATA_DIR, "all_players.csv")
    os.makedirs(PRODUCTION_DATA_DIR, exist_ok=True)

    if not os.path.exists(STAGING_DATA_DIR):
        console.print("[red]❌ Staging file not found. Cannot proceed.[/red]")
        return

    df_staging = pd.read_csv(STAGING_DATA_DIR)

    # Case 1: Production is empty → just copy
    if not os.path.exists(production_path):
        df_staging.to_csv(production_path, index=False)
        console.print("[green]✅ Production was empty. File copied successfully.[/green]")
        return

    # Case 2: Production exists → compare sums
    df_prod = pd.read_csv(production_path)

    columns_to_check = [
        "matches", "minutes", "total_shots", "accurate_passes", "saves",  # Replace with real ones
    ]

    failed_checks = []
    for col in columns_to_check:
        if col not in df_staging.columns or col not in df_prod.columns:
            console.print(f"[yellow]⚠️ Skipping column '{col}' (missing in one of the files)[/yellow]")
            continue
        try:
            sum_staging = pd.to_numeric(df_staging[col], errors="coerce").sum()
            sum_prod = pd.to_numeric(df_prod[col], errors="coerce").sum()
            if sum_staging < sum_prod:
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
