"""components/top_boards.py - Top-N boards by pass % for each year."""
import pandas as pd
import streamlit as st
from data.loader import agg


def _block(df, year, n):
    rows = agg(df[df["Year"] == year], ["Board"]).sort_values("Pass %", ascending=False).head(n)
    if rows.empty: return None
    mx = float(rows["Pass %"].max()) or 1.0
    items = "".join(
        f'<div class="topboard-row"><div class="topboard-rank">{i}</div><div class="topboard-name">{r.Board}</div>'
        f'<div class="topboard-bar"><div class="topboard-fill" style="width:{max(4.0, r._5 / mx * 100):.1f}%"></div></div>'
        f'<div class="topboard-value">{r._5:.1f}%</div></div>'
        for i, r in enumerate(rows.rename(columns={"Pass %": "_5"}).itertuples(), 1))
    return f'<div class="topboard-year">Top {n} · {year}</div><div class="topboard-list">{items}</div>'


def render_top_boards(df: pd.DataFrame, n: int = 3, years=(2026, 2025, 2024)) -> None:
    blocks = [b for b in (_block(df, y, n) for y in years) if b]
    if not blocks:
        st.info("No pass-percentage rows available."); return
    st.markdown('<div class="topboard-root">' + "".join(blocks) + "</div>", unsafe_allow_html=True)
