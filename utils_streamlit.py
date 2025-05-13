import os
import streamlit as st

@st.cache_data
def get_sofascore_player_stats():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, "etl_sofascore_aggregate_stats", "data", "production", "all_players.csv")
