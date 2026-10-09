"""data/cohort.py - follows a batch of students through the classes (9th -> 10th -> 11th -> 12th).

Assumption: the batch that sat class N in year Y sits class N+1 in year Y+1. This is a PROXY - private
candidates, repeaters and board changes mean counts are not exactly the same students.
"""
import pandas as pd
from config.settings import CLASSES
from data.loader import agg


def chains(df: pd.DataFrame) -> dict:
    have = set(map(tuple, df[["Class", "Year"]].drop_duplicates().values))
    out = {}
    for i, c in enumerate(CLASSES):
        for y in sorted({y for cc, y in have if cc == c}):
            if i > 0 and (CLASSES[i - 1], y - 1) in have:
                continue                         # not a starting point
            steps, j, yy = [], i, y
            while j < len(CLASSES) and (CLASSES[j], yy) in have:
                steps.append((CLASSES[j], yy)); j += 1; yy += 1
            if len(steps) >= 2:
                out[" → ".join(f"{c2} {y2}" for c2, y2 in steps)] = steps
    return out


def _boards(df, steps):
    sets = [set(df[(df["Class"] == c) & (df["Year"] == y)]["Board"]) for c, y in steps]
    return set.intersection(*sets) if sets else set()


def funnel(df: pd.DataFrame, steps: list) -> pd.DataFrame:
    boards = _boards(df, steps)
    rows = []
    for c, y in steps:
        d = df[(df["Class"] == c) & (df["Year"] == y) & (df["Board"].isin(boards))]
        rows.append({"Step": f"{c} {y}", "Appeared": float(d["Appeared"].sum()), "Passed": float(d["Passed"].sum()),
                     "Boards": len(boards)})
    f = pd.DataFrame(rows)
    f["Pass %"] = f["Passed"] / f["Appeared"] * 100
    return f


def transition(df: pd.DataFrame, a: tuple, b: tuple) -> pd.DataFrame:
    """Per-board: a = (class, year) before, b = (class, year) after."""
    da = agg(df[(df["Class"] == a[0]) & (df["Year"] == a[1])], ["Board"])
    db = agg(df[(df["Class"] == b[0]) & (df["Year"] == b[1])], ["Board"])
    m = da.merge(db, on="Board", suffixes=(" before", " after"))
    if m.empty: return m
    m["Progression %"] = m["Appeared after"] / m["Appeared before"] * 100
    m["Pass % change"] = m["Pass % after"] - m["Pass % before"]
    return m[["Board", "Appeared before", "Passed before", "Pass % before", "Appeared after", "Pass % after",
              "Progression %", "Pass % change"]]
