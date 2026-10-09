"""components/page_boot.py - shared page skeleton + the class selector used on every page."""
import streamlit as st
from config.settings import APP_NAME, PAGE_ICON, CLASSES, DEFAULT_CLASS, DEFAULT_YEAR
from styles.css import inject_css
from components.sidebar import render_sidebar
from components.topbar import render_topbar
from components.kpi_card import format_compact
from components.filter_bar import render_filter_bar
from components.page_header import render_page_header
from data.loader import prev_year


def boot(page, subtitle, stat_label="Classes", stat_value="4", stat_icon="school"):
    st.set_page_config(page_title=f"{page} - {APP_NAME}", page_icon=PAGE_ICON, layout="wide")
    inject_css()
    render_sidebar()
    render_topbar(active_page=page, subtitle=subtitle, stat_label=stat_label, stat_value=stat_value, stat_icon=stat_icon)


def year_and_class(key, years=(2026, 2025, 2024), allow_all=False, title="Select Year to View Results"):
    """Year pills (default 2026) + class pills (default 12th). Returns (year, class)."""
    year = render_page_header(title, year_options=list(years), year_default=DEFAULT_YEAR, key=f"{key}_year")
    opts = (["All Classes"] if allow_all else []) + CLASSES
    cls = render_filter_bar("Class", options=opts, default=DEFAULT_CLASS, key=f"{key}_class") or DEFAULT_CLASS
    return year, cls


def delta_kpi(cur, prv, fmt=format_compact, pct=False, invert=False):
    """-> (delta_text, positive). pct=True means values are percentages (shown as points)."""
    if prv is None or cur is None: return "", True
    d = cur - prv
    txt = f"{abs(d):.1f} pts" if pct else fmt(abs(d))
    good = d >= 0
    return txt, (not good if invert else good)


def no_data(cls, year, df):
    ys = sorted(df["Year"].unique()) if len(df) else []
    st.info(f"No {cls} class data for {year}." + (f" Available years: {', '.join(map(str, ys))}." if ys else ""))
    st.stop()


def not_published(cls, what):
    st.info(f"{what} is not published for the {cls} class in the source gazettes, so there is nothing to show here.")
