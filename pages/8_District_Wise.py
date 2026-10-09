"""pages/8_District_Wise.py - district pass rates, then the same board's districts across classes."""
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

boot("District Wise", "District pass rates for a class (default 12th, 2026), then the same districts compared across classes.")
year, cls = year_and_class("ds", title="Select Year")
D = load("district"); d = D[D["Class"] == cls]
if d[d["Year"] == year].empty: no_data(cls, year, d)
boards = sorted(d[d["Year"] == year]["Board"].unique())
pick = render_filter_bar("Board", ["All"] + boards, default="All", key="ds_board") or "All"
sd = d if pick == "All" else d[d["Board"] == pick]
cur = agg(sd[sd["Year"] == year], ["District"])
render_kpi_row([
    dict(icon="location_city", value=str(len(cur)), label=f"Districts · {year}", accent="blue"),
    dict(icon="emoji_events", value=f"{cur['Pass %'].max():.1f}%", label=f"Highest · {cur.sort_values('Pass %').iloc[-1]['District']}", accent="green"),
    dict(icon="trending_down", value=f"{cur['Pass %'].min():.1f}%", label=f"Lowest · {cur.sort_values('Pass %').iloc[0]['District']}", accent="red"),
    dict(icon="account_balance", value=str(len(boards)), label="Boards with district data", accent="gold"),
])
two("District Pass %", f"{cls} · {year} · top 20", C.chart_district(sd, year), "District Pass % Trend", f"{cls}", C.chart_district_trend(sd, pick if pick != "All" else boards[0]))
section("Compare All 4 Classes")
cb = sorted(D[D["Year"] == year]["Board"].unique())
board_c = st.selectbox("Board", cb, index=cb.index(pick) if pick in cb else 0, key="ds_cmp_board")
one(f"{board_c} · District Pass % by Class", f"{year} · classes that publish districts for this board", C.chart_district_by_class(D, year, board_c))
st.caption("District data is published for few boards and classes: " + ", ".join(f"{c}: {D[D['Class'] == c]['Board'].nunique()} boards" for c in CLASSES) + ".")
