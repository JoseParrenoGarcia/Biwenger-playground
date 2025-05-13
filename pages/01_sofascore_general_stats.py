import streamlit as st
import pandas as pd
import plotly.express as px
from utils_streamlit import get_sofascore_player_stats

# --- Page Setup ---
st.set_page_config(layout="wide", page_title="SofaScore Stats Explorer")

# --- Load Data ---
PRODUCTION_DATA_DIR = get_sofascore_player_stats()
df = pd.read_csv(PRODUCTION_DATA_DIR)

# --- Main page ---
st.title("SofaScore Player Statistics Explorer")

# --- Filters ---
with st.form("filters_form"):
    cols = st.columns([1, 1, 1, 1])

    # FILTER COLS
    season_list = sorted(df['season'].unique(), reverse=True)
    season = cols[0].multiselect(
        "Season",
        options=season_list,
        default=season_list[0]
    )

    position = cols[1].multiselect(
        "Position",
        options=sorted(df['position'].unique()),
    )
    team = cols[2].multiselect(
        "Team",
        options=sorted(df['current_team'].unique()),
    )

    # CHART LAYOUT COLS
    metric_cols = df.select_dtypes(include=['float', 'int']).columns.tolist()
    if "id" in metric_cols:
        metric_cols.remove("id")

    x_metric = cols[0].selectbox("X-axis", metric_cols, index=0)
    y_metric = cols[1].selectbox("Y-axis", metric_cols, index=1)
    bubble_metric = cols[2].selectbox("Bubble Size", [None] + metric_cols)

    # sliders = st.columns(2)
    # x_range = sliders[0].slider(f"{x_metric} Range", float(df[x_metric].min()), float(df[x_metric].max()), (float(df[x_metric].min()), float(df[x_metric].max())))
    # y_range = sliders[1].slider(f"{y_metric} Range", float(df[y_metric].min()), float(df[y_metric].max()), (float(df[y_metric].min()), float(df[y_metric].max())))

    submitted = st.form_submit_button("Apply Filters")


# --- Filter data based on selection ---
if submitted:
    if season:
        df = df[df['season'].isin(season)]
    if position:
        df = df[df['position'].isin(position)]
    if team:
        df = df[df['current_team'].isin(team)]

    # --- Visualise ---
    with st.container(border=True):
        st.subheader("Stats scatter plot")

        # Create scatter plot
        fig = px.scatter(
            df,
            x=x_metric,
            y=y_metric,
            size=bubble_metric if bubble_metric else None,
            # color="team" if "team" in df.columns else None,
            hover_name="name" if "name" in df.columns else None,
            hover_data=["team", "position"] if all(col in df.columns for col in ["team", "position"]) else None,
            # title=f"{position if position != 'All' else 'All Positions'} Players - {season}",
            height=600
        )

        st.plotly_chart(fig, use_container_width=True)

st.dataframe(df)