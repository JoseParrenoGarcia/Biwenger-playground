import os
import json
import pandas as pd

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 0)

def transform_players(
        input_filename="biwenger_players_raw.json",
        output_filename="biwenger_players_transformed.csv",
        season_tag='24/25',
):
    # Step 1: Build paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(current_dir, ".."))
    raw_path = os.path.join(root_dir, "etl_biwenger_player_stats", "data", "raw", input_filename)
    processed_path = os.path.join(root_dir, "etl_biwenger_player_stats", "data", "processed")
    os.makedirs(processed_path, exist_ok=True)

    output_path = os.path.join(processed_path, output_filename)

    # Step 2: Load JSON
    with open(raw_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Step 3: Convert to DataFrame
    df = pd.DataFrame(data)

    # Step 4: Clean numeric fields
    currency_fields = ["current_value", "max_value_1y"]
    for field in currency_fields:
        df[field] = df[field].str.replace("€", "", regex=False).str.replace(",", "", regex=False)
        df[field] = pd.to_numeric(df[field], errors="coerce")

    numeric_fields = ["total_points", "games_played"]
    for field in numeric_fields:
        df[field] = pd.to_numeric(df[field], errors="coerce")

    # Add season tag
    df['season'] = season_tag

    # Enrichment
    df['possible_value_improvement'] = df['max_value_1y'] - df['current_value']
    df['points_per_value'] = df['total_points'] / (df['current_value'] / 1_000_000)
    df['points_per_game'] = df['total_points'] / df['games_played']
    df['current_team'] = df['team']

    float_columns = df.select_dtypes(include=['float']).columns
    for col in float_columns:
        df[col] = df[col].round(2)

    print(df)

    # Step 5: Save to CSV
    df.to_csv(output_path, index=False)
    print(f"✅ Transformed data saved to {output_path}")

    return df
