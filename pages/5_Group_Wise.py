"""pages/5_Group_Wise.py - results by study group, then streams across classes."""
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

boot("Group Wise", "Pass rate by study group for a class (default 12th, 2026), then streams compared across classes.")
year, cls = year_and_class("gp", title="Select Year")
G = load("group"); g = G[G["Class"] == cls]
if g.empty: not_published(cls, "Group-wise data"); 
if g[g["Year"] == year].empty: no_data(cls, year, g)
cur = agg(g[g["Year"] == year], ["Group"]).sort_values("Pass %")
render_kpi_row([
    dict(icon="category", value=str(len(cur)), label=f"Groups · {year}", accent="blue"),
    dict(icon="emoji_events", value=f"{cur.iloc[-1]['Pass %']:.1f}%", label=f"Highest · {cur.iloc[-1]['Group']}", accent="green"),
    dict(icon="trending_down", value=f"{cur.iloc[0]['Pass %']:.1f}%", label=f"Lowest · {cur.iloc[0]['Group']}", accent="red"),
    dict(icon="account_balance", value=str(g[g["Year"] == year]["Board"].nunique()), label="Boards with group data", accent="gold"),
])
two("Pass % by Group", f"{cls} · {year}", C.chart_group_pass(g, year), "Share of Candidates by Group", f"{cls} · {year}", C.chart_group_share(g, year))
one("Pass % by Group and Board", f"{cls} · {year}", C.chart_group_by_board(g, year))
section("Compare All 4 Classes")
st.caption("Groups are merged into streams so classes can be compared: Science (incl. Pre-Medical, Pre-Engineering, General Science), Humanities, Commerce, Other.")
two("Stream Pass % by Class", f"{year}", C.chart_stream_by_class(G, year), "Stream Share of Candidates by Class", f"{year}", C.chart_stream_share_by_class(G, year))
