import os
import pandas as pd
import numpy as np
from rich.console import Console
console = Console()

RAW_DATA_DIR = os.path.join(os.path.dirname(__file__), "data/raw")
STAGING_DATA_DIR = os.path.join(os.path.dirname(__file__), "data/staging")

columns_to_drop = [
        "Shooting_OF_MP",
        "Shooting_OF_GLS",
        "Team play_OF_MP",
        "Team play_OF_AST",
        "Additional_OF_GLS",
        "Additional_OF_AST",
        "Goalkeeping_GK_MP",
        "Additional_GK_GC",
        "Defending_GK_CLS",
    ]

rename_dict = {
        "Year": "season",
        "General_OF_MP": "matches",
        "General_OF_MIN": "minutes",
        "General_OF_GLS": "goals",
        "General_OF_AST": "assists",
        "General_OF_CLS": "clean_sheets",
        "General_OF_GC": "goals_conceded",
        "General_rating_OF_ASR": "avg_rating",
        "Shooting_OF_TOS": "total_shots",
        "Shooting_OF_SOT": "shots_on_target",
        "Shooting_OF_BCM": "big_chances_missed",
        "Team play_OF_KEYP": "key_passes",
        "Team play_OF_BCC": "big_chances_created",
        "Team play_OF_SDR": "dribbles",
        "Passing_OF_APS": "accurate_passes",
        "Passing_OF_APS%": "passing_accuracy",
        "Passing_OF_ALB": "accurate_long_balls",
        "Passing_OF_LBA%": "long_ball_accuracy",
        "Passing_OF_ACR": "accurate_crosses",
        "Passing_OF_CA%": "crossing_accuracy",
        "Defending_OF_CLS": "clean_sheets",
        "Defending_OF_YC": "yellow_cards",
        "Defending_OF_RC": "red_cards",
        "Defending_OF_ELTG": "errors_leading_to_goal",
        "Defending_OF_DRP": "dribbled_past",
        "Defending_OF_TACK": "tackles",
        "Defending_OF_INT": "interceptions",
        "Defending_OF_BLS": "blocked_shots",
        "Defending_OF_ADW": "aerial_duels_won",
        "Additional_OF_xG": "xGoals",
        "Additional_OF_XA": "xAssists",
        "Additional_OF_GI": "goal_involvements",
        "Additional_OF_XGI": "expected_goal_involvements",
        "General_GK_MP": "gk_matches",
        "General_GK_MIN": "gk_minutes",
        "General_GK_CLS": "gk_clean_sheets",
        "General_GK_GC": "goals_conceded",
        "General_rating_GK_ASR": "gk_avg_rating",
        "Goalkeeping_GK_SAV": "saves",
        "Goalkeeping_GK_SAV%": "prct_saves",
        "Goalkeeping_GK_PS": "penalties_saved",
        "Goalkeeping_GK_PS%": "prct_penalties_saved",
        "Passing_GK_APS": "gk_accurate_passes",
        "Passing_GK_APS%": "gk_passing_accuracy",
        "Passing_GK_ALB": "gk_accurate_long_balls",
        "Passing_GK_LBA%": "gk_long_ball_accuracy",
        "Defending_GK_CLS": "gk_clean_sheets",
        "Defending_GK_YC": "gk_yellow_cards",
        "Defending_GK_RC": "gk_red_cards",
        "Defending_GK_ELTG": "gk_errors_leading_to_goal",
        "Defending_GK_DRP": "gk_dribbled_past",
        "Defending_GK_TACK": "gk_tackles",
        "Defending_GK_INT": "gk_interceptions",
        "Defending_GK_BLS": "gk_blocked_shots",
        "Defending_GK_ADW": "gk_aerial_duels_won",
        "Additional_GK_xGC": "xGoals_Conceded",
        "Additional_GK_GP": "goals_prevented",
    }

merge_columns = {
        "matches": "gk_matches",
        "minutes": "gk_minutes",
        "clean_sheets": "gk_clean_sheets",
        "avg_rating": "gk_avg_rating",
        "accurate_passes": "gk_accurate_passes",
        "passing_accuracy": "gk_passing_accuracy",
        "accurate_long_balls": "gk_accurate_long_balls",
        "long_ball_accuracy": "gk_long_ball_accuracy",
        "yellow_cards": "gk_yellow_cards",
        "red_cards": "gk_red_cards",
        "errors_leading_to_goal": "gk_errors_leading_to_goal",
        "dribbled_past": "gk_dribbled_past",
        "tackles": "gk_tackles",
        "interceptions": "gk_interceptions",
        "aerial_duels_won": "gk_aerial_duels_won"
    }

def transform_players():
    all_dfs = []

    for filename in os.listdir(RAW_DATA_DIR):
        if filename.endswith(".csv"):
            filepath = os.path.join(RAW_DATA_DIR, filename)
            try:
                df = pd.read_csv(filepath)
                all_dfs.append(df)
                # console.print(f"📥 Loaded [green]{filename}[/green] with {len(df)} rows")
            except Exception as e:
                console.print(f"[red]❌ Failed to load {filename}: {e}[/red]")

    if not all_dfs:
        console.print("[red]⚠️ No data files found. Nothing to transform.[/red]")
        return

    df_all = pd.concat(all_dfs, ignore_index=True)
    console.print(f"📊 Total rows after concat: [bold]{len(df_all)}[/bold]")

    # --- Step 1: Drop unwanted columns ---
    df_all.drop(columns=[col for col in columns_to_drop if col in df_all.columns], inplace=True)

    # --- Step 2: Rename columns ---
    df_all.rename(columns=rename_dict, inplace=True)

    # --- Step 3: Fill base stats from goalkeeper columns ---
    for base_col, gk_col in merge_columns.items():
        df_all[base_col] = np.where(df_all[base_col].isna(),
                                    df_all[gk_col],
                                    df_all[base_col]
                                    )

    # Drop all gk_ columns
    cols_to_drop = list(merge_columns.values())
    df_all.drop(columns=[col for col in cols_to_drop if col in df_all.columns], inplace=True)

    # print(df_all.dtypes)

    # Enrich with some columns
    df_all.replace("-", 0, inplace=True)
    df_all['avg_rating'] = df_all['avg_rating'].astype(float)

    # Offensive metrics
    df_all["avg_total_rating"] = df_all['avg_rating'] * df_all['matches']
    df_all["pct_shots_on_target"] = df_all['shots_on_target'] / df_all['total_shots']
    df_all['goals_per_90'] = df_all['goals'] / (df_all['minutes'] / 90)
    df_all['assists_per_90'] = df_all['assists'] / (df_all['minutes'] / 90)
    df_all["key_passes_per_90"] = df_all['key_passes'] / (df_all['minutes'] / 90)
    df_all["accurate_passes_per_90"] = df_all['accurate_passes'] / (df_all['minutes'] / 90)
    df_all['goal_involvements_per_90'] = df_all['goal_involvements'] / (df_all['minutes'] / 90)
    df_all["big_chances_created_per_90"] = df_all['big_chances_created'] / (df_all['minutes'] / 90)
    df_all["big_chance_conversion_rate"] = (df_all['goals'] / (df_all['shots_on_target'] + df_all['big_chances_missed'])) * 100
    df_all['xG_diff'] = df_all['goals'] - df_all['xGoals']
    df_all['xA_diff'] = df_all['assists'] - df_all['xAssists']

    # Defensive metrics
    df_all["tackle_success_rate"] = (df_all['tackles'] / (df_all['tackles'] + df_all['dribbled_past'])) * 100
    df_all["defensive_actions_per_90"] = (df_all['tackles'] + df_all['interceptions'] + df_all['blocked_shots']) / (df_all['minutes'] / 90)
    df_all["yellow_cards_per_90"] = df_all['yellow_cards'] / (df_all['minutes'] / 90)
    df_all["red_cards_per_90"] = df_all['red_cards'] / (df_all['minutes'] / 90)
    df_all["aerial_duel_win_rate"] = (df_all['aerial_duels_won'] / (df_all['aerial_duels_won'] + df_all['minutes'] / 90)) * 100
    df_all["errors_leading_to_goal_per_90"] = df_all['errors_leading_to_goal'] / (df_all['minutes'] / 90)
    df_all["interceptions_per_90"] = df_all['interceptions'] / (df_all['minutes'] / 90)
    df_all["clean_sheets_per_90"] = df_all['clean_sheets'] / (df_all['minutes'] / 90)
    df_all["blocked_shots_per_90"] = df_all['blocked_shots'] / (df_all['minutes'] / 90)

    # Goalkeeper metrics
    df_all['goals_prevented_per_90'] = df_all['goals_prevented'] / (df_all['minutes'] / 90)
    df_all['xGoals_conceded_diff'] = df_all['goals_conceded'] - df_all['xGoals_Conceded']

    # Other
    df_all['availability_rate'] = df_all['minutes'] / (df_all['matches'] * 90)

    # 3 Decimal points
    for col in df_all.select_dtypes(include='float64').columns:
        df_all[col] = df_all[col].round(3)

    # --- Save to staging ---
    os.makedirs(STAGING_DATA_DIR, exist_ok=True)
    out_path = os.path.join(STAGING_DATA_DIR, "all_players.csv")

    df_all.to_csv(out_path, index=False)

    console.print("✅ Saved to staging directory")
