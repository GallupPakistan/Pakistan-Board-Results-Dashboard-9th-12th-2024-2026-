"""pages/9_Grade_Distribution.py - grade mix of passed candidates, then across classes."""
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

boot("Grade Distribution", "Grade mix of passed candidates for a class (default 12th, 2026), then compared across classes.")
year, cls = year_and_class("gd", title="Select Year")
GR = load("grade"); gd = GR[GR["Class"] == cls]
if gd.empty: not_published(cls, "Grade distribution")
if gd[gd["Year"] == year].empty: no_data(cls, year, gd)
cur = gd[gd["Year"] == year]; tot = cur["Count"].sum(); top = cur[cur["Grade"].isin(["A+", "A"])]["Count"].sum()
render_kpi_row([
    dict(icon="military_tech", value=format_compact(tot), label=f"Graded candidates · {year}", accent="blue"),
    dict(icon="emoji_events", value=f"{top / tot * 100:.1f}%", label="A+ and A share", accent="green"),
    dict(icon="workspace_premium", value=f"{cur[cur['Grade'] == 'A+']['Count'].sum() / tot * 100:.1f}%", label="A+ share", accent="gold"),
    dict(icon="account_balance", value=str(cur["Board"].nunique()), label="Boards with grade data", accent="blue"),
])
two("Grade Mix", f"{cls} · {year}", C.chart_grade_donut(gd, year), "Grade Mix by Board", f"{cls} · {year}", C.chart_grade_by_board(gd, year))
section("Compare All 4 Classes")
st.caption("Published for " + ", ".join(sorted(GR[GR["Year"] == year]["Class"].unique(), key=CLASSES.index)) + f" in {year}.")
two("Grade Mix by Class", f"{year}", C.chart_grade_by_class(GR, year), "A+ and A Share by Class", f"{year}", C.chart_top_grades_by_class(GR, year))
