import os

import pandas as pd
import numpy as np
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

def metrics_container(current_season: pd.DataFrame):
    total_players = current_season['name'].nunique()
    sum_current_points_per_game = np.round((current_season['points_per_game'].sum() / total_players) * 11, 2)  # normalise to 11 players
    sum_predicted_points = np.round((current_season['remaining_points'].sum() / total_players) * 11, 2)  # normalise to 11 players


    cols_metrics = st.columns(3)
    with cols_metrics[0]:
        with st.container(border=True):
            st.metric(label="Total points per game", value=sum_current_points_per_game)

    with cols_metrics[1]:
        with st.container(border=True):
            st.metric(label="Remaining predicted points end of season", value=sum_predicted_points)

    with cols_metrics[2]:
        with st.container(border=True):
            st.metric(label="Total players in team", value=total_players)
