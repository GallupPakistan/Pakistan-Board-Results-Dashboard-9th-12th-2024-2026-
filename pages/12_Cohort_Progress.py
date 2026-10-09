"""pages/12_Cohort_Progress.py - follow a batch of students through 9th -> 10th -> 11th -> 12th."""
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

import plotly.express as px
from data.cohort import chains, funnel, transition

boot("Cohort Progress", "Follow a batch of students from one class to the next: how many pass, how many come back, how results change.",
     stat_label="Cohorts", stat_value="3", stat_icon="route")
full = load("overall")
ch = chains(full)
label = st.selectbox("Cohort (batch of students)", list(ch), index=list(ch).index(next((k for k in ch if k.endswith("12th 2026")), list(ch)[0])), key="co_chain")
steps = ch[label]
f = funnel(full, steps)
st.caption(f"Same {int(f['Boards'].iloc[0])} boards in every step, so the steps are comparable. Assumes the batch sitting class N in year Y sits class N+1 in year Y+1. "
           "This is a proxy: private candidates, repeaters and board changes mean it is not exactly the same students.")
cards = []
for i in range(len(steps) - 1):
    p_prev, a_next = f["Appeared"].iloc[i], f["Appeared"].iloc[i + 1]
    cards.append(dict(icon="trending_flat", value=f"{a_next / p_prev * 100:.0f}%", label=f"{steps[i+1][0]} appeared ÷ {steps[i][0]} appeared", accent="blue" if i % 2 == 0 else "gold"))
cards.append(dict(icon="percent", value=f"{f['Pass %'].iloc[-1] - f['Pass %'].iloc[0]:+.1f} pts", label="Pass rate: last step vs first", accent="green" if f['Pass %'].iloc[-1] >= f['Pass %'].iloc[0] else "red"))
cards.append(dict(icon="groups", value=format_compact(f["Appeared"].iloc[0]), label=f"Started: {f['Step'].iloc[0]}", accent="blue"))
render_kpi_row(cards[:5])
two("Cohort Funnel", "Appeared and passed at each step", C.chart_cohort_funnel(f),
    "Pass % at each Step", "same boards", C.base(px.line(f, x="Step", y="Pass %", markers=True).update_traces(line=dict(width=3), marker=dict(size=10)).update_yaxes(range=[0, 100]), 400))
one("Candidate Flow", "Appeared → passed / failed → next class · same boards in every step", X.chart_cohort_sankey(f))
st.caption("Grey = passed but did not sit the next class. Gold = candidates in the next class beyond those who passed (private candidates, repeaters or students from other boards). Same proxy as above, not the same individual students.")
labels = [f"{steps[i][0]} {steps[i][1]} → {steps[i+1][0]} {steps[i+1][1]}" for i in range(len(steps) - 1)]
section("Board-level progression")
pick = st.selectbox("Step", labels, key="co_step") if len(labels) > 1 else labels[0]
i = labels.index(pick)
t = transition(full, steps[i], steps[i + 1])
la, lb = f"{steps[i][0]} {steps[i][1]}", f"{steps[i+1][0]} {steps[i+1][1]}"
if t.empty:
    st.info("No board has data for both steps.")
else:
    two("Progression by Board", f"{steps[i+1][0]} appeared as % of {steps[i][0]} appeared · 100% = same number sat the next class", C.chart_progression_by_board(t, la, lb),
        "Pass % Before vs After", "above the dotted line = results improved", C.chart_cohort_scatter(t, f"{steps[i][0]} {steps[i][1]}", lb))
    with chart_card("Cohort Table", "Board by board"):
        st.dataframe(t.round(2), width="stretch", hide_index=True)
        st.download_button("Download cohort CSV", t.round(2).to_csv(index=False).encode(), "bise_cohort_progress.csv", "text/csv")
st.caption("Below 100% means fewer candidates sat the next class (students leaving or not yet appearing); above 100% means private candidates, repeaters or students from other boards joined. 11th Mardan and Bannu 2025 are 'promoted' results, so their pass % is not comparable.")