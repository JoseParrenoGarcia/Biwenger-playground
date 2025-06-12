import streamlit as st
import os

# Locate the root of your project and summaries folder
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, ".."))
summaries_dir = os.path.join(root_dir, "scraper_news_agent", "summaries")

# List markdown files in the summaries directory
md_files = [f for f in os.listdir(summaries_dir) if f.endswith(".md")]

# Generate team name display map
team_names = [f.replace("-", " ").replace(".md", "").title() for f in md_files]
team_map = dict(zip(team_names, md_files))

# --- Page Setup ---
st.set_page_config(layout="wide", page_title="News scraper")

# Team selector in sidebar or top of page
with st.container(border=True):
    cols = st.columns([1, 7])

    with cols[0]:
        selected_team = st.selectbox("Select a Team", sorted(team_names))

st.divider()

# Display the markdown content
with st.container(border=True):
    if selected_team:
        file_path = os.path.join(summaries_dir, team_map[selected_team])
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        st.markdown(content, unsafe_allow_html=False)

