"""pages/1_Overview.py - Home. Opens on 12th class + 2026 (12th dashboard layout) + all-class comparison."""
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
def section(t): st.markdown(f"<div class=\"page-header-title\" style=\"margin:1.2rem 0 .4rem\">{t}</div>", unsafe_allow_html=True)
def two(a_title, a_sub, a_fig, b_title, b_sub, b_fig):
    a, b = st.columns(2)
    with a:
        with chart_card(a_title, a_sub): st.plotly_chart(a_fig, width="stretch")
    with b:
        with chart_card(b_title, b_sub): st.plotly_chart(b_fig, width="stretch")

from components.provincial_tiles import render_province_tiles
from components.top_boards import render_top_boards
from components.notes import render_important_points

boot("Overview", "Results of 9th, 10th, 11th and 12th class across all BISE boards (default: 12th class, 2026).")
year, cls = year_and_class("ov", allow_all=True)
other = prev_year(year)
ALL = "All Provinces"
prov = render_filter_bar("Province", [ALL] + list(PROVINCE_BOARD_MAP), default=ALL, key="ov_prov") or ALL
boards = [b for bs in PROVINCE_BOARD_MAP.values() for b in bs] if prov == ALL else PROVINCE_BOARD_MAP[prov]

full = load("overall"); full = full[full["Board"].isin(boards)]
df = scope(full, cls)
if df[df["Year"] == year].empty: no_data(cls, year, df)
g = scope(load("gender"), cls); g = g[g["Board"].isin(boards)]
c = scope(load("category"), cls); c = c[c["Board"].isin(boards)]

cur = totals(df[df["Year"] == year])
ll = like_for_like(df, year, other) if other else df.iloc[0:0]
def s(y, k): return float(ll[ll["Year"] == y][k].sum())
if other and len(ll):
    ca, cp, pa, pp = s(year, "Appeared"), s(year, "Passed"), s(other, "Appeared"), s(other, "Passed")
    d_app = delta_kpi(ca, pa); d_pas = delta_kpi(cp, pp); d_fail = delta_kpi(ca - cp, pa - pp, invert=True)
    d_pct = delta_kpi(cp / ca * 100, pp / pa * 100, pct=True)
else:
    d_app = d_pas = d_fail = d_pct = ("", True)
tt = {y: totals(df[df["Year"] == y]) for y in (2024, 2025, 2026)}
sp = lambda k: [tt[y][k] for y in tt if tt[y]["appeared"]]
render_kpi_row([
    dict(icon="groups", value=format_compact(cur["appeared"]), label=f"Appeared · {year}", delta=d_app[0], delta_positive=d_app[1], accent="blue", spark=sp("appeared")),
    dict(icon="check_circle", value=format_compact(cur["passed"]), label=f"Passed · {year}", delta=d_pas[0], delta_positive=d_pas[1], accent="green", spark=sp("passed")),
    dict(icon="cancel", value=format_compact(cur["failed"]), label=f"Failed · {year}", delta=d_fail[0], delta_positive=d_fail[1], accent="red", spark=sp("failed")),
    dict(icon="percent", value=f"{cur['pct']:.1f}%", label=f"Pass Rate · {year}", delta=d_pct[0], delta_positive=d_pct[1], accent="gold", spark=[tt[y]["pct"] for y in tt if tt[y]["appeared"]]),
    dict(icon="account_balance", value=str(df[df["Year"] == year]["Board"].nunique()), label=f"Boards reporting · {year}", accent="blue"),
])
st.caption(f"Changes compare {year} with {other}, using only boards that published both years." if other else f"{year} is the first year, so there is nothing earlier to compare with.")

gain, loss = C.top_movers(df, year, other) if other else (None, None)
if gain:
    a, b = st.columns(2)
    a.success(f"**Top gainer:** {gain[0]}  ({gain[1]:+.1f} pts vs {other})")
    b.error(f"**Top decliner:** {loss[0]}  ({loss[1]:+.1f} pts vs {other})")

left, right = st.columns([1.6, 1])
with left:
    with chart_card("Pakistan Map", f"{cls} · Appeared by province, {year}. Hover for all years."):
        st.plotly_chart(C.chart_pakistan_map(df, year), width="stretch")
with right:
    with chart_card("Top 3 Boards by Pass %", f"{cls} · highest pass rate in each year"):
        render_top_boards(df, n=3, years=(2026, 2025, 2024))
with chart_card("Province Snapshot", f"{cls} · {year}"):
    metric = st.pills("Metric", ["Appeared", "Pass %"], default="Appeared", key="ov_tile_metric", label_visibility="collapsed") or "Appeared"
    render_province_tiles(df, metric, year)

two("Overall Performance", f"{cls} · Appeared vs Passed vs Failed", C.chart_yoy_totals(df),
    "Pass % Trend by Province", f"{cls} · aggregate pass rate", C.chart_province_pass_trend(df))
two("Board Pass Rate", f"{cls} · {year}", C.chart_board_pass_rate(df, year),
    "Pass % Change by Board", f"{year} vs {other}" if other else "Needs an earlier year",
    C.chart_yoy_change_by_board(df, year, other) if other else C.empty("2024 is the first year in the dataset"))
two("Pass % Across Years by Board", "Boards with at least two years of data", C.chart_trend_lines(df),
    "Share of Candidates by Board", f"{cls} · Appeared, {year}", C.chart_appeared_share(df, year))
_hh = max(340, 30 * df[df["Year"] == year]["Board"].nunique() + 80)
two("Board Size and Pass Rate", f"{cls} · {year} · box size = candidates, colour = pass %", X.chart_treemap(df, year, _hh),
    "Pass % Before vs After", f"{cls} · {other} → {year}, boards that published both" if other else "Needs an earlier year",
    X.chart_dumbbell(df, year, other) if other else C.empty("No earlier year to compare with"))
if g.empty: 
    with chart_card("Gender", f"{cls}"): not_published(cls, "Gender data")
else:
    two("Gender: Pass Rate", f"{cls} · Male vs Female", C.chart_gender_pass_rate(g), "Gender: Share of Candidates", f"{cls} · {year}", C.chart_gender_share(g, year))
if c.empty:
    with chart_card("Regular vs Private", f"{cls}"): not_published(cls, "Regular vs Private data")
else:
    two("Regular vs Private: Pass Rate", f"{cls}", C.chart_category_pass_rate(c), "Regular vs Private: Share", f"{cls} · {year}", C.chart_category_share(c, year))

section("Compare All 4 Classes")
st.caption(f"Province filter applies. Year: {year}.")
two("Pass % by Class", "All years", C.chart_class_pass_by_year(full), "Pass % Trend by Class", "2024-2026", C.chart_class_trend(full))
two("Candidates Appeared by Class", "All years", C.chart_class_appeared(full), "Share of Candidates by Class", f"{year}", C.chart_class_share(full, year))
with chart_card("Pass % Heatmap · Board × Class", f"{year} · blank = board has no data for that class"):
    st.plotly_chart(C.chart_heatmap(full, year), width="stretch")
section("Important Points")
render_important_points()