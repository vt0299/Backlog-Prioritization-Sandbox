import os
import requests
import streamlit as st
import pandas as pd
import plotly.express as px

API_BASE = os.getenv("API_BASE", "http://localhost:8000")

st.set_page_config(page_title="Backlog Dashboard", layout="wide")
st.title("Backlog & Prioritization Dashboard")

st.sidebar.header("Settings")
api_base = st.sidebar.text_input("API Base", API_BASE)
refresh = st.sidebar.button("Refresh")

@st.cache_data(ttl=15)
def fetch(endpoint: str):
    r = requests.get(f"{api_base}{endpoint}", timeout=10)
    r.raise_for_status()
    return r.json()

if refresh:
    st.cache_data.clear()

ranked = fetch("/ranked")
summary = fetch("/metrics/summary")
roadmap = fetch("/roadmap")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Stories", summary["story_count"])
c2.metric("Avg RICE", f"{summary['avg_rice']:.2f}")
c3.metric("Done", summary["status_counts"]["done"])
c4.metric("In Progress", summary["status_counts"]["in_progress"])

st.subheader("Status Distribution")
status_df = pd.DataFrame([{"status": k, "count": v} for k, v in summary["status_counts"].items()])
st.plotly_chart(px.bar(status_df, x="status", y="count"), use_container_width=True)

st.subheader("Top RICE Stories")
top_df = pd.DataFrame(ranked)[:10]
st.plotly_chart(px.bar(top_df, x="title", y="rice_score", color="epic_name"), use_container_width=True)
st.dataframe(top_df[["id","title","epic_name","status","rice_score","reach","impact","confidence","effort"]])

st.subheader("Epic Impact (sum of RICE)")
epic_df = pd.DataFrame([{"epic": k, "score": v} for k, v in summary["epic_scores"].items()])
st.plotly_chart(px.bar(epic_df, x="epic", y="score"), use_container_width=True)

st.subheader("Roadmap Timeline")
roadmap_df = pd.DataFrame(roadmap)
if not roadmap_df.empty:
    roadmap_df["start"] = pd.to_datetime(roadmap_df["start"])
    roadmap_df["finish"] = pd.to_datetime(roadmap_df["finish"])
    fig_tl = px.timeline(roadmap_df, x_start="start", x_end="finish", y="task", color="epic", hover_data=["status", "id"])
    fig_tl.update_yaxes(autorange="reversed")
    st.plotly_chart(fig_tl, use_container_width=True)

    st.markdown("**Dependencies**")
    dep_rows = []
    for _, r in roadmap_df.iterrows():
        for d in r["depends_on"]:
            dep_rows.append({"from": d, "to": r["id"]})
    dep_df = pd.DataFrame(dep_rows)
    if dep_df.empty:
        st.write("No dependencies defined.")
    else:
        st.dataframe(dep_df)
else:
    st.info("No roadmap data (missing start/finish on stories).")
