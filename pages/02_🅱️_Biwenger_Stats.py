import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils_streamlit import (
    get_biwenger_player_stats,
    get_current_team_players,
    enrich_team_stats
)

# --- Page Setup ---
st.set_page_config(layout="wide", page_title="Biwenger Stats Explorer")

# --- Load Data ---
PRODUCTION_DATA_DIR = get_biwenger_player_stats()
PRODUCTION_DATA_DIR_TEAM = get_current_team_players()

df = pd.read_csv(PRODUCTION_DATA_DIR)
df_team = pd.read_csv(PRODUCTION_DATA_DIR_TEAM)
df_team_enriched = enrich_team_stats(current_team_df=df_team, all_players_df=df)
current_team_players = df_team['name'].tolist()

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


        def _highlight_players(fig, df, players_to_highlight, x_metric, y_metric, color, line_color):
            """
            Highlights specified players on the scatter plot with a given color.

            Args:
                fig: The plotly figure to add the highlighted players to.
                df: The DataFrame containing player data.
                players_to_highlight: A list of player names to highlight.
                x_metric: The column name for the x-axis.
                y_metric: The column name for the y-axis.
                color: The color of the highlighted markers.
                line_color: The color of the highlighted marker borders.
            """
            highlighted_df = df[df['name'].isin(players_to_highlight)]

            fig.add_trace(
                go.Scatter(
                    x=highlighted_df[x_metric],
                    y=highlighted_df[y_metric],
                    mode='markers',
                    marker=dict(
                        color=color,
                        line=dict(width=2, color=line_color),
                        size=10,
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


        _highlight_players(fig, df, current_team_players, x_metric, y_metric, 'rgb(125, 60, 152)', 'rgb(187, 143, 206)')

        if highlight_players:
            _highlight_players(fig, df, highlight_players, x_metric, y_metric, 'black', 'grey')

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
        st.dataframe(df, hide_index=True)

with st.container(border=True):
    st.subheader("Transfer options")
    cols = st.columns([1, 8])
    with cols[0]:
        num_gameweeks = st.selectbox("Select Gameweek", list(range(1, 39)))

    st.write("##### Current team")
    current_season = df_team_enriched.copy()
    current_season['games_played_until_today'] = max(df_team_enriched['games_played'].max(), num_gameweeks)
    current_season['games_missing_till_end'] = 38 - current_season['games_played_until_today']
    current_season['predicted_games_till_end'] = np.floor(current_season['games_played_perct'] * current_season['games_missing_till_end'])
    current_season['remaining_points'] = current_season['points_per_game'] * current_season['predicted_games_till_end']


    # Sum of current points per game
    # Sum of predicted points
    # Total players

    select_cols = [
        'position',
        'name',
        'current_season_points',
        'market_value',
        'possible_value_improvement',
        'games_played',
        'games_played_perct',
        'points_per_game',
        'points_per_value',
        'predicted_games_till_end',
        'remaining_points',
    ]
    st.dataframe(current_season[select_cols], hide_index=True, height=650)

    st.write("### Possible team")
    cols_2 = st.columns([1, 1, 3])

    players_to_remove = cols_2[0].multiselect(
        "Remove players from team",
        options=sorted(current_season['name'].unique()),
    )

    predicted_season = current_season.copy()

    if players_to_remove:
        predicted_season = predicted_season[~predicted_season['name'].isin(players_to_remove)]

    players_to_add = cols_2[1].multiselect(
        "Add players to team",
        options=sorted(df['name'].unique()),
    )

    st.dataframe(predicted_season, hide_index=True, height=650)





