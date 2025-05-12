import streamlit as st
import pandas as pd
from utils_streamlit import get_sofascore_player_stats

# --- Page Setup ---
st.set_page_config(layout="wide", page_title="SofaScore Stats Explorer")

# --- Load Data ---
PRODUCTION_DATA_DIR = get_sofascore_player_stats()
df = pd.read_csv(PRODUCTION_DATA_DIR)

# --- Filters ---
with st.form("filters_form"):
    cols = st.columns([2, 2, 2, 2])
    season = cols[0].selectbox("Season", sorted(df['season'].unique()))
    position = cols[1].selectbox("Position", sorted(df['position'].unique()))

    metric_cols = df.select_dtypes(include=['float', 'int']).columns.tolist()

    x_metric = cols[2].selectbox("X-axis", metric_cols, index=0)
    y_metric = cols[3].selectbox("Y-axis", metric_cols, index=1)

    bubble_col = st.selectbox("Bubble Size", [None] + metric_cols)

    sliders = st.columns(2)
    x_range = sliders[0].slider(f"{x_metric} Range", float(df[x_metric].min()), float(df[x_metric].max()), (float(df[x_metric].min()), float(df[x_metric].max())))
    y_range = sliders[1].slider(f"{y_metric} Range", float(df[y_metric].min()), float(df[y_metric].max()), (float(df[y_metric].min()), float(df[y_metric].max())))

    submitted = st.form_submit_button("Apply Filters")






st.dataframe(df)