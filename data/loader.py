"""data/loader.py - the ONLY place the dashboard reads data (tidy CSVs in data/processed/)."""
from pathlib import Path
import pandas as pd
import streamlit as st
from config.settings import BOARD_PROVINCE, YEARS

_P = Path(__file__).resolve().parent / "processed"
KINDS = ["overall", "gender", "category", "group", "subject", "district", "grade"]


def _ensure():
    if not (_P / "overall.csv").exists():
        import runpy
        runpy.run_path(str(Path(__file__).resolve().parent / "build_combined.py"))


@st.cache_data(show_spinner="Loading data...")
def load(kind: str) -> pd.DataFrame:
    """kind: overall | gender | category | group | subject | district | grade"""
    _ensure()
    df = pd.read_csv(_P / f"{kind}.csv")
    df["Province"] = df["Board"].map(BOARD_PROVINCE).fillna("Other")
    if "Appeared" in df.columns:
        df["Failed"] = df["Appeared"] - df["Passed"]
        df["Pass %"] = df["Passed"] / df["Appeared"] * 100
    return df


def agg(df: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    """Sum Appeared/Passed over `keys`, then recompute Failed and Pass %."""
    out = df.groupby(keys, as_index=False)[["Appeared", "Passed"]].sum()
    out["Failed"] = out["Appeared"] - out["Passed"]
    out["Pass %"] = out["Passed"] / out["Appeared"] * 100
    return out


def totals(df: pd.DataFrame) -> dict:
    a, p = float(df["Appeared"].sum()), float(df["Passed"].sum())
    return {"appeared": a, "passed": p, "failed": a - p, "pct": (p / a * 100) if a else 0.0,
            "boards": int(df.groupby(["Class", "Board"]).ngroups) if len(df) else 0}


def prev_year(year: int):
    earlier = [y for y in YEARS if y < year]
    return earlier[-1] if earlier else None


def like_for_like(df: pd.DataFrame, y1: int, y2: int) -> pd.DataFrame:
    """Rows of y1 and y2 for (Class, Board) pairs that published BOTH years."""
    a = set(map(tuple, df[df["Year"] == y1][["Class", "Board"]].values))
    b = set(map(tuple, df[df["Year"] == y2][["Class", "Board"]].values))
    keep = a & b
    mask = [(c, bd) in keep for c, bd in zip(df["Class"], df["Board"])]
    return df[pd.Series(mask, index=df.index) & df["Year"].isin([y1, y2])]


def scope(df: pd.DataFrame, cls: str) -> pd.DataFrame:
    return df if cls == "All Classes" else df[df["Class"] == cls]
