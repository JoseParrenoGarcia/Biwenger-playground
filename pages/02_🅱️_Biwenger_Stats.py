import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils_streamlit import get_biwenger_player_stats

# --- Page Setup ---
st.set_page_config(layout="wide", page_title="Biwenger Stats Explorer")

# --- Load Data ---
PRODUCTION_DATA_DIR = get_biwenger_player_stats()
df = pd.read_csv(PRODUCTION_DATA_DIR)

# --- Main page ---
st.title("Biwenger Player Statistics Explorer")

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
    highlight_players = cols[3].multiselect(
        "Highlight Players",
        options=sorted(df['name'].unique()),
    )

    # CHART LAYOUT COLS
    metric_cols = df.select_dtypes(include=['float', 'int']).columns.tolist()
    if "id" in metric_cols:
        metric_cols.remove("id")

    x_metric = cols[0].selectbox("X-axis", metric_cols, index=0)
    y_metric = cols[1].selectbox("Y-axis", metric_cols, index=1)
    bubble_metric = cols[2].selectbox("Bubble Size", [None] + metric_cols)

    submitted = st.form_submit_button("Apply Filters")


# --- Filter data based on selection ---
if submitted:
    if season:
        df = df[df['season'].isin(season)]
    if position:
        df = df[df['position'].isin(position)]
    if team:
        df = df[df['current_team'].isin(team)]

    # Reorder columns to show avg_total_rating after season
    cols = df.columns.tolist()
    if 'avg_total_rating' in cols and 'season' in cols:
        cols.remove('avg_total_rating')
        season_index = cols.index('season')
        cols.insert(season_index + 1, 'avg_total_rating')
        df = df[cols]

    # Calculate tertiles for X and Y axes
    x_tertiles = [df[x_metric].quantile(q) for q in [0.33, 0.67]]
    y_tertiles = [df[y_metric].quantile(q) for q in [0.33, 0.67]]

    # --- Visualise ---
    with st.container(border=True):
        st.subheader("Stats scatter plot")

        # Create scatter plot
        position_colors = {
            "Goalkeeper": "rgb(253, 216, 53)",
            "Defender": "rgb(30, 136, 229)",
            "Midfielder": "rgb(67, 160, 71)",
            "Forward": "rgb(244, 81, 30)"
        }

        fig = px.scatter(
            df,
            x=x_metric,
            y=y_metric,
            size=bubble_metric if bubble_metric else None,
            color="position",  # Color by position
            color_discrete_map=position_colors,  # Map positions to colors
            hover_name="name" if "name" in df.columns else None,
            hover_data={
                x_metric: True,
                y_metric: True,
                "position": False,
            },
            height=600
        )

        if highlight_players:
            highlighted_df = df[df['name'].isin(highlight_players)]

            fig.add_trace(
                go.Scatter(
                    x=highlighted_df[x_metric],
                    y=highlighted_df[y_metric],
                    mode='markers',
                    marker=dict(
                        color='black',
                        line=dict(width=2, color='grey'),
                        size=highlighted_df[bubble_metric] * 5 if bubble_metric else 10
                    ),
                    text=[f"<b>{name}</b><br><br>{x_metric}: {x_val}<br>{y_metric}: {y_val}"
                          for name, x_val, y_val in zip(
                            highlighted_df['name'],
                            highlighted_df[x_metric],
                            highlighted_df[y_metric]
                        )],
                    hoverinfo='text',
                    showlegend=False
                )
            )

        # Add vertical tertile lines (X-axis)
        colour="rgb(248, 196, 113)"
        for x_val in x_tertiles:
            fig.add_vline(x=x_val, line_dash="dash", line_color=colour)

        # Add horizontal tertile lines (Y-axis)
        for y_val in y_tertiles:
            fig.add_hline(y=y_val, line_dash="dash", line_color=colour)

        st.plotly_chart(fig, use_container_width=True)

    with st.container(border=True):
        st.subheader("Stats table")
        st.dataframe(df)