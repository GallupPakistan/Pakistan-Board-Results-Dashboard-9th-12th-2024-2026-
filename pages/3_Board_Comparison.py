"""pages/3_Board_Comparison.py - rank boards for a class and year, then compare across classes."""
import streamlit as st
import pandas as pd
from config.settings import CLASSES, CLASS_COLORS, DEFAULT_CLASS, PROVINCE_BOARD_MAP
from components.page_boot import boot, year_and_class, delta_kpi, no_data, not_published
from components.filter_bar import render_filter_bar
from components.kpi_card import render_kpi_row, format_compact
from components.chart_card import chart_card
from data.loader import load, agg, totals, prev_year, like_for_like, scope
import charts.combined_charts as C
import charts.extra_charts as X


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

boot("Board Comparison", "Rank BISE boards by pass rate for a class (default 12th, 2026), then compare across all classes.",
     stat_label="BISE Boards", stat_value="15", stat_icon="account_balance")
year, cls = year_and_class("bc", title="Select Year")
other = prev_year(year)
full = load("overall")
d = full[full["Class"] == cls]; cur = d[d["Year"] == year]
if cur.empty: no_data(cls, year, d)
t = totals(cur); a = agg(cur, ["Board"]).sort_values("Pass %"); best, worst = a.iloc[-1], a.iloc[0]
render_kpi_row([
    dict(icon="groups", value=format_compact(t["appeared"]), label=f"{cls} Appeared · {year}", accent="blue"),
    dict(icon="percent", value=f"{t['pct']:.1f}%", label="Overall Pass Rate", accent="gold"),
    dict(icon="emoji_events", value=f"{best['Pass %']:.1f}%", label=f"Highest · {best['Board']}", accent="green"),
    dict(icon="trending_down", value=f"{worst['Pass %']:.1f}%", label=f"Lowest · {worst['Board']}", accent="red"),
])
two("Pass % by Board", f"{cls} · {year}", C.chart_board_pass_rate(d, year), "Change in Pass % vs Previous Year", f"{other} → {year}" if other else "Needs an earlier year",
    C.chart_yoy_change_by_board(d, year, other) if other else C.empty("2024 is the first year"))
import plotly.express as px
s = cur.sort_values("Appeared", ascending=False)
fig = px.bar(s, x="Board", y=["Passed", "Failed"], barmode="stack", color_discrete_sequence=["#22C55E", "#EF4444"]); fig.update_layout(legend_title_text="")
two("Appeared = Passed + Failed", f"{cls} · {year}", C.base(fig, 400), "Board Size vs Pass %", f"{cls} · {year}", C.chart_class_bubble(cur, year))
one("Board Quadrant", f"{cls} · {year} · pass % vs change from {other}; bubble size = candidates" if other else f"{cls} · needs an earlier year",
    X.chart_quadrant(d, year, other) if other else C.empty("2024 is the first year in the dataset"))
one("Ranking Race", f"{cls} · press Play to watch the boards re-order by pass % from year to year", X.chart_rank_race(d))
if cls == "11th" and year == 2025: st.caption("11th 2025: Mardan and Bannu report promoted results (pass % near 99%), so they sit far from the rest.")
section("Compare All 4 Classes")
boards = st.multiselect("Boards (empty = all)", sorted(full["Board"].unique()), key="bc_boards")
one("Pass % by Board and Class", f"{year}", C.chart_board_by_class(full, year, boards or None))
sub = full[full["Board"].isin(boards)] if boards else full
one("Pass % Heatmap · Board × Class", f"{year}", C.chart_heatmap(sub, year))
if boards: one("Pass % Trend by Class", "Selected boards combined", C.chart_class_trend(sub))