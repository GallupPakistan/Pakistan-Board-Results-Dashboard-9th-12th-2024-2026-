"""pages/2_Class_Comparison.py - 9th vs 10th vs 11th vs 12th (the core comparison page)."""
import streamlit as st
import pandas as pd
from config.settings import CLASSES, CLASS_COLORS, DEFAULT_CLASS, PROVINCE_BOARD_MAP
from components.page_boot import boot, year_and_class, delta_kpi, no_data, not_published
from components.filter_bar import render_filter_bar
from components.kpi_card import render_kpi_row, format_compact
from components.chart_card import chart_card
from components.insights import build_insights
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

boot("Class Comparison", "Compare 9th, 10th, 11th and 12th class results: classes, boards, provinces, years.")
year, _ = year_and_class("cc", title="Select Year to Compare Classes")
other = prev_year(year)
prov = render_filter_bar("Province", ["All Provinces"] + list(PROVINCE_BOARD_MAP), default="All Provinces", key="cc_prov") or "All Provinces"
full = load("overall")
if prov != "All Provinces": full = full[full["Board"].isin(PROVINCE_BOARD_MAP[prov])]
cur = full[full["Year"] == year]
if cur.empty: no_data("any", year, full)

cards = []
for i, cl in enumerate(CLASSES):
    x = cur[cur["Class"] == cl]
    if x.empty:
        cards.append(dict(icon="school", value="-", label=f"{cl} · no {year} data", accent=["blue", "gold", "green", "red"][i])); continue
    t = totals(x); dtxt, dpos = "", True
    if other:
        ll = like_for_like(full[full["Class"] == cl], year, other)
        if len(ll):
            a = ll[ll["Year"] == year]; b = ll[ll["Year"] == other]
            dtxt, dpos = delta_kpi(a["Passed"].sum() / a["Appeared"].sum() * 100, b["Passed"].sum() / b["Appeared"].sum() * 100, pct=True)
    cards.append(dict(icon="school", value=f"{t['pct']:.1f}%", label=f"{cl} Pass Rate · {year}", delta=dtxt, delta_positive=dpos, accent=["blue", "gold", "green", "red"][i]))
render_kpi_row(cards)
st.caption(f"{format_compact(totals(cur)['appeared'])} candidates across the classes shown. Boards without data for a class are skipped.")

with chart_card("Key Insights", f"Generated from the data · {year}" + (f" vs {other}" if other else "")):
    for line in build_insights(full, year, other, load("gender")):
        st.markdown("- " + line)
two("Pass % by Class", "All years", C.chart_class_pass_by_year(full), "Pass % Trend by Class", "2024-2026", C.chart_class_trend(full))
two("Candidates Appeared by Class", "All years", C.chart_class_appeared(full), "Share of Candidates by Class", f"{year}", C.chart_class_share(full, year))
two("Change in Pass % by Class", f"{other} → {year}, same boards" if other else "Needs an earlier year",
    C.chart_class_yoy(full, year, other) if other else C.empty("2024 is the first year"),
    "Best vs Weakest Board in each Class", f"{year}", C.chart_spread(full, year))
one("Pass % Heatmap · Board × Class", f"{year} · blank = board has no data for that class", C.chart_heatmap(full, year))
one("Board-wise Pass % by Class", f"{year}", C.chart_board_by_class(full, year))
two("Spread of Board Pass Rates", f"{year} · each dot is a board", C.chart_class_box(full, year),
    "Board Size vs Pass %", f"{year} · bubble = candidates", C.chart_class_bubble(full, year))
one("Province-wise Pass % by Class", f"{year}", C.chart_province_by_class(full, year))
g = load("gender"); g = g[g["Board"].isin(full["Board"].unique())]
if not g[g["Year"] == year].empty:
    two("Gender Pass % by Class", f"{year}", C.chart_gender_by_class(g, year), "Female-Male Gap by Class", "All years", C.chart_gender_gap_by_class(g))

section("Board Ranking Across Classes")
rt = C.rank_table(full, year)
two("Board Rank by Class", f"{year} · rank 1 = best pass % in that class", C.chart_rank_bump_classes(full, year),
    "Board Consistency", "average rank across classes (colour = rank spread)", C.chart_rank_consistency(rt))
cls_r = st.selectbox("Rank movement over years for class", CLASSES, index=CLASSES.index("12th"), key="cc_rank_cls")
one(f"{cls_r} · Board Rank by Year", "rank 1 = best pass % that year", C.chart_rank_bump_years(full, cls_r))
with chart_card("Ranking Table", f"{year} · rank of every board in each class"):
    st.dataframe(rt, width="stretch", hide_index=True)
    st.download_button("Download ranking CSV", rt.to_csv(index=False).encode(), "bise_board_ranking.csv", "text/csv")
