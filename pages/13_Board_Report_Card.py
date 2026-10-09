"""pages/13_Board_Report_Card.py - one board, all 4 classes: rank, 3-year trend, best/weakest areas + PDF."""
import streamlit as st
import pandas as pd
from html import escape
from config.settings import CLASS_COLORS
from components.page_boot import boot
from components.page_header import render_page_header
from components.filter_bar import render_filter_bar
from components.kpi_card import render_kpi_row, format_compact
from components.chart_card import chart_card
from components.report_pdf import build_pdf
from data.board_report import board_list, board_report, highlights, ordinal, waffle_groups
import charts.extra_charts as X

boards = board_list()
boot("Board Report Card", "One-page report for a board across 9th, 10th, 11th and 12th: rank, 3-year trend, best and weakest areas, with PDF download.",
     stat_label="Boards", stat_value=str(len(boards)), stat_icon="assignment")

year = render_page_header("Select Year to View Results", year_options=[2026, 2025, 2024], year_default=2026, key="rc_year")
board = render_filter_bar("Board", boards, default="Lahore" if "Lahore" in boards else boards[0], key="rc_board") or "Lahore"
rep = board_report(board, year)
cl = rep["classes"]
if not cl:
    st.info(f"No results are published for {board} up to {year}.")
    st.stop()

ranks = {r["class"]: r for r in cl}
best = min(cl, key=lambda r: r["rank"] / r["n_boards"]); worst = max(cl, key=lambda r: r["rank"] / r["n_boards"])
render_kpi_row([
    dict(icon="military_tech", value=f"#{rep['avg_rank']:.1f}", label="Average rank across classes", accent="gold"),
    dict(icon="emoji_events", value=f"{ordinal(best['rank'])} of {best['n_boards']}", label=f"Best position · {best['class']}", accent="green"),
    dict(icon="trending_down", value=f"{ordinal(worst['rank'])} of {worst['n_boards']}", label=f"Weakest position · {worst['class']}", accent="red"),
    dict(icon="groups", value=format_compact(sum(r["appeared"] for r in cl)), label=f"Candidates · {len(cl)} classes", accent="blue"),
])

left, right = st.columns([3, 1])
with right:
    st.download_button("⬇  Download PDF report", data=build_pdf(rep), file_name=f"BISE_{board.replace(' ', '_')}_Report_Card_{year}.pdf",
                       mime="application/pdf", type="primary", width="stretch", key="rc_pdf")
with left:
    if year != 2024:
        short = [r["class"] for r in cl if r["year"] != year]
        if short: st.caption(f"{', '.join(short)} not published for {year}; the latest earlier year is shown instead.")

cols = st.columns(4)
for col, c in zip(cols, ["9th", "10th", "11th", "12th"]):
    r = ranks.get(c)
    with col:
        with st.container(border=True):
            color = CLASS_COLORS[c]
            if not r:
                st.markdown(f'<div style="font-weight:700;color:{color}">{c}</div><div style="color:#6B7280;font-size:.85rem;margin-top:.4rem">Not published for this board</div>', unsafe_allow_html=True)
                continue
            d = r["delta"]
            dtxt = "first year" if d is None else f"{d:+.1f} pts vs {r['prev_year']}"
            dcol = "#6B7280" if d is None else ("#15803D" if d >= 0 else "#B91C1C")
            def line(lbl, d_):
                if not d_: return ""
                return (f'<div style="font-size:.78rem;margin-top:.3rem"><span style="color:#6B7280">{lbl}</span><br>'
                        f'<b style="color:#15803D">▲ {escape(str(d_["best"][0]))}</b> {d_["best"][1]:.1f}%<br>'
                        f'<b style="color:#B91C1C">▼ {escape(str(d_["weak"][0]))}</b> {d_["weak"][1]:.1f}%</div>')
            nt = f'<div style="font-size:.72rem;color:#B45309;margin-top:.3rem">{escape(r["note"])}</div>' if r["note"] else ""
            st.markdown(
                f'<div style="font-weight:700;color:{color};font-size:1rem">{c} · {r["year"]}</div>'
                f'<div style="font-size:1.9rem;font-weight:800;color:#141B3C;line-height:1.15">{r["pct"]:.1f}%</div>'
                f'<div style="font-size:.85rem;color:#141B3C"><b>{ordinal(r["rank"])}</b> of {r["n_boards"]} boards</div>'
                f'<div style="font-size:.8rem;color:{dcol};font-weight:600">{dtxt}</div>'
                f'<div style="font-size:.78rem;color:#6B7280">All-board avg {r["avg_pct"]:.1f}%</div>'
                f'{line("Subjects", r["subject"])}{line("Groups", r["group"])}{nt}', unsafe_allow_html=True)

with chart_card("Key Points", f"{board} · for management"):
    for t in highlights(rep): st.markdown(f"- {t}")

with chart_card("If 100 Students Sat the Exam", f"{board} · each square is 1 candidate in 100, for the year shown on each class"):
    mode = st.pills("Split by", ["Pass / fail", "Gender", "Regular vs Private"], default="Pass / fail", key="rc_waffle", label_visibility="collapsed") or "Pass / fail"
    wcols = st.columns(4)
    for wc, cname in zip(wcols, ["9th", "10th", "11th", "12th"]):
        r = ranks.get(cname)
        with wc:
            st.markdown(f'<div style="font-weight:700;color:{CLASS_COLORS[cname]}">{cname}{" · " + str(r["year"]) if r else ""}</div>', unsafe_allow_html=True)
            wg = waffle_groups(board, cname, r["year"], mode) if r else None
            if wg is None:
                st.caption("Not published for this board" if mode == "Pass / fail" or not r else f"{mode} not published for {cname}")
                continue
            st.plotly_chart(X.chart_waffle(wg), width="stretch", key=f"rc_wf_{cname}")
            if mode == "Pass / fail": st.caption(f"**{wg[0]['n']}** of 100 passed")
st.caption("Squares are rounded so every grid adds up to exactly 100. In Gender and Regular vs Private views the split follows each group's share of candidates, and the faded squares are those who failed.")

a, b = st.columns(2)
with a:
    with chart_card("Pass % Trend", f"{board} · 2024-2026, by class"):
        st.plotly_chart(X.chart_report_trend(rep), width="stretch")
with b:
    with chart_card("This Board vs All Boards", f"{board} · pass %, same class and year"):
        st.plotly_chart(X.chart_report_vs_avg(rep), width="stretch")
with chart_card("Rank by Class", f"{board} · taller bar = better rank among boards that published that class"):
    st.plotly_chart(X.chart_report_rank(rep), width="stretch")

with chart_card("Detail Table", "Same numbers as the PDF"):
    t = pd.DataFrame([{
        "Class": r["class"], "Year": r["year"], "Appeared": round(r["appeared"]), "Passed": round(r["passed"]), "Pass %": round(r["pct"], 1),
        "Rank": f"{r['rank']} of {r['n_boards']}", "Change (pts)": None if r["delta"] is None else round(r["delta"], 1),
        "All-board avg %": round(r["avg_pct"], 1),
        "Best subject": f"{r['subject']['best'][0]} ({r['subject']['best'][1]:.1f}%)" if r["subject"] else "-",
        "Weakest subject": f"{r['subject']['weak'][0]} ({r['subject']['weak'][1]:.1f}%)" if r["subject"] else "-",
        "Best group": f"{r['group']['best'][0]} ({r['group']['best'][1]:.1f}%)" if r["group"] else "-",
        "Weakest group": f"{r['group']['weak'][0]} ({r['group']['weak'][1]:.1f}%)" if r["group"] else "-"} for r in cl])
    st.dataframe(t, width="stretch", hide_index=True)
    st.download_button("Download table (CSV)", t.to_csv(index=False).encode(), f"bise_{board}_report_{year}.csv", "text/csv", key="rc_csv")
st.caption("Rank = position among boards that published that class and year, by Pass % (Passed ÷ Appeared). Best/weakest subject or group needs "
           "at least 1% of the board's candidates (minimum 100). Subject data is published by only some boards; group data by more.")