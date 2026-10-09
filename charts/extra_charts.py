"""charts/extra_charts.py - charts for Board Report Card, Subject Difficulty and Province Comparison.
Same look as charts/combined_charts.py (it reuses base/empty/_pct). Nothing here reads files."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from styles.theme import COLORS
from config.settings import CLASS_COLORS, CLASSES
from data.loader import agg, like_for_like
from charts.combined_charts import base, empty, _pct, _h, CAT_COLORS, GENDER_COLORS, _cls_order, format_k

PROV_COLORS = {"Punjab": "#3B82F6", "Khyber Pakhtunkhwa": "#22C55E", "Federal": "#C9A84C"}
PROV_ORDER = ["Punjab", "Khyber Pakhtunkhwa", "Federal"]
FAIL_SCALE = ["#FEF2F2", "#F87171", "#991B1B"]


# ===================================================================== board report card
def chart_report_trend(rep):
    rows = [{"Class": r["class"], "Year": str(y), "Pass %": v} for r in rep["classes"] for y, v in r["trend"].items()]
    if not rows: return empty()
    d = pd.DataFrame(rows)
    fig = px.line(d, x="Year", y="Pass %", color="Class", markers=True, color_discrete_map=CLASS_COLORS,
                  category_orders={"Class": CLASSES, "Year": ["2024", "2025", "2026"]})
    fig.update_traces(line=dict(width=3), marker=dict(size=9))
    return base(fig, 360, "Class")


def chart_report_vs_avg(rep):
    rows = []
    for r in rep["classes"]:
        rows.append({"Class": f"{r['class']} ({r['year']})", "Who": "This board", "Pass %": r["pct"]})
        rows.append({"Class": f"{r['class']} ({r['year']})", "Who": "All boards", "Pass %": r["avg_pct"]})
    if not rows: return empty()
    d = pd.DataFrame(rows)
    fig = px.bar(d, x="Class", y="Pass %", color="Who", barmode="group", text=_pct(d["Pass %"]),
                 color_discrete_map={"This board": COLORS["accent"], "All boards": COLORS["gold"]})
    fig.update_traces(textposition="outside", cliponaxis=False); fig.update_yaxes(range=[0, 108])
    return base(fig, 360, "")


def chart_report_rank(rep):
    d = pd.DataFrame([{"Class": r["class"], "Rank": r["rank"], "Boards": r["n_boards"], "Pos": r["n_boards"] - r["rank"] + 1}
                      for r in rep["classes"]])
    if d.empty: return empty()
    fig = go.Figure()
    fig.add_bar(x=d["Class"], y=d["Boards"], marker_color="rgba(20,27,60,0.08)", hoverinfo="skip", name="All boards")
    fig.add_bar(x=d["Class"], y=d["Pos"], marker_color=[CLASS_COLORS[c] for c in d["Class"]],
                text=[f"#{r}" for r in d["Rank"]], textposition="inside", name="Position",
                customdata=d[["Rank", "Boards"]], hovertemplate="Rank %{customdata[0]} of %{customdata[1]}<extra></extra>")
    fig.update_layout(barmode="overlay", showlegend=False)
    fig.update_yaxes(title="Taller bar = better rank", showticklabels=False)
    return base(fig, 360)


# ===================================================================== subject difficulty
def chart_hardest(s, cls, n=8, min_n=5000):
    """s: one class + year, already aggregated by Subject (needs Appeared, Pass %)."""
    d = s[s["Appeared"] >= min_n].copy()
    if d.empty: return empty(f"No subject has {min_n:,}+ candidates")
    d["Fail %"] = 100 - d["Pass %"]
    d = d.sort_values("Fail %", ascending=False).head(n).sort_values("Fail %")
    fig = px.bar(d, x="Fail %", y="Subject", orientation="h", text=_pct(d["Fail %"]), color_discrete_sequence=[CLASS_COLORS[cls]],
                 hover_data={"Appeared": ":,.0f"})
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_xaxes(range=[0, max(10, d["Fail %"].max() * 1.25)], title="Fail % (higher = harder)")
    return base(fig, _h(len(d)))


def chart_fail_lines(piv):
    """piv: index Subject, columns Class, values Fail %."""
    if piv.empty: return empty("Pick at least one subject")
    d = piv.reset_index().melt("Subject", var_name="Class", value_name="Fail %").dropna()
    fig = px.line(d, x="Class", y="Fail %", color="Subject", markers=True, category_orders={"Class": CLASSES},
                  color_discrete_sequence=px.colors.qualitative.Bold)
    fig.update_traces(line=dict(width=3), marker=dict(size=9))
    fig.update_yaxes(title="Fail % (higher = harder)", rangemode="tozero")
    return base(fig, 420, "Subject")


def chart_fail_heat(piv):
    if piv.empty: return empty("Pick at least one subject")
    fig = go.Figure(go.Heatmap(z=piv.values, x=list(piv.columns), y=list(piv.index), text=piv.round(1).astype(str) + "%",
                               texttemplate="%{text}", colorscale=FAIL_SCALE, zmin=0, zmax=max(40, float(piv.max().max())),
                               hoverongaps=False, colorbar=dict(title="Fail %")))
    fig.update_yaxes(autorange="reversed")
    return base(fig, _h(len(piv)))


# ===================================================================== province comparison
def chart_prov_class(df):
    """df: overall rows for ONE year (any classes) with Province."""
    d = agg(df, ["Province", "Class"])
    if d.empty: return empty()
    fig = px.bar(d, x="Class", y="Pass %", color="Province", barmode="group", text=_pct(d["Pass %"]),
                 color_discrete_map=PROV_COLORS, category_orders={**_cls_order(d), "Province": PROV_ORDER})
    fig.update_traces(textposition="outside", cliponaxis=False); fig.update_yaxes(range=[0, 108])
    return base(fig, 400, "Province")


def chart_prov_trend(df):
    d = agg(df, ["Year", "Province"])
    if d.empty: return empty()
    d["Year"] = d["Year"].astype(str)
    fig = px.line(d, x="Year", y="Pass %", color="Province", markers=True, color_discrete_map=PROV_COLORS,
                  category_orders={"Province": PROV_ORDER})
    fig.update_traces(line=dict(width=3), marker=dict(size=9))
    return base(fig, 400, "Province")


SHORT = {"Khyber Pakhtunkhwa": "KPK"}
SHORT_ORDER = ["Punjab", "KPK", "Federal"]


def _split_by_province(df, split, cmap, order):
    d = agg(df, ["Province", "Class", split])
    if d.empty: return empty()
    d["Prov"] = d["Province"].replace(SHORT)           # short names so the x labels do not collide
    fig = px.bar(d, x="Prov", y="Pass %", color=split, barmode="group", facet_col="Class", text=_pct(d["Pass %"]),
                 color_discrete_map=cmap, category_orders={"Prov": SHORT_ORDER, **_cls_order(d), split: order})
    fig.update_traces(textposition="outside", cliponaxis=False, textfont=dict(size=10)); fig.update_yaxes(range=[0, 115])
    fig.for_each_annotation(lambda a: a.update(text=f"<b>{a.text.split('=')[-1]}</b>", font=dict(size=14, color=COLORS["text_on_light"])))
    fig.update_xaxes(title="")
    fig = base(fig, 440, split)
    fig.update_layout(margin=dict(t=45, b=10, l=10, r=10), bargap=0.15, bargroupgap=0.05, uniformtext_minsize=8)   # room for the class headings
    return fig


def chart_prov_gender(g): return _split_by_province(g, "Gender", GENDER_COLORS, ["Male", "Female"])
def chart_prov_category(c): return _split_by_province(c, "Category", CAT_COLORS, ["Regular", "Private"])


def _gap(df, split, plus, minus):
    d = agg(df, ["Province", "Class", split])
    pv = d.pivot_table(index=["Province", "Class"], columns=split, values="Pass %").reset_index()
    if plus not in pv or minus not in pv: return pd.DataFrame()
    pv["Gap"] = pv[plus] - pv[minus]
    return pv.dropna(subset=["Gap"])


def chart_prov_gap(df, split, plus, minus, title_hint):
    pv = _gap(df, split, plus, minus)
    if pv.empty: return empty()
    fig = px.bar(pv, x="Class", y="Gap", color="Province", barmode="group", text=pv["Gap"].map(lambda v: f"{v:+.1f}"),
                 color_discrete_map=PROV_COLORS, category_orders={**_cls_order(pv), "Province": PROV_ORDER})
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.add_hline(y=0, line_color="rgba(20,27,60,0.4)")
    fig.update_yaxes(title=f"{title_hint} (pts)")
    return base(fig, 380, "Province")


# ===================================================================== new visuals: treemap, dumbbell, quadrant, sankey
def _rgba(hex_, a):
    h = hex_.lstrip("#"); return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{a})"


def chart_treemap(df, year, height=420):
    """Box size = candidates appeared, colour = pass %. Province -> Board. Pass % is written into each label."""
    cur = df[df["Year"] == year]
    d = agg(cur, ["Province", "Board"])
    if d.empty: return empty()
    prov = agg(cur, ["Province"]).set_index("Province")["Pass %"]
    d["Province "] = d["Province"].map(lambda p: f"{p} · {prov[p]:.1f}%")
    d["Board "] = d["Board"] + "<br>" + d["Pass %"].map(lambda v: f"{v:.1f}%")
    fig = px.treemap(d, path=[px.Constant("All boards"), "Province ", "Board "], values="Appeared", color="Pass %",
                     color_continuous_scale=COLORS["map_scale"], range_color=[float(d["Pass %"].min()), float(d["Pass %"].max())])
    fig.update_traces(texttemplate="<b>%{label}</b>", textfont=dict(size=12), root_color="rgba(0,0,0,0)",
                      marker=dict(line=dict(width=2, color="white")),
                      hovertemplate="<b>%{label}</b><br>Candidates: %{value:,.0f}<extra></extra>")
    fig.update_coloraxes(colorbar=dict(title="Pass %", thickness=12, len=0.8))
    return base(fig, height)


def chart_dumbbell(df, y_to, y_from):
    """Two dots per board (previous year vs this year) joined by a line; green = improved, red = declined."""
    ll = like_for_like(df, y_to, y_from)
    a = agg(ll[ll["Year"] == y_from], ["Board"])[["Board", "Pass %"]].rename(columns={"Pass %": "pf"})
    b = agg(ll[ll["Year"] == y_to], ["Board"])[["Board", "Pass %"]].rename(columns={"Pass %": "pt"})
    m = a.merge(b, on="Board")
    if m.empty: return empty(f"No board has data for both {y_from} and {y_to}")
    m = m.sort_values("pt").reset_index(drop=True); m["up"] = m["pt"] >= m["pf"]
    fig = go.Figure()
    for flag, name, col in ((True, "Improved", COLORS["positive"]), (False, "Declined", COLORS["negative"])):
        r = m[m["up"] == flag]
        if r.empty: continue
        xs, ys = [], []
        for _, x in r.iterrows(): xs += [x["pf"], x["pt"], None]; ys += [x["Board"], x["Board"], None]
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(width=5, color=_rgba(col, 0.55)), name=name, hoverinfo="skip"))
    pos_to = ["middle right" if u else "middle left" for u in m["up"]]; pos_from = ["middle left" if u else "middle right" for u in m["up"]]
    fig.add_trace(go.Scatter(x=m["pf"], y=m["Board"], mode="markers+text", name=str(y_from), text=m["pf"].map(lambda v: f"{v:.0f}%"),
                             textposition=pos_from, textfont=dict(size=11, color=COLORS["text_on_light_muted"]), cliponaxis=False,
                             marker=dict(size=12, color=COLORS["gold"], line=dict(width=1, color="white")),
                             hovertemplate="%{y}<br>" + str(y_from) + ": %{x:.1f}%<extra></extra>"))
    fig.add_trace(go.Scatter(x=m["pt"], y=m["Board"], mode="markers+text", name=str(y_to), text=m["pt"].map(lambda v: f"{v:.0f}%"),
                             textposition=pos_to, textfont=dict(size=12), cliponaxis=False,
                             marker=dict(size=13, color=COLORS["accent"], line=dict(width=1, color="white")),
                             hovertemplate="%{y}<br>" + str(y_to) + ": %{x:.1f}%<extra></extra>"))
    lo, hi = min(m["pf"].min(), m["pt"].min()), max(m["pf"].max(), m["pt"].max())
    fig.update_xaxes(range=[max(0, lo - 16), min(112, hi + 16)], title="Pass %", dtick=10)
    fig.update_yaxes(categoryorder="array", categoryarray=list(m["Board"]), title="")
    fig = base(fig, _h(len(m)) + 30, "")
    fig.update_layout(legend=dict(orientation="h", x=0, y=1.07, xanchor="left"), margin=dict(t=40, b=10, l=10, r=10))
    return fig


def chart_quadrant(d, year, other):
    """x = pass % this year, y = change vs previous year. Dashed lines = average pass % and zero change."""
    ll = like_for_like(d, year, other)
    cur = agg(ll[ll["Year"] == year], ["Board"]); old = agg(ll[ll["Year"] == other], ["Board"])[["Board", "Pass %"]]
    m = cur.merge(old, on="Board", suffixes=("", " prev"))
    if len(m) < 2: return empty(f"Needs at least 2 boards with data in both {other} and {year}")
    m["Change"] = m["Pass %"] - m["Pass % prev"]
    c = ll[ll["Year"] == year]; avg = float(c["Passed"].sum() / c["Appeared"].sum() * 100)
    m = m.sort_values("Pass %").reset_index(drop=True); m["pos"] = ["top center" if i % 2 == 0 else "bottom center" for i in range(len(m))]
    quads = {(True, True): ("Above average · improving", COLORS["positive"]), (True, False): ("Above average · falling", COLORS["gold"]),
             (False, True): ("Below average · improving", COLORS["accent"]), (False, False): ("Below average · falling", COLORS["negative"])}
    sizeref = 2.0 * float(m["Appeared"].max()) / (34 ** 2)
    fig = go.Figure()
    for (hi_, up_), (name, col) in quads.items():
        r = m[((m["Pass %"] >= avg) == hi_) & ((m["Change"] >= 0) == up_)]
        if r.empty: continue
        fig.add_trace(go.Scatter(x=r["Pass %"], y=r["Change"], mode="markers+text", name=name, text=r["Board"], textposition=list(r["pos"]),
                                 textfont=dict(size=12), cliponaxis=False,
                                 marker=dict(size=r["Appeared"], sizemode="area", sizeref=sizeref, sizemin=8, color=_rgba(col, 0.7),
                                             line=dict(width=1, color="white")),
                                 customdata=r[["Appeared", "Pass % prev"]],
                                 hovertemplate="<b>%{text}</b><br>Pass %: %{x:.1f}%<br>Change: %{y:+.1f} pts<br>Previous: %{customdata[1]:.1f}%"
                                               "<br>Appeared: %{customdata[0]:,.0f}<extra></extra>"))
    ym = max(5.0, float(m["Change"].abs().max()) * 1.35)
    fig.update_xaxes(range=[float(m["Pass %"].min()) - 5, float(m["Pass %"].max()) + 5], title=f"Pass % in {year}")
    fig.update_yaxes(range=[-ym, ym], title=f"Change vs {other} (points)", zeroline=False)
    fig.add_vline(x=avg, line_dash="dot", line_color=COLORS["text_on_light_muted"])
    fig.add_hline(y=0, line_dash="dot", line_color=COLORS["text_on_light_muted"])
    for (hi_, up_), (name, col) in quads.items():
        fig.add_annotation(xref="paper", yref="paper", x=0.99 if hi_ else 0.01, y=0.98 if up_ else 0.02, text=f"<b>{name}</b>",
                           showarrow=False, xanchor="right" if hi_ else "left", yanchor="top" if up_ else "bottom",
                           font=dict(size=12, color=col))
    fig.add_annotation(xref="x", yref="paper", x=avg, y=1.0, text=f"avg {avg:.1f}%", showarrow=False, yanchor="bottom", font=dict(size=11, color=COLORS["text_on_light_muted"]))
    fig = base(fig, 480)
    fig.update_layout(showlegend=False, margin=dict(t=28, b=10, l=10, r=10))      # base() resets margins; keep room for the 'avg' label
    return fig


def chart_cohort_sankey(f):
    """Flow of candidates through the chain. f: Step ('9th 2025'), Appeared, Passed (same boards in every step).
    Appeared -> Passed / Failed; Passed -> next class appeared; leftovers = 'did not sit next class';
    extra candidates in the next class = 'new / repeat entrants' (private candidates, repeaters, other boards)."""
    if len(f) < 2: return empty("Needs at least 2 steps")
    labels, colors, src, tgt, val, lcol, llab = [], [], [], [], [], [], []

    def node(text, col): labels.append(text); colors.append(col); return len(labels) - 1

    def link(s, t, v, col, lab=""):
        src.append(s); tgt.append(t); val.append(float(v)); lcol.append(col); llab.append(lab)

    n = len(f); GREEN, RED, GREY, GOLD = COLORS["positive"], COLORS["negative"], "#9CA3AF", COLORS["gold"]
    A = [node(f"{r.Step} · {format_k(r.Appeared)}", CLASS_COLORS.get(str(r.Step).split()[0], COLORS["accent"])) for r in f.itertuples()]
    for i, r in enumerate(f.itertuples()):
        P = node(f"Passed {format_k(r.Passed)}", GREEN); F = node(f"Failed {format_k(r.Appeared - r.Passed)}", RED)
        link(A[i], P, r.Passed, _rgba(GREEN, 0.22), "Passed"); link(A[i], F, r.Appeared - r.Passed, _rgba(RED, 0.18), "Failed")
        if i == n - 1: break
        nxt = f["Appeared"].iloc[i + 1]; cont = min(r.Passed, nxt)
        link(P, A[i + 1], cont, _rgba(CLASS_COLORS.get(str(f["Step"].iloc[i + 1]).split()[0], COLORS["accent"]), 0.28), "Passed and sat the next class")
        if r.Passed > nxt:
            D = node(f"Did not sit next class {format_k(r.Passed - nxt)}", GREY)
            link(P, D, r.Passed - nxt, _rgba(GREY, 0.25), "Passed but did not sit the next class")
        elif nxt > r.Passed:
            J = node(f"New / repeat entrants {format_k(nxt - r.Passed)}", GOLD)
            link(A[i], J, 1, "rgba(0,0,0,0)", "")                    # 1-candidate invisible link: only places the node in the right column
            link(J, A[i + 1], nxt - r.Passed, _rgba(GOLD, 0.30), "New or repeat entrants (private, repeaters, other boards)")
    fig = go.Figure(go.Sankey(arrangement="snap", node=dict(label=labels, color=colors, pad=22, thickness=22, line=dict(width=0)),
                              textfont=dict(size=14, color="#0B1E4D"),
                              link=dict(source=src, target=tgt, value=val, color=lcol, label=llab,
                                        hovertemplate="%{label}<br>%{value:,.0f} candidates<extra></extra>")))
    fig = base(fig, 580)
    fig.update_layout(margin=dict(t=10, b=10, l=10, r=40))
    return fig


# ===================================================================== animated ranking race + "100 students" waffle
def chart_rank_race(d):
    """d: overall rows for ONE class (all years). Press Play: boards re-order by pass % year by year."""
    t = agg(d, ["Province", "Board", "Year"])
    if t["Year"].nunique() < 2: return empty("This class needs at least 2 years of results for a ranking race")
    t["Year"] = t["Year"].astype(str); t["Label"] = t["Pass %"].map(lambda v: f"{v:.1f}%")
    t = t.sort_values(["Year", "Pass %"])
    fig = px.bar(t, x="Pass %", y="Board", color="Province", orientation="h", animation_frame="Year", text="Label",
                 color_discrete_map=PROV_COLORS, category_orders={"Province": PROV_ORDER},
                 range_x=[0, 108], hover_data={"Label": False, "Pass %": ":.1f", "Appeared": ":,.0f"})
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_yaxes(categoryorder="total ascending", title="")           # re-sorts the bars in every frame
    fig.update_xaxes(title="Pass %")
    fig = base(fig, _h(t["Board"].nunique()) + 70, "Province")
    if fig.layout.updatemenus:
        a = fig.layout.updatemenus[0].buttons[0].args[1]
        a["frame"]["duration"] = 1600; a["frame"]["redraw"] = True; a["transition"]["duration"] = 900
    fig.update_layout(legend=dict(orientation="h", x=0, y=1.08, xanchor="left"))
    return fig


def chart_waffle(groups, height=300):
    """groups: list of {group, status, n} summing to 100. One square = 1 in 100 candidates."""
    if not groups or sum(g["n"] for g in groups) == 0: return empty("Not published", height)
    fig = go.Figure(); i = 0
    for g in groups:
        if g["n"] <= 0: continue
        idx = range(i, i + g["n"]); i += g["n"]
        base_col = (COLORS["positive"] if g["status"] == "Passed" else COLORS["negative"]) if g["group"] == "All" else \
                   (GENDER_COLORS.get(g["group"]) or CAT_COLORS.get(g["group"]) or COLORS["accent"])
        col = base_col if g["status"] == "Passed" else (_rgba(base_col, 0.28) if g["group"] != "All" else base_col)
        name = g["status"] if g["group"] == "All" else f"{g['group']} {g['status'].lower()}"
        fig.add_trace(go.Scatter(x=[k % 10 for k in idx], y=[k // 10 for k in idx], mode="markers", name=f"{name} ({g['n']})",
                                 marker=dict(symbol="square", size=21, color=col, line=dict(width=1, color="white")),
                                 hovertemplate=f"{name}: {g['n']} in 100<extra></extra>"))
    fig.update_xaxes(visible=False, range=[-0.7, 9.7], fixedrange=True); fig.update_yaxes(visible=False, range=[-0.7, 9.7], fixedrange=True, scaleanchor="x")
    fig = base(fig, height, "")
    fig.update_layout(legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.02, yanchor="top", font=dict(size=12)),
                      margin=dict(t=6, b=6, l=6, r=6))
    return fig