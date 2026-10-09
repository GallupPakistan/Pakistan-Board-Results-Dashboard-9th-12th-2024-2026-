"""charts/combined_charts.py - every Plotly chart in the dashboard (9th/12th dashboard look)."""
import json
import re
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from styles.theme import COLORS, BOARD_COLOR_SEQUENCE
from config.settings import CLASS_COLORS, CLASSES, YEARS, PROVINCE_BOARD_MAP
from data.loader import agg

GENDER_COLORS = {"Male": COLORS["accent"], "Female": COLORS["gold"]}
CAT_COLORS = {"Regular": COLORS["accent"], "Private": COLORS["gold"]}
YEAR_COLORS = {"2024": "#8FB8F6", "2025": COLORS["accent"], "2026": COLORS["primary"]}
GRADE_ORDER = ["A+", "A", "B", "C", "D", "E"]
GRADE_COLORS = ["#0B1E4D", "#3B82F6", "#22C55E", "#C9A84C", "#F97316", "#EF4444"]


def _tidy_bar_labels(fig):
    """Bar value labels were hidden whenever they were wider than a narrow grouped bar. Keep them visible, use a smaller
    font, and in crowded grouped charts show whole-number % ("53%") so neighbours do not overlap (hover keeps 1 decimal)."""
    bars = [t for t in fig.data if t.type == "bar"]
    if not bars:
        fig.update_layout(uniformtext_minsize=10, uniformtext_mode="hide")      # donut: hide labels that do not fit a slice
        return
    fig.update_layout(uniformtext_mode=False)
    n = sum(len(t.x if t.orientation == "h" else t.y) for t in bars if (t.x if t.orientation == "h" else t.y) is not None)
    for t in bars:
        t.textfont = dict(size=13 if n <= 8 else 12)      # readable on screen; whole-number % keeps wider charts uncluttered
        if t.orientation != "h" and fig.layout.barmode == "group" and len(bars) > 1 and n > 8 and t.text is not None:
            t.text = [re.sub(r"(\d+\.\d)%", lambda m: f"{float(m.group(1)):.0f}%", x) if isinstance(x, str) else x for x in t.text]


def _on_bars(fig, n, kind="pct", limit=24, ymax=None):
    """Value labels on top of bars, only when there is room (<= limit bars). Otherwise hover shows the value."""
    if n > limit: return fig
    fmt = "%{y:.2s}" if kind == "count" else ("%{y:.0f}%" if n > 8 else "%{y:.1f}%")
    fig.update_traces(texttemplate=fmt, textposition="outside", cliponaxis=False)
    if ymax: fig.update_yaxes(range=[0, ymax])
    return fig


def base(fig, height=400, legend_title=""):
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color=COLORS["text_on_light"],
                      font_size=12, legend_title_text=legend_title, margin=dict(t=10, b=10, l=10, r=10), height=height,
                      bargap=0.3)
    fig.update_xaxes(gridcolor="rgba(20,27,60,0.08)"); fig.update_yaxes(gridcolor="rgba(20,27,60,0.08)")
    _tidy_bar_labels(fig)
    return fig


def empty(msg="No data for this selection", height=300):
    fig = go.Figure()
    fig.add_annotation(text=msg, showarrow=False, font=dict(size=14, color=COLORS["text_on_light_muted"]))
    fig.update_xaxes(visible=False); fig.update_yaxes(visible=False)
    return base(fig, height)


def _pct(s): return s.map(lambda v: f"{v:.1f}%")
def _h(n): return max(340, 30 * n + 80)


def donut(d, names, values, cmap=None, height=380):
    if d.empty: return empty()
    many = len(d) > 6                       # many slices: labels inside only, names live in the legend, distinct colours
    d = d.sort_values(values, ascending=False) if many else d
    fig = px.pie(d, names=names, values=values, hole=0.55, color=names, color_discrete_map=cmap,
                 color_discrete_sequence=BOARD_COLOR_SEQUENCE)
    if many:
        fig.update_traces(textinfo="percent", textposition="inside", insidetextorientation="horizontal", sort=False,
                          marker=dict(line=dict(color="white", width=1.5)), hovertemplate="%{label}<br>%{value:,.0f} (%{percent})<extra></extra>")
    else:
        fig.update_traces(textinfo="label+percent")
    return base(fig, height)


# ===================================================================== overview (one class or all)
def chart_yoy_totals(df):
    d = agg(df, ["Year"]).melt("Year", ["Appeared", "Passed", "Failed"], "Metric", "Count")
    if d.empty: return empty()
    d["Year"] = d["Year"].astype(str)
    fig = px.bar(d, x="Year", y="Count", color="Metric", barmode="group",
                 color_discrete_map={"Appeared": COLORS["accent"], "Passed": COLORS["positive"], "Failed": COLORS["negative"]})
    _on_bars(fig, len(d), "count")
    return base(fig, 380, "")


def chart_province_pass_trend(df):
    d = agg(df, ["Year", "Province"])
    if d.empty: return empty()
    fig = px.line(d, x="Year", y="Pass %", color="Province", markers=True)
    fig.update_traces(line=dict(width=3), marker=dict(size=9)); fig.update_xaxes(dtick=1)
    return base(fig, 380, "Province")


def chart_board_pass_rate(df, year):
    d = agg(df[df["Year"] == year], ["Board"]).sort_values("Pass %")
    if d.empty: return empty()
    fig = px.bar(d, x="Pass %", y="Board", orientation="h", text=_pct(d["Pass %"]), color="Pass %",
                 color_continuous_scale=COLORS["map_scale"])
    fig.update_traces(textposition="outside", cliponaxis=False); fig.update_coloraxes(showscale=False)
    fig.update_xaxes(range=[0, 108], title="Pass %")
    return base(fig, _h(len(d)))


def chart_yoy_change_by_board(df, y_to, y_from):
    a = agg(df[df["Year"] == y_from], ["Board"])[["Board", "Pass %"]].rename(columns={"Pass %": "a"})
    b = agg(df[df["Year"] == y_to], ["Board"])[["Board", "Pass %"]].rename(columns={"Pass %": "b"})
    m = a.merge(b, on="Board")
    if m.empty: return empty(f"No board has data for both {y_from} and {y_to}")
    m["Change"] = m["b"] - m["a"]; m = m.sort_values("Change")
    fig = px.bar(m, x="Change", y="Board", orientation="h", text=m["Change"].map(lambda v: f"{v:+.1f}"),
                 color=m["Change"] >= 0, color_discrete_map={True: COLORS["positive"], False: COLORS["negative"]})
    fig.update_traces(textposition="outside", cliponaxis=False); fig.update_layout(showlegend=False)
    fig.update_xaxes(title=f"Change in Pass % ({y_from} → {y_to}, pts)")
    return base(fig, _h(len(m)))


def chart_trend_lines(df):
    d = agg(df, ["Year", "Board"])
    d = d[d.groupby("Board")["Year"].transform("nunique") >= 2]
    if d.empty: return empty("Needs boards with at least two years of data")
    fig = px.line(d, x="Year", y="Pass %", color="Board", markers=True, color_discrete_sequence=BOARD_COLOR_SEQUENCE)
    fig.update_traces(line=dict(width=2.5), marker=dict(size=7)); fig.update_xaxes(dtick=1)
    return base(fig, 400, "Board")


def chart_appeared_share(df, year):
    d = agg(df[df["Year"] == year], ["Board"])
    return donut(d, "Board", "Appeared")


def chart_gender_pass_rate(g):
    d = agg(g, ["Year", "Gender"]); d["Year"] = d["Year"].astype(str)
    if d.empty: return empty()
    fig = px.bar(d, x="Year", y="Pass %", color="Gender", barmode="group", color_discrete_map=GENDER_COLORS, text=_pct(d["Pass %"]))
    fig.update_traces(textposition="outside", cliponaxis=False); fig.update_yaxes(range=[0, 105])
    return base(fig, 380, "Gender")


def chart_gender_share(g, year):
    return donut(agg(g[g["Year"] == year], ["Gender"]), "Gender", "Appeared", GENDER_COLORS)


def chart_category_pass_rate(c):
    d = agg(c, ["Year", "Category"]); d["Year"] = d["Year"].astype(str)
    if d.empty: return empty()
    fig = px.bar(d, x="Year", y="Pass %", color="Category", barmode="group", color_discrete_map=CAT_COLORS, text=_pct(d["Pass %"]))
    fig.update_traces(textposition="outside", cliponaxis=False); fig.update_yaxes(range=[0, 105])
    return base(fig, 380, "Category")


def chart_category_share(c, year):
    return donut(agg(c[c["Year"] == year], ["Category"]), "Category", "Appeared", CAT_COLORS)


_GEO = Path(__file__).resolve().parent.parent / "assets" / "pakistan_provinces.geojson"
_ALIAS = {"Punjab": "Punjab", "Khyber Pakhtunkhwa": "Khyber Pakhtunkhwa", "Islamabad Capital Territory": "Federal"}


def chart_pakistan_map(df, year):
    if not _GEO.exists(): return empty("Pakistan map data not found", 440)
    geo = json.loads(_GEO.read_text(encoding="utf-8"))
    tot = {}
    for prov, boards in PROVINCE_BOARD_MAP.items():
        s = df[df["Board"].isin(boards)]
        yd = {y: (int(s[s["Year"] == y]["Appeared"].sum()), int(s[s["Year"] == y]["Passed"].sum())) for y in YEARS}
        if any(a for a, _ in yd.values()): tot[prov] = yd
    locs, zs, hov, vals = [], [], [], []
    for f in geo["features"]:
        name = f["properties"]["shapeName"]; prov = _ALIAS.get(name); locs.append(name)
        if prov in tot:
            t = tot[prov]; zs.append(t[year][0]); vals.append(t[year][0])
            lines = "".join(f"<br><span style='opacity:.7'>{y}</span> {a:,} appeared · {p:,} passed · <b>{p / a * 100:.1f}%</b>"
                            for y, (a, p) in t.items() if a)
            hov.append(f"<b>{name}</b>{lines}<extra></extra>")
        else:
            zs.append(0); hov.append(f"<b>{name}</b><br><span style='opacity:.7'>No BISE board data in this dataset</span><extra></extra>")
    vmax = max(vals) if vals else 1
    grey, blues = COLORS["map_no_data_strong"], COLORS["map_scale"]; eps = 0.5 / vmax if vmax else 0.0
    cs = [[0.0, grey], [eps, grey]] + [[eps + (i / max(len(blues) - 1, 1)) * (1 - eps), c] for i, c in enumerate(blues)]
    fig = go.Figure(go.Choroplethmap(geojson=geo, featureidkey="properties.shapeName", locations=locs, z=zs, zmin=0, zmax=vmax,
                                     colorscale=cs, showscale=True, marker_line_color="#FFFFFF", marker_line_width=1.2,
                                     colorbar=dict(title=f"Appeared {year}", thickness=12, len=0.75, tickformat="~s"),
                                     text=hov, hovertemplate="%{text}", name=""))
    fig.update_layout(map=dict(style="carto-positron", center=dict(lat=30.3753, lon=69.3451), zoom=4.3),
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=6, b=6, l=6, r=6), height=460,
                      hoverlabel=dict(bgcolor=COLORS["primary"], font_color="#FFFFFF", bordercolor=COLORS["primary_light"]))
    return fig


def top_movers(df, year, other):
    a = agg(df[df["Year"] == year], ["Board"]).set_index("Board")["Pass %"]
    b = agg(df[df["Year"] == other], ["Board"]).set_index("Board")["Pass %"]
    d = (a - b).dropna()
    return (None, None) if d.empty else ((d.idxmax(), d.max()), (d.idxmin(), d.min()))


# ===================================================================== class comparison (all 4 classes)
def _cls_order(d): return {"Class": [c for c in CLASSES if c in d["Class"].unique()]}


def chart_class_pass_by_year(df):
    d = agg(df, ["Class", "Year"]); d["Year"] = d["Year"].astype(str)
    if d.empty: return empty()
    fig = px.bar(d, x="Class", y="Pass %", color="Year", barmode="group", category_orders=_cls_order(d),
                 text=_pct(d["Pass %"]), color_discrete_map=YEAR_COLORS)
    fig.update_traces(textposition="outside", cliponaxis=False); fig.update_yaxes(range=[0, 108])
    return base(fig, 380, "Year")


def chart_class_appeared(df):
    d = agg(df, ["Class", "Year"]); d["Year"] = d["Year"].astype(str)
    if d.empty: return empty()
    fig = px.bar(d, x="Class", y="Appeared", color="Year", barmode="group", category_orders=_cls_order(d), color_discrete_map=YEAR_COLORS)
    _on_bars(fig, len(d), "count")
    return base(fig, 380, "Year")


def chart_class_share(df, year):
    return donut(agg(df[df["Year"] == year], ["Class"]), "Class", "Appeared", CLASS_COLORS)


def chart_class_trend(df):
    d = agg(df, ["Year", "Class"])
    if d.empty: return empty()
    fig = px.line(d, x="Year", y="Pass %", color="Class", markers=True, color_discrete_map=CLASS_COLORS, category_orders=_cls_order(d))
    fig.update_traces(line=dict(width=3), marker=dict(size=9)); fig.update_xaxes(dtick=1)
    return base(fig, 400, "Class")


def chart_class_yoy(df, year, other):
    ll = df[df["Year"].isin([year, other])]
    a = agg(ll[ll["Year"] == other], ["Class"])[["Class", "Pass %"]].rename(columns={"Pass %": "a"})
    b = agg(ll[ll["Year"] == year], ["Class"])[["Class", "Pass %"]].rename(columns={"Pass %": "b"})
    m = a.merge(b, on="Class")
    if m.empty: return empty(f"No class has data for both {other} and {year}")
    m["Change"] = m["b"] - m["a"]
    fig = px.bar(m, x="Class", y="Change", text=m["Change"].map(lambda v: f"{v:+.1f}"), category_orders=_cls_order(m),
                 color=m["Change"] >= 0, color_discrete_map={True: COLORS["positive"], False: COLORS["negative"]})
    fig.update_traces(textposition="outside", cliponaxis=False); fig.update_layout(showlegend=False)
    fig.update_yaxes(title=f"Change in Pass % ({other} → {year}, pts)")
    return base(fig, 380)


def chart_heatmap(df, year):
    d = agg(df[df["Year"] == year], ["Board", "Class"])
    if d.empty: return empty()
    pv = d.pivot(index="Board", columns="Class", values="Pass %").reindex(columns=[c for c in CLASSES if c in d["Class"].unique()])
    fig = go.Figure(go.Heatmap(z=pv.values, x=pv.columns, y=pv.index, text=pv.round(1).astype(str) + "%", texttemplate="%{text}",
                               colorscale=COLORS["map_scale"], zmin=0, zmax=100, colorbar=dict(title="Pass %"), hoverongaps=False))
    fig.update_yaxes(autorange="reversed")
    return base(fig, _h(len(pv)))


def chart_board_by_class(df, year, boards=None):
    d = agg(df[df["Year"] == year], ["Board", "Class"])
    if boards: d = d[d["Board"].isin(boards)]
    if d.empty: return empty()
    fig = px.bar(d, x="Board", y="Pass %", color="Class", barmode="group", color_discrete_map=CLASS_COLORS, category_orders=_cls_order(d))
    fig.update_yaxes(range=[0, 105]); _on_bars(fig, len(d), ymax=112)      # labels appear when 8 or fewer boards are picked
    return base(fig, 420, "Class")


def chart_class_box(df, year):
    d = agg(df[df["Year"] == year], ["Class", "Board"])
    if d.empty: return empty()
    fig = px.box(d, x="Class", y="Pass %", color="Class", points="all", hover_name="Board",
                 color_discrete_map=CLASS_COLORS, category_orders=_cls_order(d))
    fig.update_layout(showlegend=False)
    return base(fig, 380)


def chart_class_bubble(df, year):
    d = agg(df[df["Year"] == year], ["Class", "Board"])
    if d.empty: return empty()
    fig = px.scatter(d, x="Appeared", y="Pass %", color="Class", size="Appeared", hover_name="Board", size_max=38,
                     color_discrete_map=CLASS_COLORS, category_orders=_cls_order(d))
    return base(fig, 400, "Class")


def chart_province_by_class(df, year):
    d = agg(df[df["Year"] == year], ["Province", "Class"])
    if d.empty: return empty()
    fig = px.bar(d, x="Province", y="Pass %", color="Class", barmode="group", text=_pct(d["Pass %"]),
                 color_discrete_map=CLASS_COLORS, category_orders=_cls_order(d))
    fig.update_traces(textposition="outside", cliponaxis=False); fig.update_yaxes(range=[0, 108])
    return base(fig, 380, "Class")


def chart_spread(df, year):
    """Best vs worst board pass % inside each class."""
    d = agg(df[df["Year"] == year], ["Class", "Board"])
    if d.empty: return empty()
    r = d.groupby("Class")["Pass %"].agg(["min", "max"]).reindex([c for c in CLASSES if c in d["Class"].unique()]).reset_index()
    fig = go.Figure()
    fig.add_bar(x=r["Class"], y=r["max"], name="Best board", marker_color=COLORS["positive"], text=_pct(r["max"]), textposition="outside")
    fig.add_bar(x=r["Class"], y=r["min"], name="Weakest board", marker_color=COLORS["negative"], text=_pct(r["min"]), textposition="outside")
    fig.update_layout(barmode="group"); fig.update_yaxes(range=[0, 108], title="Pass %")
    return base(fig, 380)


# ===================================================================== gender
def chart_gender_by_board(g, year):
    d = agg(g[g["Year"] == year], ["Board", "Gender"])
    if d.empty: return empty()
    fig = px.bar(d, x="Board", y="Pass %", color="Gender", barmode="group", color_discrete_map=GENDER_COLORS)
    fig.update_yaxes(range=[0, 105]); _on_bars(fig, len(d), ymax=112)
    return base(fig, 400, "Gender")


def chart_gender_gap(g, year):
    d = agg(g[g["Year"] == year], ["Board", "Gender"]).pivot(index="Board", columns="Gender", values="Pass %")
    if not {"Male", "Female"} <= set(d.columns): return empty()
    d = d.dropna(); d["Gap"] = d["Female"] - d["Male"]; d = d.sort_values("Gap").reset_index()
    if d.empty: return empty()
    fig = px.bar(d, x="Gap", y="Board", orientation="h", text=d["Gap"].map(lambda v: f"{v:+.1f}"),
                 color=d["Gap"] >= 0, color_discrete_map={True: COLORS["gold"], False: COLORS["accent"]})
    fig.update_traces(textposition="outside", cliponaxis=False); fig.update_layout(showlegend=False)
    fig.update_xaxes(title="Female minus Male pass % (pts)")
    return base(fig, _h(len(d)))


def chart_gender_by_class(g, year):
    d = agg(g[g["Year"] == year], ["Class", "Gender"])
    if d.empty: return empty()
    fig = px.bar(d, x="Class", y="Pass %", color="Gender", barmode="group", category_orders=_cls_order(d),
                 text=_pct(d["Pass %"]), color_discrete_map=GENDER_COLORS)
    fig.update_traces(textposition="outside", cliponaxis=False); fig.update_yaxes(range=[0, 108])
    return base(fig, 380, "Gender")


def chart_gender_gap_by_class(g):
    d = agg(g, ["Class", "Year", "Gender"]).pivot_table(index=["Class", "Year"], columns="Gender", values="Pass %").dropna().reset_index()
    if d.empty or "Male" not in d or "Female" not in d: return empty()
    d["Gap"] = d["Female"] - d["Male"]; d["Year"] = d["Year"].astype(str)
    fig = px.bar(d, x="Class", y="Gap", color="Year", barmode="group", category_orders=_cls_order(d),
                 color_discrete_map=YEAR_COLORS, text=d["Gap"].map(lambda v: f"{v:+.1f}"))
    fig.update_traces(textposition="outside", cliponaxis=False); fig.update_yaxes(title="Female minus Male pass % (pts)")
    return base(fig, 380, "Year")


def chart_gender_share_by_class(g, year):
    d = agg(g[g["Year"] == year], ["Class", "Gender"])
    if d.empty: return empty()
    d["Share"] = d["Appeared"] / d.groupby("Class")["Appeared"].transform("sum") * 100
    fig = px.bar(d, x="Class", y="Share", color="Gender", barmode="stack", category_orders=_cls_order(d),
                 text=_pct(d["Share"]), color_discrete_map=GENDER_COLORS)
    fig.update_yaxes(title="Share of candidates %", range=[0, 100])
    return base(fig, 380, "Gender")


# ===================================================================== group / category
def chart_group_pass(gr, year):
    d = agg(gr[gr["Year"] == year], ["Group"]).sort_values("Pass %")
    if d.empty: return empty()
    fig = px.bar(d, x="Pass %", y="Group", orientation="h", text=_pct(d["Pass %"]), color="Pass %", color_continuous_scale=COLORS["map_scale"])
    fig.update_traces(textposition="outside", cliponaxis=False); fig.update_coloraxes(showscale=False); fig.update_xaxes(range=[0, 108])
    return base(fig, _h(len(d)))


def chart_group_share(gr, year):
    return donut(agg(gr[gr["Year"] == year], ["Group"]), "Group", "Appeared")


def chart_group_by_board(gr, year):
    d = agg(gr[gr["Year"] == year], ["Board", "Group"])
    if d.empty: return empty()
    fig = px.bar(d, x="Board", y="Pass %", color="Group", barmode="group", color_discrete_sequence=BOARD_COLOR_SEQUENCE)
    fig.update_yaxes(range=[0, 105]); _on_bars(fig, len(d), ymax=112)
    return base(fig, 420, "Group")


def chart_stream_by_class(gr, year):
    d = agg(gr[gr["Year"] == year], ["Class", "Stream"])
    if d.empty: return empty()
    fig = px.bar(d, x="Stream", y="Pass %", color="Class", barmode="group", text=_pct(d["Pass %"]),
                 color_discrete_map=CLASS_COLORS, category_orders=_cls_order(d))
    fig.update_traces(textposition="outside", cliponaxis=False); fig.update_yaxes(range=[0, 108])
    return base(fig, 400, "Class")


def chart_stream_share_by_class(gr, year):
    d = agg(gr[gr["Year"] == year], ["Class", "Stream"])
    if d.empty: return empty()
    d["Share"] = d["Appeared"] / d.groupby("Class")["Appeared"].transform("sum") * 100
    fig = px.bar(d, x="Class", y="Share", color="Stream", barmode="stack", text=_pct(d["Share"]), category_orders=_cls_order(d))
    fig.update_yaxes(title="Share of candidates %", range=[0, 100])
    return base(fig, 400, "Stream")


def chart_category_by_board(c, year):
    d = agg(c[c["Year"] == year], ["Board", "Category"])
    if d.empty: return empty()
    fig = px.bar(d, x="Board", y="Pass %", color="Category", barmode="group", color_discrete_map=CAT_COLORS)
    fig.update_yaxes(range=[0, 105]); _on_bars(fig, len(d), ymax=112)
    return base(fig, 400, "Category")


def chart_category_by_class(c, year):
    d = agg(c[c["Year"] == year], ["Class", "Category"])
    if d.empty: return empty()
    fig = px.bar(d, x="Class", y="Pass %", color="Category", barmode="group", category_orders=_cls_order(d),
                 text=_pct(d["Pass %"]), color_discrete_map=CAT_COLORS)
    fig.update_traces(textposition="outside", cliponaxis=False); fig.update_yaxes(range=[0, 108])
    return base(fig, 380, "Category")


def chart_category_share_by_class(c, year):
    d = agg(c[c["Year"] == year], ["Class", "Category"])
    if d.empty: return empty()
    d["Share"] = d["Appeared"] / d.groupby("Class")["Appeared"].transform("sum") * 100
    fig = px.bar(d, x="Class", y="Share", color="Category", barmode="stack", category_orders=_cls_order(d),
                 text=_pct(d["Share"]), color_discrete_map=CAT_COLORS)
    fig.update_yaxes(title="Share of candidates %", range=[0, 100])
    return base(fig, 380, "Category")


# ===================================================================== subject / district / grade
def chart_subject_rank(s, year, n=10, best=True):
    d = agg(s[s["Year"] == year], ["Subject"]); d = d[d["Appeared"] >= 200]
    if d.empty: return empty("No subject has 200+ candidates in this selection")
    d = d.sort_values("Pass %", ascending=not best).head(n).sort_values("Pass %", ascending=best)
    fig = px.bar(d, x="Pass %", y="Subject", orientation="h", text=_pct(d["Pass %"]),
                 color_discrete_sequence=[COLORS["positive"] if best else COLORS["negative"]])
    fig.update_traces(textposition="outside", cliponaxis=False); fig.update_xaxes(range=[0, 108])
    return base(fig, _h(len(d)))


def chart_subject_volume(s, year, n=10):
    d = agg(s[s["Year"] == year], ["Subject"]).sort_values("Appeared", ascending=False).head(n)
    if d.empty: return empty()
    fig = px.bar(d.sort_values("Appeared"), x="Appeared", y="Subject", orientation="h", color="Pass %",
                 color_continuous_scale=COLORS["map_scale"], range_color=[0, 100])
    fig.update_traces(texttemplate="%{x:.2s}", textposition="outside", cliponaxis=False)
    fig.update_xaxes(range=[0, float(d["Appeared"].max()) * 1.18])
    return base(fig, _h(len(d)))


def chart_subject_by_class(s, year, subjects):
    d = agg(s[(s["Year"] == year) & (s["Subject"].isin(subjects))], ["Subject", "Class"])
    if d.empty: return empty()
    fig = px.bar(d, x="Subject", y="Pass %", color="Class", barmode="group", color_discrete_map=CLASS_COLORS, category_orders=_cls_order(d))
    fig.update_yaxes(range=[0, 105]); _on_bars(fig, len(d), ymax=112)
    return base(fig, 420, "Class")


def chart_subject_heat(s, year, subjects):
    d = agg(s[(s["Year"] == year) & (s["Subject"].isin(subjects))], ["Subject", "Class"])
    if d.empty: return empty()
    pv = d.pivot(index="Subject", columns="Class", values="Pass %").reindex(columns=[c for c in CLASSES if c in d["Class"].unique()])
    fig = go.Figure(go.Heatmap(z=pv.values, x=pv.columns, y=pv.index, text=pv.round(1).astype(str) + "%", texttemplate="%{text}",
                               colorscale=COLORS["map_scale"], zmin=0, zmax=100, hoverongaps=False, colorbar=dict(title="Pass %")))
    fig.update_yaxes(autorange="reversed")
    return base(fig, _h(len(pv)))


def chart_district(dist, year, top=20):
    d = agg(dist[dist["Year"] == year], ["District"]).sort_values("Pass %").tail(top)
    if d.empty: return empty()
    fig = px.bar(d, x="Pass %", y="District", orientation="h", text=_pct(d["Pass %"]), color="Pass %", color_continuous_scale=COLORS["map_scale"])
    fig.update_traces(textposition="outside", cliponaxis=False); fig.update_coloraxes(showscale=False); fig.update_xaxes(range=[0, 108])
    return base(fig, _h(len(d)))


def chart_district_by_class(dist, year, board):
    d = agg(dist[(dist["Year"] == year) & (dist["Board"] == board)], ["District", "Class"])
    if d.empty: return empty()
    fig = px.bar(d, x="District", y="Pass %", color="Class", barmode="group", color_discrete_map=CLASS_COLORS, category_orders=_cls_order(d))
    fig.update_yaxes(range=[0, 105]); _on_bars(fig, len(d), ymax=112)
    return base(fig, 400, "Class")


def chart_district_trend(dist, board):
    d = agg(dist[dist["Board"] == board], ["Year", "District"])
    d = d[d.groupby("District")["Year"].transform("nunique") >= 2]
    if d.empty: return empty("Needs districts with at least two years of data")
    fig = px.line(d, x="Year", y="Pass %", color="District", markers=True); fig.update_xaxes(dtick=1)
    return base(fig, 400, "District")


def _grade_share(gd):
    d = gd.groupby("Grade", as_index=False)["Count"].sum()
    d["Grade"] = pd.Categorical(d["Grade"], GRADE_ORDER, ordered=True)
    return d.sort_values("Grade")


def chart_grade_donut(gd, year):
    d = _grade_share(gd[gd["Year"] == year])
    if d.empty: return empty()
    fig = px.pie(d, names="Grade", values="Count", hole=0.55, color="Grade", color_discrete_map=dict(zip(GRADE_ORDER, GRADE_COLORS)))
    fig.update_traces(textinfo="label+percent", sort=False)
    return base(fig, 380)


def chart_grade_by_board(gd, year):
    d = gd[gd["Year"] == year].groupby(["Board", "Grade"], as_index=False)["Count"].sum()
    if d.empty: return empty()
    d["Share"] = d["Count"] / d.groupby("Board")["Count"].transform("sum") * 100
    fig = px.bar(d, x="Board", y="Share", color="Grade", barmode="stack", category_orders={"Grade": GRADE_ORDER},
                 color_discrete_map=dict(zip(GRADE_ORDER, GRADE_COLORS)))
    fig.update_yaxes(title="Share of passed candidates %")
    return base(fig, 420, "Grade")


def chart_grade_by_class(gd, year):
    d = gd[gd["Year"] == year].groupby(["Class", "Grade"], as_index=False)["Count"].sum()
    if d.empty: return empty()
    d["Share"] = d["Count"] / d.groupby("Class")["Count"].transform("sum") * 100
    fig = px.bar(d, x="Class", y="Share", color="Grade", barmode="stack", category_orders={"Grade": GRADE_ORDER, **_cls_order(d)},
                 color_discrete_map=dict(zip(GRADE_ORDER, GRADE_COLORS)), text=_pct(d["Share"]))
    fig.update_yaxes(title="Share of graded candidates %", range=[0, 100])
    return base(fig, 400, "Grade")


def chart_top_grades_by_class(gd, year):
    d = gd[gd["Year"] == year].groupby(["Class", "Grade"], as_index=False)["Count"].sum()
    d["Share"] = d["Count"] / d.groupby("Class")["Count"].transform("sum") * 100
    d = d[d["Grade"].isin(["A+", "A"])]
    if d.empty: return empty()
    fig = px.bar(d, x="Class", y="Share", color="Grade", barmode="group", category_orders=_cls_order(d),
                 text=_pct(d["Share"]), color_discrete_map=dict(zip(GRADE_ORDER, GRADE_COLORS)))
    fig.update_traces(textposition="outside", cliponaxis=False)
    return base(fig, 380, "Grade")


# ===================================================================== advanced comparison: head to head
A_COLOR, B_COLOR = COLORS["accent"], COLORS["gold"]


def _side(la, lb): return {la: A_COLOR, lb: B_COLOR}


def chart_h2h_boards(a, b, la, lb):
    da, db = agg(a, ["Board"]).assign(Side=la), agg(b, ["Board"]).assign(Side=lb)
    d = pd.concat([da, db])
    if d.empty: return empty()
    order = d.groupby("Board")["Pass %"].mean().sort_values(ascending=False).index.tolist()
    fig = px.bar(d, x="Board", y="Pass %", color="Side", barmode="group", color_discrete_map=_side(la, lb),
                 category_orders={"Board": order, "Side": [la, lb]})
    fig.update_yaxes(range=[0, 105]); _on_bars(fig, len(d), ymax=112)
    return base(fig, 420, "")


def chart_h2h_gap(a, b, la, lb):
    m = agg(a, ["Board"])[["Board", "Pass %"]].merge(agg(b, ["Board"])[["Board", "Pass %"]], on="Board", suffixes=("_a", "_b"))
    if m.empty: return empty("No board is common to both selections")
    m["Gap"] = m["Pass %_a"] - m["Pass %_b"]; m = m.sort_values("Gap")
    fig = px.bar(m, x="Gap", y="Board", orientation="h", text=m["Gap"].map(lambda v: f"{v:+.1f}"),
                 color=m["Gap"] >= 0, color_discrete_map={True: A_COLOR, False: B_COLOR})
    fig.update_traces(textposition="outside", cliponaxis=False); fig.update_layout(showlegend=False)
    fig.update_xaxes(title=f"Pass % difference  ({la} minus {lb}, pts)")
    return base(fig, _h(len(m)))


def chart_h2h_totals(a, b, la, lb):
    rows = []
    for side, d in ((la, a), (lb, b)):
        t = agg(d, ["Class"])[["Appeared", "Passed", "Failed"]].sum()
        rows += [(side, k, float(t[k])) for k in ("Appeared", "Passed", "Failed")]
    d = pd.DataFrame(rows, columns=["Side", "Metric", "Count"])
    fig = px.bar(d, x="Metric", y="Count", color="Side", barmode="group", color_discrete_map=_side(la, lb),
                 category_orders={"Side": [la, lb]})
    _on_bars(fig, len(d), "count")
    return base(fig, 380, "")


def chart_h2h_province(a, b, la, lb):
    d = pd.concat([agg(a, ["Province"]).assign(Side=la), agg(b, ["Province"]).assign(Side=lb)])
    if d.empty: return empty()
    fig = px.bar(d, x="Province", y="Pass %", color="Side", barmode="group", text=_pct(d["Pass %"]),
                 color_discrete_map=_side(la, lb), category_orders={"Side": [la, lb]})
    fig.update_traces(textposition="outside", cliponaxis=False); fig.update_yaxes(range=[0, 108])
    return base(fig, 380, "")


def chart_h2h_gender(ga, gb, la, lb):
    d = pd.concat([agg(ga, ["Gender"]).assign(Side=la), agg(gb, ["Gender"]).assign(Side=lb)])
    if d.empty: return empty("Gender data is not published for one of the selections")
    fig = px.bar(d, x="Gender", y="Pass %", color="Side", barmode="group", text=_pct(d["Pass %"]),
                 color_discrete_map=_side(la, lb), category_orders={"Side": [la, lb]})
    fig.update_traces(textposition="outside", cliponaxis=False); fig.update_yaxes(range=[0, 108])
    return base(fig, 380, "")


# ===================================================================== advanced comparison: ranks
def _ranked(df, year):
    d = agg(df[df["Year"] == year], ["Board", "Class"])
    d["Rank"] = d.groupby("Class")["Pass %"].rank(ascending=False, method="min")
    return d


def rank_table(df, year):
    d = _ranked(df, year)
    pv = d.pivot(index="Board", columns="Class", values="Rank").reindex(columns=[c for c in CLASSES if c in d["Class"].unique()])
    pv["Avg rank"] = pv.mean(axis=1).round(1)
    pv["Rank spread"] = (pv.drop(columns="Avg rank").max(axis=1) - pv.drop(columns="Avg rank").min(axis=1))
    return pv.sort_values("Avg rank").reset_index()


def chart_rank_bump_classes(df, year):
    d = _ranked(df, year)
    d = d[d.groupby("Board")["Class"].transform("nunique") >= 2]
    if d.empty: return empty()
    fig = px.line(d, x="Class", y="Rank", color="Board", markers=True, category_orders=_cls_order(d),
                  color_discrete_sequence=BOARD_COLOR_SEQUENCE)
    fig.update_traces(line=dict(width=2.5), marker=dict(size=8)); fig.update_yaxes(autorange="reversed", title="Rank (1 = best pass %)", dtick=1)
    return base(fig, 460, "Board")


def chart_rank_bump_years(df, cls):
    d = agg(df[df["Class"] == cls], ["Board", "Year"])
    d["Rank"] = d.groupby("Year")["Pass %"].rank(ascending=False, method="min")
    d = d[d.groupby("Board")["Year"].transform("nunique") >= 2]
    if d.empty: return empty("Needs boards with at least two years of data")
    fig = px.line(d, x="Year", y="Rank", color="Board", markers=True, color_discrete_sequence=BOARD_COLOR_SEQUENCE)
    fig.update_traces(line=dict(width=2.5), marker=dict(size=8)); fig.update_xaxes(dtick=1)
    fig.update_yaxes(autorange="reversed", title="Rank (1 = best pass %)", dtick=1)
    return base(fig, 460, "Board")


def chart_rank_consistency(rt):
    d = rt.dropna(subset=["Avg rank"]).sort_values("Avg rank", ascending=False)
    if d.empty: return empty()
    fig = px.bar(d, x="Avg rank", y="Board", orientation="h", text=d["Avg rank"].map(lambda v: f"{v:.1f}"),
                 color="Rank spread", color_continuous_scale=COLORS["map_scale"])
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_xaxes(title="Average rank across classes (lower = better)", autorange="reversed")
    return base(fig, _h(len(d)))


# ===================================================================== advanced comparison: cohort progression
def chart_cohort_funnel(f):
    """f: DataFrame Step, Appeared, Passed."""
    if f.empty: return empty()
    fig = go.Figure()
    fig.add_bar(x=f["Step"], y=f["Appeared"], name="Appeared", marker_color=COLORS["accent"],
                text=f["Appeared"].map(format_k), textposition="outside")
    fig.add_bar(x=f["Step"], y=f["Passed"], name="Passed", marker_color=COLORS["positive"],
                text=f["Passed"].map(format_k), textposition="outside")
    fig.update_layout(barmode="group"); fig.update_traces(cliponaxis=False)
    return base(fig, 400, "")


def format_k(v):
    return f"{v / 1e6:.2f}M" if v >= 1e6 else f"{v / 1e3:.0f}K"


def chart_progression_by_board(t, la, lb):
    if t.empty: return empty()
    t = t.sort_values("Progression %")
    fig = px.bar(t, x="Progression %", y="Board", orientation="h", text=t["Progression %"].map(lambda v: f"{v:.0f}%"),
                 color="Progression %", color_continuous_scale=COLORS["map_scale"])
    fig.update_traces(textposition="outside", cliponaxis=False); fig.update_coloraxes(showscale=False)
    fig.add_vline(x=100, line_dash="dot", line_color=COLORS["text_on_light_muted"])
    fig.update_xaxes(title=f"{lb} appeared as % of {la} appeared")
    return base(fig, _h(len(t)))


def chart_cohort_scatter(t, la, lb):
    if t.empty: return empty()
    t = t.copy()
    t["Change"] = t["Pass % after"] - t["Pass % before"]
    # label only the boards that stand out (biggest moves + biggest boards); every board stays in the hover
    show = (set(t.nsmallest(2, "Change")["Board"]) | set(t.nlargest(2, "Change")["Board"]) | set(t.nlargest(2, "Appeared before")["Board"]))
    t["Label"] = t["Board"].where(t["Board"].isin(show), "")
    fig = px.scatter(t, x="Pass % before", y="Pass % after", size="Appeared before", hover_name="Board", text="Label", size_max=18,
                     color_discrete_sequence=[COLORS["accent"]],
                     hover_data={"Label": False, "Pass % before": ":.1f", "Pass % after": ":.1f", "Appeared before": ":,.0f"})
    both = pd.concat([t["Pass % before"], t["Pass % after"]])
    lo = max(0, int((both.min() - 8) // 10 * 10)); hi = min(105, int(both.max() + 8))
    fig.add_shape(type="line", x0=lo, y0=lo, x1=hi, y1=hi, line=dict(dash="dot", color=COLORS["text_on_light_muted"]))
    fig.update_traces(textposition="top center", textfont=dict(size=11), cliponaxis=False,
                      marker=dict(opacity=0.6, line=dict(width=1, color="white")))
    fig.update_xaxes(title=f"{la} pass %", range=[lo, hi]); fig.update_yaxes(title=f"{lb} pass %", range=[lo, hi])
    return base(fig, 420)