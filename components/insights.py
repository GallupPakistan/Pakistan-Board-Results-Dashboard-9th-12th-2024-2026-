"""components/insights.py - plain-language findings generated from the data (never hard-coded)."""
import pandas as pd
from config.settings import CLASSES
from data.loader import agg, like_for_like


def build_insights(full: pd.DataFrame, year: int, other, gender: pd.DataFrame) -> list[str]:
    out = []
    cur = agg(full[full["Year"] == year], ["Class"])
    if len(cur) >= 2:
        b, w = cur.sort_values("Pass %").iloc[-1], cur.sort_values("Pass %").iloc[0]
        out.append(f"**{b['Class']}** has the highest pass rate in {year} ({b['Pass %']:.1f}%), **{w['Class']}** the lowest ({w['Pass %']:.1f}%) - a gap of {b['Pass %'] - w['Pass %']:.1f} points.")
    if other:
        moves = []
        for c in CLASSES:
            ll = like_for_like(full[full["Class"] == c], year, other)
            if len(ll):
                a = ll[ll["Year"] == year]; p = ll[ll["Year"] == other]
                moves.append((c, a["Passed"].sum() / a["Appeared"].sum() * 100 - p["Passed"].sum() / p["Appeared"].sum() * 100))
        if moves:
            top = max(moves, key=lambda x: abs(x[1]))
            lst = ", ".join(f"{c} {v:+.1f}" for c, v in moves)
            out.append(f"Versus {other} (same boards), pass rate changed by: {lst} pts. **{top[0]}** moved the most.")
    d = agg(full[full["Year"] == year], ["Board", "Class"])
    d["Rank"] = d.groupby("Class")["Pass %"].rank(ascending=False, method="min")
    g = d.groupby("Board")["Rank"].agg(["mean", "std", "count"]); g = g[g["count"] >= 2]
    if len(g):
        out.append(f"**{g['mean'].idxmin()}** ranks best on average across classes in {year} (average rank {g['mean'].min():.1f}).")
        gg = g.dropna(subset=["std"])
        if len(gg): out.append(f"**{gg['std'].idxmax()}** is the least consistent board across classes (ranks swing the most), **{gg['std'].idxmin()}** the most consistent.")
    s = d.groupby("Class")["Pass %"].agg(["min", "max"]); s["gap"] = s["max"] - s["min"]
    if len(s): out.append(f"Boards differ most in **{s['gap'].idxmax()}** ({s['gap'].max():.0f} points between best and weakest board).")
    gy = gender[gender["Year"] == year]
    if not gy.empty:
        p = agg(gy, ["Class", "Gender"]).pivot(index="Class", columns="Gender", values="Pass %").dropna()
        if {"Male", "Female"} <= set(p.columns) and len(p):
            gap = (p["Female"] - p["Male"]); c = gap.abs().idxmax()
            out.append(f"Largest gender gap in {year}: **{c}** ({'female' if gap[c] >= 0 else 'male'} students ahead by {abs(gap[c]):.1f} pts).")
    return out
