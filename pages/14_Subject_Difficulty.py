"""pages/14_Subject_Difficulty.py - which subjects are hardest in each class, and how that changes 9th -> 12th."""
import streamlit as st
import pandas as pd
from config.settings import CLASSES, CLASS_COLORS
from components.page_boot import boot, no_data
from components.page_header import render_page_header
from components.kpi_card import render_kpi_row
from components.chart_card import chart_card
from data.loader import load, agg
from data.subject_names import unify
import charts.extra_charts as X


def section(t):
    st.markdown(f'<div class="page-header-title" style="margin:1.2rem 0 .4rem">{t}</div>', unsafe_allow_html=True)


boot("Subject Difficulty", "Which subjects are hardest in 9th, 10th, 11th and 12th, and how difficulty changes from class to class.",
     stat_label="Classes", stat_value="4", stat_icon="psychology")
st.caption("Difficulty = Fail % (100 − Pass %). Higher means harder. Only boards that publish subject results are included. "
           "9th has 2025-26, 11th has 2024-25, so default is 2025, the one year where all four classes exist.")
year = render_page_header("Select Year", year_options=[2026, 2025, 2024], year_default=2025, key="sd_year")

c1, c2 = st.columns([1.2, 1])
with c1:
    min_n = st.select_slider("Minimum candidates for a subject to be ranked", options=[500, 1000, 2000, 5000, 10000, 20000, 50000],
                             value=5000, key="sd_min")
with c2:
    like = st.toggle("Like-for-like across classes (same boards in every class)", value=True, key="sd_like",
                     help="Applies to the class-to-class section. Different boards publish different classes, which can distort comparisons.")

S = load("subject"); S = S[S["Year"] == year]
if S.empty: no_data("any", year, S)
S = agg(S.assign(Subject=S["Subject"].map(unify)), ["Class", "Board", "Subject"])
have = [c for c in CLASSES if c in S["Class"].unique()]
if len(have) < 4:
    st.warning(f"{', '.join(c for c in CLASSES if c not in have)} has no subject data for {year}, so only {', '.join(have)} are shown.")

# ---------- hardest subject per class (all boards that publish)
by_cls = {c: agg(S[S["Class"] == c], ["Subject"]) for c in have}
cards = []
for c in have:
    d = by_cls[c]; d = d[d["Appeared"] >= min_n]
    if d.empty: continue
    h = d.sort_values("Pass %").iloc[0]
    cards.append(dict(icon="school", value=f"{100 - h['Pass %']:.1f}%", label=f"Hardest in {c} · {h['Subject']}", accent="red"))
if cards: render_kpi_row(cards)

section("Hardest Subjects in Each Class")
for row in (have[:2], have[2:4]):
    if not row: continue
    cols = st.columns(2)
    for col, c in zip(cols, row):
        with col:
            n_b = S[S["Class"] == c]["Board"].nunique()
            with chart_card(f"{c} · Top 8 Hardest", f"{year} · {n_b} boards with subject data · {min_n:,}+ candidates"):
                st.plotly_chart(X.chart_hardest(by_cls[c], c, 8, min_n), width="stretch")

# ---------- class to class
section("How Difficulty Changes from Class to Class")
T = S
if like and len(have) > 1:
    common = set.intersection(*[set(S[S["Class"] == c]["Board"]) for c in have])
    if common:
        T = S[S["Board"].isin(common)]
        st.caption(f"Like-for-like: {len(common)} boards publish subjects for every class shown ({', '.join(sorted(common))}).")
    else:
        st.caption("No board publishes subjects for every class, so all boards are used (not like-for-like).")
else:
    st.caption("All boards that publish each class are used, so the board mix differs between classes.")
tab = agg(T, ["Class", "Subject"])
tab = tab[tab["Appeared"] >= min_n]
tab["Fail %"] = 100 - tab["Pass %"]
piv_all = tab.pivot(index="Subject", columns="Class", values="Fail %").reindex(columns=[c for c in CLASSES if c in tab["Class"].unique()])
multi = piv_all[piv_all.notna().sum(axis=1) >= 2]
if multi.empty:
    st.info("No subject is taught in two or more classes with this many candidates. Lower the minimum candidates.")
    st.stop()
core = ["English", "Urdu", "Islamic Education", "Pakistan Studies", "Mathematics", "Physics", "Chemistry", "Biology", "Computer Science"]
default = [s for s in core if s in multi.index] or list(multi.index[:6])
subs = st.multiselect("Subjects to compare", sorted(multi.index), default=default, key="sd_subs")
piv = multi.loc[[s for s in subs if s in multi.index]]
a, b = st.columns(2)
with a:
    with chart_card("Fail % by Class", f"{year} · each line is a subject"):
        st.plotly_chart(X.chart_fail_lines(piv), width="stretch")
with b:
    with chart_card("Subject × Class Heatmap", f"{year} · Fail %, darker red = harder"):
        st.plotly_chart(X.chart_fail_heat(piv), width="stretch")

# insights + table
rows, lines = [], []
for s, r in piv.iterrows():
    r = r.dropna(); hard, easy = r.idxmax(), r.idxmin()
    first, last = r.index[0], r.index[-1]
    rows.append({"Subject": s, **{c: round(r[c], 1) if c in r else None for c in piv.columns},
                 f"Change {first}→{last} (pts)": round(r[last] - r[first], 1), "Hardest class": hard, "Easiest class": easy})
    if hard != easy:
        lines.append(f"**{s}** is hardest in **{hard}** ({r[hard]:.1f}% fail) and easiest in **{easy}** ({r[easy]:.1f}%).")
with chart_card("What the Numbers Say", f"{year} · auto-generated from the selection above"):
    if lines:
        for t in lines: st.markdown(f"- {t}")
    else:
        st.write("Select subjects above.")
if rows:
    tbl = pd.DataFrame(rows)
    with chart_card("Subject Difficulty Table", "Fail % by class · change shown from the first to the last class where the subject appears"):
        st.dataframe(tbl, width="stretch", hide_index=True)
        st.download_button("Download CSV", tbl.to_csv(index=False).encode(), f"bise_subject_difficulty_{year}.csv", "text/csv", key="sd_csv")
st.caption("Subject names are merged where boards spell the same subject differently (e.g. Translation of the Holy Quran). "
           "Optional or elective subjects with few candidates are hidden by the minimum-candidates setting. "
           "A subject can differ between classes in content, so read the change as a signal, not a like-for-like exam.")
