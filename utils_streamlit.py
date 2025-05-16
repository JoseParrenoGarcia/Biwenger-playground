import os

import pandas as pd
import streamlit as st

@st.cache_data
def get_sofascore_player_stats():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, "etl_sofascore_aggregate_stats", "data", "production", "all_players.csv")

@st.cache_data
def get_biwenger_player_stats():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, "etl_biwenger_player_stats", "data", "processed", "biwenger_players_transformed.csv")

@st.cache_data
def get_current_team_players():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, "etl_biwenger_player_stats", "data", "raw", "current_team.csv")

@st.cache_data
def enrich_team_stats(current_team_df: pd.DataFrame, all_players_df: pd.DataFrame):
    merged_df = pd.merge(current_team_df, all_players_df, on=['name', 'season'], how='left')

    # # Define the columns to rename
    # cols_to_rename = {
    #     'possible_value_improvement': 'last_season_possible_value_improvement',
    #     'games_played_perct': 'last_season_games_played_perct',
    #     'points_per_game': 'last_season_points_per_game',
    #     'points_per_value': 'last_season_points_per_value',
    # }

    # merged_df.rename(columns=cols_to_rename)

    return merged_df

@st.cache_data
def transform_for_transfers(df_enriched: pd.DataFrame):
    return df_enriched
