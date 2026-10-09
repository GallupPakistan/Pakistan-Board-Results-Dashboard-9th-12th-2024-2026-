"""pages/7_Subject_Wise.py - subject pass rates, then chosen subjects across classes."""
import streamlit as st
import pandas as pd
from config.settings import CLASSES, CLASS_COLORS, DEFAULT_CLASS, PROVINCE_BOARD_MAP
from components.page_boot import boot, year_and_class, delta_kpi, no_data, not_published
from components.filter_bar import render_filter_bar
from components.kpi_card import render_kpi_row, format_compact
from components.chart_card import chart_card
from data.loader import load, agg, totals, prev_year, like_for_like, scope
import charts.combined_charts as C


def section(t):
    st.markdown(f'<div class="page-header-title" style="margin:1.2rem 0 .4rem">{t}</div>', unsafe_allow_html=True)


def two(a_title, a_sub, a_fig, b_title, b_sub, b_fig):
    a, b = st.columns(2)
    with a:
        with chart_card(a_title, a_sub):
            st.plotly_chart(a_fig, width="stretch")
    with b:
        with chart_card(b_title, b_sub):
            st.plotly_chart(b_fig, width="stretch")


def one(title, sub, fig):
    with chart_card(title, sub):
        st.plotly_chart(fig, width="stretch")

boot("Subject Wise", "Subject pass rates for a class (default 12th, 2026), then chosen subjects compared across classes.")
year, cls = year_and_class("sj", title="Select Year")
S = load("subject"); s = S[S["Class"] == cls]
if s[s["Year"] == year].empty: no_data(cls, year, s)
boards = sorted(s[s["Year"] == year]["Board"].unique())
pick = st.multiselect("Boards (empty = all boards that publish subjects)", boards, key="sj_boards")
sb = s[s["Board"].isin(pick)] if pick else s
cur = agg(sb[sb["Year"] == year], ["Subject"]); cur = cur[cur["Appeared"] >= 200]
render_kpi_row([
    dict(icon="menu_book", value=str(cur["Subject"].nunique()), label=f"Subjects (200+ candidates) · {year}", accent="blue"),
    dict(icon="emoji_events", value=f"{cur['Pass %'].max():.1f}%" if len(cur) else "-", label=f"Best · {cur.sort_values('Pass %').iloc[-1]['Subject'] if len(cur) else ''}", accent="green"),
    dict(icon="trending_down", value=f"{cur['Pass %'].min():.1f}%" if len(cur) else "-", label=f"Weakest · {cur.sort_values('Pass %').iloc[0]['Subject'] if len(cur) else ''}", accent="red"),
    dict(icon="account_balance", value=str(len(boards)), label="Boards with subject data", accent="gold"),
])
two("Top 10 Subjects by Pass %", f"{cls} · {year}", C.chart_subject_rank(sb, year, 10, True), "Weakest 10 Subjects", f"{cls} · {year}", C.chart_subject_rank(sb, year, 10, False))
one("Most Attempted Subjects", f"{cls} · {year} · colour = pass %", C.chart_subject_volume(sb, year, 12))
section("Compare All 4 Classes")
yr = S[S["Year"] == year]
common = ["English", "Urdu", "Islamic Education", "Pakistan Studies", "Mathematics", "Physics", "Chemistry", "Biology", "Computer Science"]
avail = sorted(yr["Subject"].unique())
default = [x for x in common if x in avail][:8] or avail[:8]
subs = st.multiselect("Subjects to compare", avail, default=default, key="sj_compare")
two("Subject Pass % by Class", f"{year} · all boards that publish subjects", C.chart_subject_by_class(S, year, subs),
    "Subject × Class Heatmap", f"{year}", C.chart_subject_heat(S, year, subs))
