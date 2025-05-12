import streamlit as st
import pandas as pd
from utils_streamlit import get_sofascore_player_stats

# --- Page Setup ---
st.set_page_config(layout="wide")

# --- Load Data ---
PRODUCTION_DATA_DIR = get_sofascore_player_stats()

df = pd.read_csv(PRODUCTION_DATA_DIR)

st.dataframe(df)