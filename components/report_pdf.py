"""components/report_pdf.py - builds the one-page A4 PDF for the Board Report Card (reportlab, no extra system deps)."""
from io import BytesIO
from datetime import date
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.graphics.shapes import Drawing, String, Line, Rect
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.widgets.markers import makeMarker
from config.settings import APP_NAME, APP_SUBTITLE, CLASS_COLORS, LAST_UPDATED
from data.board_report import highlights, ordinal

NAVY, GOLD, GREY = colors.HexColor("#0B1E4D"), colors.HexColor("#C9A84C"), colors.HexColor("#6B7280")
GREEN, RED = colors.HexColor("#15803D"), colors.HexColor("#B91C1C")


def _p(txt, size=8, bold=False, color=colors.HexColor("#141B3C"), align=0):
    return Paragraph(str(txt), ParagraphStyle("x", fontName="Helvetica-Bold" if bold else "Helvetica", fontSize=size,
                                              leading=size + 2.5, textColor=color, alignment=align))


def _esc(s): return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _extreme(d, key):
    return f"{_esc(d[key][0])} ({d[key][1]:.1f}%)" if d else "-"


def _trend_chart(rep, width, height=150):
    dr = Drawing(width, height)
    series = [(r["class"], sorted(r["trend"].items())) for r in rep["classes"] if len(r["trend"]) >= 1]
    vals = [v for _, pts in series for _, v in pts]
    if not vals: return dr
    lo = max(0, int((min(vals) - 8) // 10 * 10)); hi = min(100, int((max(vals) + 8) // 10 * 10 + 10))
    lp = LinePlot(); lp.x, lp.y, lp.width, lp.height = 38, 22, width - 110, height - 34
    lp.data = [[(float(y), float(v)) for y, v in pts] for _, pts in series]
    lp.xValueAxis.valueMin, lp.xValueAxis.valueMax = 2023.6, 2026.4
    lp.xValueAxis.valueSteps = [2024, 2025, 2026]; lp.xValueAxis.labelTextFormat = "%d"
    lp.yValueAxis.valueMin, lp.yValueAxis.valueMax = lo, hi
    lp.yValueAxis.valueStep = 10 if hi - lo <= 60 else 20
    lp.yValueAxis.labelTextFormat = "%d%%"; lp.yValueAxis.visibleGrid = True
    lp.yValueAxis.gridStrokeColor = colors.HexColor("#E5E7EB")
    lp.xValueAxis.labels.fontSize = lp.yValueAxis.labels.fontSize = 7
    for i, (cls, pts) in enumerate(series):
        c = colors.HexColor(CLASS_COLORS[cls])
        lp.lines[i].strokeColor, lp.lines[i].strokeWidth = c, 2
        lp.lines[i].symbol = makeMarker("FilledCircle"); lp.lines[i].symbol.fillColor = c
        lp.lines[i].symbol.strokeColor = c; lp.lines[i].symbol.size = 5
        ly = height - 28 - i * 16
        dr.add(Rect(width - 62, ly, 9, 9, fillColor=c, strokeColor=c)); dr.add(String(width - 49, ly + 1, cls, fontSize=8))
    dr.add(lp)
    return dr


def build_pdf(rep: dict) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=14 * mm, rightMargin=14 * mm, topMargin=12 * mm, bottomMargin=12 * mm,
                            title=f"{rep['board']} Board Report Card {rep['year']}", author=APP_NAME)
    W = A4[0] - 28 * mm
    story = []
    head = Table([[_p(f"{_esc(rep['board'])} Board", 20, True, colors.white),
                   _p(f"Board Report Card · {rep['year']}<br/>{APP_NAME} · {APP_SUBTITLE}", 9, False, colors.HexColor('#79AFFF'), 2)]],
                 colWidths=[W * 0.55, W * 0.45])
    head.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), NAVY), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                              ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                              ("TOPPADDING", (0, 0), (-1, -1), 12), ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                              ("LINEBELOW", (0, 0), (-1, -1), 3, GOLD)]))
    story += [head, Spacer(1, 8)]
    cl = rep["classes"]
    if not cl:
        story.append(_p("No results are published for this board.", 10))
        doc.build(story); return buf.getvalue()

    story.append(_p("Key points", 11, True, NAVY)); story.append(Spacer(1, 2))
    for line in highlights(rep):
        story.append(_p("• " + _esc(line), 8.5))
    story.append(Spacer(1, 8))

    story.append(_p("Results by class", 11, True, NAVY)); story.append(Spacer(1, 3))
    rows = [[_p(h, 7.5, True, colors.white, 1) for h in ["Class", "Year", "Appeared", "Passed", "Pass %", "Rank", "vs prev. year", "All-board avg"]]]
    for r in cl:
        d = r["delta"]
        dtxt = "-" if d is None else f"{d:+.1f} pts"
        dcol = GREY if d is None else (GREEN if d >= 0 else RED)
        rows.append([_p(r["class"], 8, True, align=1), _p(r["year"], 8, align=1), _p(f"{r['appeared']:,.0f}", 8, align=1),
                     _p(f"{r['passed']:,.0f}", 8, align=1), _p(f"{r['pct']:.1f}%", 8, True, align=1),
                     _p(f"{ordinal(r['rank'])} of {r['n_boards']}", 8, True, align=1), _p(dtxt, 8, True, dcol, 1),
                     _p(f"{r['avg_pct']:.1f}%", 8, align=1)])
    t = Table(rows, colWidths=[W * f for f in (.09, .08, .15, .15, .11, .15, .14, .13)], repeatRows=1)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), NAVY), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F4F8")]),
                           ("GRID", (0, 0), (-1, -1), .4, colors.HexColor("#DCDFE6")), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                           ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    story += [t, Spacer(1, 8)]

    story.append(_p("Pass % trend (2024-2026)", 11, True, NAVY)); story.append(Spacer(1, 2))
    story += [_trend_chart(rep, W), Spacer(1, 6)]

    story.append(_p("Best and weakest areas", 11, True, NAVY)); story.append(Spacer(1, 3))
    rows = [[_p(h, 7.5, True, colors.white, 1) for h in ["Class", "Best subject", "Weakest subject", "Best group", "Weakest group"]]]
    for r in cl:
        rows.append([_p(r["class"], 8, True, align=1), _p(_extreme(r["subject"], "best"), 7.5), _p(_extreme(r["subject"], "weak"), 7.5),
                     _p(_extreme(r["group"], "best"), 7.5), _p(_extreme(r["group"], "weak"), 7.5)])
    t2 = Table(rows, colWidths=[W * f for f in (.09, .23, .23, .225, .225)], repeatRows=1)
    t2.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), NAVY), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F4F8")]),
                            ("GRID", (0, 0), (-1, -1), .4, colors.HexColor("#DCDFE6")), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                            ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    story += [t2, Spacer(1, 8)]

    notes = ["Pass % = Passed / Appeared. Rank is among the boards that published that class and year (1st = highest pass %).",
             "If a class was not published for the selected year, its latest earlier year is shown (see the Year column).",
             "Best / weakest subject and group need at least 1% of the board's candidates (minimum 100). '-' = not published for this board."]
    notes += [f"{r['class']}: {r['note']}" for r in cl if r["note"]]
    for n in notes: story.append(_p(_esc(n), 7, False, GREY))
    story.append(Spacer(1, 4))
    story.append(_p(f"Source: official BISE result gazettes · data last updated {LAST_UPDATED} · generated {date.today():%d %b %Y}", 7, False, GREY))
    doc.build(story)
    return buf.getvalue()
