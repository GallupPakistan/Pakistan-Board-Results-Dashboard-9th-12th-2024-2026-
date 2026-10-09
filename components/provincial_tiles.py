"""components/provincial_tiles.py - one stat tile per province (Punjab / KPK / Federal)."""
import pandas as pd
import streamlit as st
from config.settings import PROVINCE_BOARD_MAP


def render_province_tiles(df: pd.DataFrame, metric: str = "Appeared", year: int = 2026) -> None:
    rows = df[df["Year"] == year]
    tiles = []
    for prov, boards in PROVINCE_BOARD_MAP.items():
        s = rows[rows["Board"].isin(boards)]
        a = int(s["Appeared"].sum())
        if a: tiles.append((prov, a, s["Passed"].sum() / a))
    if not tiles:
        st.info(f"No province-level data available for {year}."); return
    use_pct = metric == "Pass %"
    vals = [t[2] if use_pct else t[1] for t in tiles]; mx = max(vals) or 1.0
    items = []
    for (name, a, pct), v in zip(tiles, vals):
        disp = f"{pct * 100:.1f}%" if use_pct else f"{a:,}"
        icon, sub = ("percent", f"Pass % · {year}") if use_pct else ("groups", f"Appeared · {year}")
        items.append(
            f'<div class="prov-tile"><div class="prov-tile-name"><span class="material-symbols-outlined">{icon}</span>{name}</div>'
            f'<div class="prov-tile-value">{disp}</div><div class="prov-tile-sub">{sub}</div>'
            f'<div class="prov-tile-bar"><div class="prov-tile-fill" style="width:{max(6.0, v / mx * 100):.1f}%"></div></div></div>')
    st.markdown('<div class="prov-grid">' + "".join(items) + "</div>", unsafe_allow_html=True)
