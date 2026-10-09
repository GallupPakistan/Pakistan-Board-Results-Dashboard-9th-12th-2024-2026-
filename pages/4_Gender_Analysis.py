"""pages/4_Gender_Analysis.py - Male vs Female for a class, then across classes."""
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

boot("Gender Analysis", "Male vs Female results for a class (default 12th, 2026), then compared across all classes.")
year, cls = year_and_class("gn", title="Select Year")
G = load("gender"); g = G[G["Class"] == cls]
if g[g["Year"] == year].empty: no_data(cls, year, g)
cur = g[g["Year"] == year]; m = agg(cur[cur["Gender"] == "Male"], ["Gender"]); f = agg(cur[cur["Gender"] == "Female"], ["Gender"])
cards = []
if not m.empty: cards.append(dict(icon="man", value=f"{m['Pass %'].iloc[0]:.1f}%", label=f"Male Pass Rate · {year}", accent="blue"))
if not f.empty: cards.append(dict(icon="woman", value=f"{f['Pass %'].iloc[0]:.1f}%", label=f"Female Pass Rate · {year}", accent="gold"))
if not m.empty and not f.empty:
    gap = f["Pass %"].iloc[0] - m["Pass %"].iloc[0]
    cards.append(dict(icon="balance", value=f"{abs(gap):.1f} pts", label=f"{'Female' if gap >= 0 else 'Male'} lead", accent="green"))
cards.append(dict(icon="groups", value=format_compact(cur["Appeared"].sum()), label="Candidates (gender known)", accent="blue"))
render_kpi_row(cards)
two("Pass % by Gender and Board", f"{cls} · {year}", C.chart_gender_by_board(g, year), "Female-Male Gap by Board", f"{cls} · {year}", C.chart_gender_gap(g, year))
two("Gender Pass Rate by Year", f"{cls}", C.chart_gender_pass_rate(g), "Gender Share of Candidates", f"{cls} · {year}", C.chart_gender_share(g, year))
section("Compare All 4 Classes")
st.caption("Gender data is published for " + ", ".join(sorted(G[G["Year"] == year]["Class"].unique(), key=CLASSES.index)) + f" in {year}.")
two("Pass % by Gender and Class", f"{year}", C.chart_gender_by_class(G, year), "Female-Male Gap by Class", "All years", C.chart_gender_gap_by_class(G))
one("Gender Share of Candidates by Class", f"{year}", C.chart_gender_share_by_class(G, year))
