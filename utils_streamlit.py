import os

import pandas as pd
import numpy as np
import streamlit as st

@st.cache_data
def get_sofascore_player_stats():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    PRODUCTION_DATA_DIR = os.path.join(current_dir, "etl_sofascore_aggregate_stats", "data", "production", "all_players.csv")
    df = pd.read_csv(PRODUCTION_DATA_DIR)
    return df

@st.cache_data
def get_biwenger_player_stats():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    PRODUCTION_DATA_DIR = os.path.join(current_dir, "etl_biwenger_player_stats", "data", "processed", "biwenger_players_transformed.csv")

    df = pd.read_csv(PRODUCTION_DATA_DIR)
    df['games_played_until_today'] = df['games_played'].max()
    df['games_missing_till_end'] = 38 - df['games_played_until_today']
    df['predicted_games_till_end'] = np.floor(df['games_played_perct'] * df['games_missing_till_end'])
    df['remaining_points'] = df['points_per_game'] * df['predicted_games_till_end']

    return df

@st.cache_data
def get_current_team_players():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    PRODUCTION_DATA_DIR = os.path.join(current_dir, "etl_biwenger_player_stats", "data", "raw", "current_team.csv")

    df = pd.read_csv(PRODUCTION_DATA_DIR)
    return df

@st.cache_data
def enrich_team_stats(current_team_df: pd.DataFrame, all_players_df: pd.DataFrame):
    merged_df = pd.merge(current_team_df, all_players_df, on=['name', 'season'], how='left')
    return merged_df

@st.cache_data
def transform_for_transfers(df_enriched: pd.DataFrame):
    return df_enriched

def metrics_container(df: pd.DataFrame):
    total_players = df['name'].nunique()
    sum_current_points_per_game = np.round((df['points_per_game'].sum() / total_players) * 11, 2)  # normalise to 11 players
    sum_predicted_points = np.round((df['remaining_points'].sum() / total_players) * 11, 2)  # normalise to 11 players


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
