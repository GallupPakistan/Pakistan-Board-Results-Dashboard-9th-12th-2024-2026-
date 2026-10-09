"""components/notes.py - the 'Important Points' block shown at the end of the Home page."""
import streamlit as st
from config.settings import CLASSES, LAST_UPDATED
from components.chart_card import chart_card
from data.loader import load, KINDS

LABELS = {"overall": "Pass % / results", "gender": "Gender", "category": "Regular vs Private", "group": "Group wise",
          "subject": "Subject wise", "district": "District wise", "grade": "Grade distribution"}


def render_important_points():
    cov = []
    ov = load("overall")
    for c in CLASSES:
        x = ov[ov["Class"] == c]
        ys = sorted(x["Year"].unique())
        cov.append(f"**{c}:** {x['Board'].nunique()} boards · {ys[0]}-{ys[-1]}")
    rows = []
    for k in KINDS[1:]:
        t = load(k)
        cells = []
        for c in CLASSES:
            n = t[t["Class"] == c]["Board"].nunique()
            cells.append(f"{n} boards" if n else "❌ not published")
        rows.append(f"| {LABELS[k]} | " + " | ".join(cells) + " |")
    table = "| Data | " + " | ".join(CLASSES) + " |\n|---|" + "---|" * len(CLASSES) + "\n" + "\n".join(rows)
    with chart_card("Important Points", f"Please read before using the numbers · Last updated {LAST_UPDATED}"):
        st.markdown(
            "**Defaults:** every page opens on the **12th class** and **2026**. Use the Year and Class pills to change them; "
            "each page also has a *Compare all classes* section.\n\n"
            "**Data coverage (results)**  \n" + " · ".join(cov) + "\n\n"
            "**What each class publishes (number of boards with data)**\n\n" + table + "\n\n"
            "**Comparison tools:** Class Comparison (insights + board rankings), Head to Head (any two selections), Cohort Progress (a batch followed from 9th to 12th, a proxy not exact students).\n\n"
            "**How numbers are calculated**\n"
            "- Pass % = Passed ÷ Appeared everywhere (recomputed from counts, not copied from gazettes).\n"
            "- Totals include only boards that published that class and year; changes vs the previous year use only boards that published both years.\n"
            "- Board names are unified (DGK / D.G. Khan → DG Khan, FSD → Faisalabad, FBISE (Islamabad) → FBISE).\n"
            "- Group wise: 9th/10th use Science / Humanities; 11th/12th use Pre-Medical, Pre-Engineering, etc. For cross-class comparison they are merged into streams (Science, Humanities, Commerce, Other).\n"
            "- Split tables (gender, group, category) are used only where they add up to the board's reported total.\n\n"
            "**Special cases**\n"
            "- 11th Mardan and Bannu 2025 report *promoted* results (not pass/fail), so pass % is near 99%.\n"
            "- 9th has 2025-26 only, 11th has 2024-25 only, so some cross-class charts show fewer classes for 2026 or 2024.\n"
            "- Source: official BISE result gazettes, in the class workbooks in `data/source/`."
        )
