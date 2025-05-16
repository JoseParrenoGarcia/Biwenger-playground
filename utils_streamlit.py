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
def enrich_biwenger_stats(all_players_df: pd.DataFrame, current_team_df: pd.DataFrame):
    merged_df = pd.merge(all_players_df, current_team_df, on='name', how='left')

    return merged_df

@st.cache_data
def transform_for_transfers(df_enriched: pd.DataFrame):
    return df_enriched
