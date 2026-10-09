"""pages/15_Province_Comparison.py - Punjab vs Khyber Pakhtunkhwa vs Federal (FBISE): classes, gender, Regular vs Private."""
import streamlit as st
import pandas as pd
from config.settings import CLASSES, PROVINCE_BOARD_MAP
from components.page_boot import boot, year_and_class, delta_kpi, no_data, not_published
from components.kpi_card import render_kpi_row, format_compact
from components.chart_card import chart_card
from data.loader import load, agg, prev_year, like_for_like
import charts.extra_charts as X

PROVS = ["Punjab", "Khyber Pakhtunkhwa", "Federal"]
ACCENT = {"Punjab": "blue", "Khyber Pakhtunkhwa": "green", "Federal": "gold"}


def section(t):
    st.markdown(f'<div class="page-header-title" style="margin:1.2rem 0 .4rem">{t}</div>', unsafe_allow_html=True)


boot("Province Comparison", "Punjab vs Khyber Pakhtunkhwa vs Federal (FBISE): classes, gender and Regular vs Private (default: 12th class, 2026).",
     stat_label="Provinces", stat_value="3", stat_icon="map")
year, cls = year_and_class("pv", title="Select Year to View Results")
other = prev_year(year)

O = load("overall"); O = O[O["Province"].isin(PROVS)]
G = load("gender"); G = G[G["Province"].isin(PROVS)]
C = load("category"); C = C[C["Province"].isin(PROVS)]
oy, oc = O[O["Year"] == year], O[(O["Year"] == year) & (O["Class"] == cls)]
if oc.empty: no_data(cls, year, O[O["Class"] == cls])
st.caption("Federal means FBISE (Islamabad), a single board, while Punjab has up to 8 boards and Khyber Pakhtunkhwa up to 6. "
           "Province figures pool the boards that published that class and year.")
if cls == "11th" and year == 2025:
    st.warning("11th 2025: Mardan and Bannu report promoted results (pass % near 99%), which lifts the Khyber Pakhtunkhwa figure.")

# ---------- KPIs (selected class)
cards = []
for p in PROVS:
    d = O[(O["Class"] == cls) & (O["Province"] == p)]
    cur = d[d["Year"] == year]
    if cur.empty:
        cards.append(dict(icon="map", value="-", label=f"{p} · not published", accent=ACCENT[p])); continue
    pct = cur["Passed"].sum() / cur["Appeared"].sum() * 100
    dl = ("", True)
    if other:
        ll = like_for_like(d, year, other)
        if len(ll):
            f = lambda y: ll[ll["Year"] == y]["Passed"].sum() / ll[ll["Year"] == y]["Appeared"].sum() * 100
            dl = delta_kpi(f(year), f(other), pct=True)
    cards.append(dict(icon="map", value=f"{pct:.1f}%", label=f"{p} · {cls} pass rate · {cur['Board'].nunique()} board(s)",
                      delta=dl[0], delta_positive=dl[1], accent=ACCENT[p]))
pp = agg(oc, ["Province"]).sort_values("Pass %")
if len(pp) > 1:
    cards.append(dict(icon="balance", value=f"{pp['Pass %'].iloc[-1] - pp['Pass %'].iloc[0]:.1f} pts",
                      label=f"Gap · {pp['Province'].iloc[-1]} vs {pp['Province'].iloc[0]}", accent="red"))
render_kpi_row(cards)
st.caption(f"Changes compare {year} with {other}, using only boards that published both years." if other else f"{year} is the first year, so there is nothing earlier to compare with.")

# ---------- classes
section("Pass Rate by Class")
a, b = st.columns(2)
with a:
    with chart_card("Pass % by Province and Class", f"{year} · all classes published"):
        st.plotly_chart(X.chart_prov_class(oy), width="stretch")
with b:
    with chart_card("Pass % Trend by Province", f"{cls} · 2024-2026"):
        st.plotly_chart(X.chart_prov_trend(O[O["Class"] == cls]), width="stretch")

# ---------- gender
section("Gender")
gy = G[G["Year"] == year]
if gy.empty:
    not_published("any", "Gender data")
else:
    a, b = st.columns(2)
    with a:
        with chart_card("Pass % by Province, Gender and Class", f"{year} · Male vs Female"):
            st.plotly_chart(X.chart_prov_gender(gy), width="stretch")
    with b:
        with chart_card("Female − Male Gap by Province", f"{year} · points; above zero = girls pass more"):
            st.plotly_chart(X.chart_prov_gap(gy, "Gender", "Female", "Male", "Female − Male"), width="stretch")

# ---------- regular vs private
section("Regular vs Private")
cy = C[C["Year"] == year]
if cy.empty:
    not_published("any", "Regular vs Private data")
else:
    st.caption("Regular vs Private is published for " + ", ".join(sorted(cy["Class"].unique(), key=CLASSES.index)) + f" in {year} (not for 11th).")
    a, b = st.columns(2)
    with a:
        with chart_card("Pass % by Province, Category and Class", f"{year} · Regular vs Private"):
            st.plotly_chart(X.chart_prov_category(cy), width="stretch")
    with b:
        with chart_card("Private − Regular Gap by Province", f"{year} · points; above zero = private candidates pass more"):
            st.plotly_chart(X.chart_prov_gap(cy, "Category", "Private", "Regular", "Private − Regular"), width="stretch")

# ---------- table
section("Province Summary Table")
rows = []
for c in CLASSES:
    for p in PROVS:
        o = oy[(oy["Class"] == c) & (oy["Province"] == p)]
        if o.empty: continue
        row = {"Class": c, "Province": p, "Boards": o["Board"].nunique(), "Appeared": int(o["Appeared"].sum()),
               "Pass %": round(o["Passed"].sum() / o["Appeared"].sum() * 100, 1)}
        for df_, col, split, plus, minus, name in ((G, "g", "Gender", "Female", "Male", "Female − Male (pts)"),
                                                  (C, "c", "Category", "Private", "Regular", "Private − Regular (pts)")):
            d = agg(df_[(df_["Year"] == year) & (df_["Class"] == c) & (df_["Province"] == p)], [split])
            d = d.set_index(split)["Pass %"]
            row[name] = round(d[plus] - d[minus], 1) if plus in d.index and minus in d.index else None
        rows.append(row)
tbl = pd.DataFrame(rows)
with chart_card("All Classes", f"{year} · Pass % pools the boards that published; gaps need both groups published"):
    st.dataframe(tbl, width="stretch", hide_index=True)
    st.download_button("Download CSV", tbl.to_csv(index=False).encode(), f"bise_province_comparison_{year}.csv", "text/csv", key="pv_csv")
