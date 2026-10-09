"""data/board_report.py - numbers behind the Board Report Card (pure pandas, no Streamlit UI).

For every class it works out: pass %, rank among boards, change vs the previous year, the 3-year trend,
and the best / weakest subject and group. It only READS the tidy tables through data.loader.load().
"""
import pandas as pd
from config.settings import CLASSES, YEARS
from data.loader import load, agg
from data.subject_names import unify

MIN_SHARE = 0.01     # a subject/group must have at least 1% of the board's candidates ...
MIN_COUNT = 100      # ... and never fewer than 100 candidates, so tiny electives do not decide best/weakest


def ordinal(n: int) -> str:
    n = int(n)
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def board_list() -> list[str]:
    return sorted(load("overall")["Board"].unique())


def _year_used(rows: pd.DataFrame, year: int):
    """Selected year if the board published it, otherwise the latest earlier year, otherwise None."""
    ys = sorted(rows["Year"].unique())
    if year in ys: return year
    earlier = [y for y in ys if y < year]
    return earlier[-1] if earlier else None


def _extremes(df: pd.DataFrame, label: str, floor: float):
    d = df[df["Appeared"] >= floor]
    if len(d) < 2: return None
    d = d.sort_values("Pass %")
    lo, hi = d.iloc[0], d.iloc[-1]
    return {"best": (hi[label], float(hi["Pass %"])), "weak": (lo[label], float(lo["Pass %"])), "n": len(d)}


def class_report(board: str, cls: str, year: int, overall: pd.DataFrame, subject: pd.DataFrame, group: pd.DataFrame):
    o = overall[overall["Class"] == cls]
    mine = o[o["Board"] == board]
    if mine.empty: return None
    y = _year_used(mine, year)
    if y is None: return None
    ranked = agg(o[o["Year"] == y], ["Board"]).sort_values("Pass %", ascending=False).reset_index(drop=True)
    row = ranked[ranked["Board"] == board].iloc[0]
    rank = int(ranked.index[ranked["Board"] == board][0]) + 1
    prev_years = [yy for yy in sorted(mine["Year"].unique()) if yy < y]
    prev = agg(mine[mine["Year"] == prev_years[-1]], ["Board"]).iloc[0] if prev_years else None
    allb = agg(o[o["Year"] == y], ["Class"]).iloc[0]
    trend = {int(r["Year"]): float(r["Pass %"]) for _, r in agg(mine, ["Year"]).iterrows()}

    floor = max(MIN_COUNT, MIN_SHARE * float(row["Appeared"]))
    sj = subject[(subject["Class"] == cls) & (subject["Board"] == board) & (subject["Year"] == y)]
    sj = agg(sj.assign(Subject=sj["Subject"].map(unify)), ["Subject"]) if len(sj) else sj
    gr = group[(group["Class"] == cls) & (group["Board"] == board) & (group["Year"] == y) & (group["Group"] != "Other")]
    gr = agg(gr, ["Group"]) if len(gr) else gr
    note = ""
    if cls == "11th" and board in ("Mardan", "Bannu") and y == 2025:
        note = "Reports promoted results, so pass % is near 99% and not comparable."
    return {
        "class": cls, "year": int(y), "asked_year": int(year), "appeared": float(row["Appeared"]), "passed": float(row["Passed"]),
        "pct": float(row["Pass %"]), "rank": rank, "n_boards": len(ranked), "avg_pct": float(allb["Pass %"]),
        "prev_year": int(prev_years[-1]) if prev_years else None, "prev_pct": float(prev["Pass %"]) if prev is not None else None,
        "delta": float(row["Pass %"] - prev["Pass %"]) if prev is not None else None,
        "trend": trend, "subject": _extremes(sj, "Subject", floor) if len(sj) else None,
        "group": _extremes(gr, "Group", floor) if len(gr) else None, "note": note,
    }


def board_report(board: str, year: int) -> dict:
    overall, subject, group = load("overall"), load("subject"), load("group")
    classes = []
    for c in CLASSES:
        r = class_report(board, c, year, overall, subject, group)
        if r: classes.append(r)
    ranks = [r["rank"] for r in classes]
    return {"board": board, "year": int(year), "classes": classes,
            "avg_rank": (sum(ranks) / len(ranks)) if ranks else None,
            "missing": [c for c in CLASSES if c not in [r["class"] for r in classes]]}


def highlights(rep: dict) -> list[str]:
    """Plain-English lines for management (used on the page and in the PDF)."""
    cl, out = rep["classes"], []
    if not cl: return out
    best = min(cl, key=lambda r: r["rank"]); worst = max(cl, key=lambda r: r["rank"] / r["n_boards"])
    out.append(f"Strongest position: {best['class']} ({best['year']}), ranked {ordinal(best['rank'])} of {best['n_boards']} boards "
               f"with a {best['pct']:.1f}% pass rate.")
    if worst is not best:
        out.append(f"Weakest position: {worst['class']} ({worst['year']}), ranked {ordinal(worst['rank'])} of {worst['n_boards']} boards "
                   f"with a {worst['pct']:.1f}% pass rate.")
    moves = [r for r in cl if r["delta"] is not None]
    if moves:
        up = max(moves, key=lambda r: r["delta"]); dn = min(moves, key=lambda r: r["delta"])
        out.append(f"Biggest improvement: {up['class']} {up['delta']:+.1f} pts vs {up['prev_year']}.")
        if dn["delta"] < 0 and dn is not up:
            out.append(f"Biggest drop: {dn['class']} {dn['delta']:+.1f} pts vs {dn['prev_year']}.")
    above = [r["class"] for r in cl if r["pct"] >= r["avg_pct"]]
    out.append(f"Above the all-board average in {len(above)} of {len(cl)} classes" + (f" ({', '.join(above)})." if above else "."))
    for r in cl:
        s = r["subject"]
        if s and s["weak"][1] < 70:
            out.append(f"Watch {r['class']} {s['weak'][0]}: only {s['weak'][1]:.1f}% passed.")
    if rep["missing"]:
        out.append("Not published for this board: " + ", ".join(rep["missing"]) + ".")
    return out


def _alloc100(values: list) -> list:
    """Split 100 dots across groups in proportion to `values` (largest-remainder rounding, always sums to 100)."""
    tot = float(sum(values))
    if tot <= 0: return [0] * len(values)
    raw = [v / tot * 100 for v in values]; base_ = [int(r) for r in raw]
    for i in sorted(range(len(raw)), key=lambda i: raw[i] - base_[i], reverse=True)[: 100 - sum(base_)]: base_[i] += 1
    return base_


def waffle_groups(board: str, cls: str, year: int, mode: str = "Pass / fail"):
    """'If 100 candidates sat the exam': list of {group, status, n} summing to 100, or None if not published.
    mode: 'Pass / fail' | 'Gender' | 'Regular vs Private'."""
    if mode == "Pass / fail":
        d = agg(load("overall").query("Board == @board and Class == @cls and Year == @year"), ["Board"])
        if d.empty: return None
        keys, rows = ["All"], [("All", float(d["Passed"].iloc[0]), float(d["Appeared"].iloc[0]))]
    else:
        tbl, col = (load("gender"), "Gender") if mode == "Gender" else (load("category"), "Category")
        d = agg(tbl[(tbl["Board"] == board) & (tbl["Class"] == cls) & (tbl["Year"] == year)], [col])
        if d.empty: return None
        rows = [(r[col], float(r["Passed"]), float(r["Appeared"])) for _, r in d.iterrows()]
        order = ["Female", "Male"] if mode == "Gender" else ["Regular", "Private"]
        rows.sort(key=lambda x: order.index(x[0]) if x[0] in order else 9)
    cells, vals = [], []
    for g, passed, appeared in rows:
        cells += [(g, "Passed"), (g, "Failed")]; vals += [passed, appeared - passed]
    return [{"group": g, "status": st, "n": n} for (g, st), n in zip(cells, _alloc100(vals))]