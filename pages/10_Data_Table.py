"""pages/10_Data_Table.py - every table behind the charts + CSV download."""
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

from data.loader import KINDS
boot("Data Table", "Every table behind the charts, filterable, with CSV download.", stat_label="Tables", stat_value=str(len(KINDS)), stat_icon="table_chart")
kind = st.selectbox("Table", KINDS, format_func=lambda k: k.title())
df = load(kind)
a, b, c = st.columns(3)
with a: cs = st.multiselect("Class", CLASSES, default=[DEFAULT_CLASS])
with b: bs = st.multiselect("Board", sorted(df["Board"].unique()))
with c: ys = st.multiselect("Year", sorted(df["Year"].unique()), default=[2026])
d = df[df["Class"].isin(cs)]
if bs: d = d[d["Board"].isin(bs)]
if ys: d = d[d["Year"].isin(ys)]
d = d.drop(columns=["Province"], errors="ignore").round(2)
st.caption(f"{len(d):,} rows")
st.dataframe(d, width="stretch", hide_index=True)
st.download_button("Download CSV", d.to_csv(index=False).encode(), f"bise_{kind}.csv", "text/csv")
