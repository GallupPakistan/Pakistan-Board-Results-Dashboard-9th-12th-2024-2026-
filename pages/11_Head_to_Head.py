"""pages/11_Head_to_Head.py - put ANY two selections (class + year + province) side by side."""
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


boot("Head to Head", "Pick any two selections (class, year, province) and compare them board by board.",
     stat_label="Compare", stat_value="A vs B", stat_icon="compare_arrows")
full = load("overall"); G = load("gender")
YEARS_D = [2026, 2025, 2024]
st.markdown('<div class="page-header-title" style="margin:.2rem 0 .4rem">Choose the two selections</div>', unsafe_allow_html=True)
ca, cb = st.columns(2)
def picker(col, tag, d_cls, d_year):
    with col:
        st.markdown(f"**Selection {tag}**")
        c1, c2, c3 = st.columns(3)
        cls = c1.selectbox("Class", CLASSES, index=CLASSES.index(d_cls), key=f"h_{tag}_cls")
        yr = c2.selectbox("Year", YEARS_D, index=YEARS_D.index(d_year), key=f"h_{tag}_yr")
        pv = c3.selectbox("Province", ["All Provinces"] + list(PROVINCE_BOARD_MAP), key=f"h_{tag}_pv")
    return cls, yr, pv
A = picker(ca, "A", "12th", 2026)
B = picker(cb, "B", "12th", 2025)
same = st.toggle("Compare only boards present in both selections (like-for-like)", value=True, key="h_same")

def pick(sel, df):
    cls, yr, pv = sel
    d = df[(df["Class"] == cls) & (df["Year"] == yr)]
    return d if pv == "All Provinces" else d[d["Board"].isin(PROVINCE_BOARD_MAP[pv])]
a, b = pick(A, full), pick(B, full)
la, lb = f"A · {A[0]} {A[1]}", f"B · {B[0]} {B[1]}"
if a.empty or b.empty:
    st.info(f"No data for {la if a.empty else lb} with this province filter. Pick another class or year (9th: 2025-26, 10th: 2024-26, 11th: 2024-25, 12th: 2024-26).")
    st.stop()
if same:
    common = set(a["Board"]) & set(b["Board"])
    if not common:
        st.info("The two selections share no board. Turn off the like-for-like switch or change the selection."); st.stop()
    a, b = a[a["Board"].isin(common)], b[b["Board"].isin(common)]
ta, tb = totals(a), totals(b)
diff = ta["pct"] - tb["pct"]
(st.success if diff >= 0 else st.warning)(
    f"**{la if diff >= 0 else lb}** has the higher pass rate: {max(ta['pct'], tb['pct']):.1f}% vs {min(ta['pct'], tb['pct']):.1f}% "
    f"(difference {abs(diff):.1f} points, {a['Board'].nunique()} boards compared).")
render_kpi_row([
    dict(icon="percent", value=f"{ta['pct']:.1f}%", label=f"{la} · Pass Rate", accent="blue"),
    dict(icon="percent", value=f"{tb['pct']:.1f}%", label=f"{lb} · Pass Rate", accent="gold"),
    dict(icon="balance", value=f"{diff:+.1f} pts", label="Pass rate difference (A − B)", accent="green" if diff >= 0 else "red"),
    dict(icon="groups", value=f"{format_compact(ta['appeared'])} vs {format_compact(tb['appeared'])}", label="Appeared (A vs B)", accent="blue"),
])
two("Pass % by Board", "A vs B", C.chart_h2h_boards(a, b, la, lb), "Gap by Board", "positive = A ahead", C.chart_h2h_gap(a, b, la, lb))
two("Appeared / Passed / Failed", "A vs B totals", C.chart_h2h_totals(a, b, la, lb), "Province Pass %", "A vs B", C.chart_h2h_province(a, b, la, lb))
ga, gb = pick(A, G), pick(B, G)
if same: ga, gb = ga[ga["Board"].isin(a["Board"])], gb[gb["Board"].isin(b["Board"])]
if not ga.empty and not gb.empty:
    one("Gender Pass %", "A vs B (boards that publish gender data)", C.chart_h2h_gender(ga, gb, la, lb))
else:
    st.caption("Gender chart skipped: gender data is not published for one of the selections.")
cls_set = list(dict.fromkeys([A[0], B[0]]))
one("Pass % Trend", "Classes in the comparison, all years", C.chart_class_trend(full[full["Class"].isin(cls_set)]))
m = agg(a, ["Board"])[["Board", "Appeared", "Pass %"]].merge(agg(b, ["Board"])[["Board", "Appeared", "Pass %"]], on="Board", how="outer", suffixes=(f" {la}", f" {lb}"))
m["Gap (A−B)"] = m[f"Pass % {la}"] - m[f"Pass % {lb}"]
m = m.sort_values("Gap (A−B)", ascending=False).round(2)
with chart_card("Comparison Table", "Board by board"):
    st.dataframe(m, width="stretch", hide_index=True)
    st.download_button("Download comparison CSV", m.to_csv(index=False).encode(), "bise_head_to_head.csv", "text/csv")
