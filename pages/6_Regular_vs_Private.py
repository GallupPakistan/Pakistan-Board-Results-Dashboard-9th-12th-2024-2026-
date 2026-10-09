"""pages/6_Regular_vs_Private.py - Regular vs Private candidates, then across classes."""
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

boot("Regular vs Private", "Regular and Private candidates for a class (default 12th, 2026), then compared across classes.")
year, cls = year_and_class("rp", title="Select Year")
Cat = load("category"); c = Cat[Cat["Class"] == cls]
if c.empty: not_published(cls, "Regular vs Private data")
if c[c["Year"] == year].empty: no_data(cls, year, c)
cur = c[c["Year"] == year]; r = agg(cur[cur["Category"] == "Regular"], ["Category"]); p = agg(cur[cur["Category"] == "Private"], ["Category"])
cards = []
if not r.empty: cards.append(dict(icon="school", value=f"{r['Pass %'].iloc[0]:.1f}%", label=f"Regular Pass Rate · {year}", accent="blue"))
if not p.empty: cards.append(dict(icon="person", value=f"{p['Pass %'].iloc[0]:.1f}%", label=f"Private Pass Rate · {year}", accent="gold"))
if not r.empty and not p.empty: cards.append(dict(icon="balance", value=f"{r['Pass %'].iloc[0] - p['Pass %'].iloc[0]:+.1f} pts", label="Regular minus Private", accent="green"))
cards.append(dict(icon="groups", value=format_compact(cur["Appeared"].sum()), label="Candidates", accent="blue"))
render_kpi_row(cards)
two("Pass % by Category and Year", f"{cls}", C.chart_category_pass_rate(c), "Share of Candidates", f"{cls} · {year}", C.chart_category_share(c, year))
one("Pass % by Category and Board", f"{cls} · {year}", C.chart_category_by_board(c, year))
section("Compare All 4 Classes")
st.caption("Published for " + ", ".join(sorted(Cat[Cat["Year"] == year]["Class"].unique(), key=CLASSES.index)) + f" in {year}.")
two("Regular vs Private Pass % by Class", f"{year}", C.chart_category_by_class(Cat, year), "Regular vs Private Share by Class", f"{year}", C.chart_category_share_by_class(Cat, year))
