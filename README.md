# 🎓 BISE Insight - Pakistan Board Results Dashboard (9th-12th, 2024-2026)

An interactive Streamlit dashboard that brings the official **9th, 10th, 11th and 12th class** result gazettes of **15 BISE boards** into one place, so results can be compared across classes, boards, provinces, years, genders, groups, subjects and districts.

> **Live app:** _add your Streamlit Cloud link here_

---

## ✨ Features

- **Overview** - Pakistan map, top boards, province tiles, class comparison and auto-generated *Important Points*
- **Class Comparison** - key insights, board rank across classes (bump chart), consistency, rank movement, ranking table + CSV
- **Board Report Card** - pick a board + year: all 4 classes with pass %, rank, change vs previous year, 3-year trend, best/weakest subject and group, plus a **one-page PDF download**
- **Province Comparison** - Punjab vs Khyber Pakhtunkhwa vs Federal (FBISE): pass % by class, trend, gender gap, Regular vs Private gap
- **Head to Head** - compare any two selections (class + year + province) with a like-for-like toggle
- **Cohort Progress** - follows a batch 9th → 10th → 11th → 12th (funnel, carry-over %, pass % change by board)
- **Board Comparison · Gender Analysis · Group Wise · Regular vs Private**
- **Subject Wise · Subject Difficulty** - fail % by subject, hardest subjects per class, difficulty heatmap 9th → 12th
- **District Wise · Grade Distribution · Data Table** (with CSV export)

Every page opens on **12th class / 2026** by default and can be switched with the Year / Class pills.

---

## 🧰 Tech Stack

Python 3.11+ · [Streamlit](https://streamlit.io) · pandas · Plotly · ReportLab (PDF) · openpyxl

---

## 🚀 Run Locally

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
streamlit run app.py
```

The app opens at `http://localhost:8501`.

---

## 📁 Project Structure

```
├── app.py                    # Entry point (redirects to Overview)
├── pages/                    # One file per dashboard page (1_Overview.py ... 15_Province_Comparison.py)
├── components/               # Reusable UI: topbar, sidebar, KPI cards, filters, insights, PDF report
├── charts/                   # Plotly chart builders (combined_charts.py, extra_charts.py)
├── data/
│   ├── source/               # Raw inputs: class workbooks (.xlsx) + extracted tables (.csv)
│   ├── processed/            # Tidy tables the app reads (overall, gender, category, group, subject, district, grade)
│   ├── build_combined.py     # Builds processed/ from source/
│   ├── loader.py             # The only place the app reads data
│   ├── cohort.py             # Cohort / progression logic
│   ├── board_report.py       # Numbers behind the Board Report Card
│   └── subject_names.py      # Merges spelling variants of the same subject
├── config/settings.py        # App name, classes, years, colours, province-board map, LAST_UPDATED
├── styles/                   # Theme + CSS
├── assets/                   # Pakistan provinces GeoJSON
└── .github/workflows/        # Keep-alive workflow for Streamlit Cloud
```

---

## 🗂️ Data

- Tidy tables in `data/processed/*.csv`, each with **Class, Board, Year** plus Appeared / Passed (or Count for grades).
- **Pass % = Passed ÷ Appeared** everywhere.
- Board names are unified (DGK → DG Khan, FSD → Faisalabad, FBISE (Islamabad) → FBISE).
- Split tables (gender / group / category) are kept only where they add up to the board's reported total.
- Source: official BISE result gazettes.

### Known limitations
- **11th:** no Regular vs Private and no Grade Distribution published.
- **9th / 10th:** only a few boards publish district data.
- **11th Mardan and Bannu 2025** are "promoted" results (pass % near 99%).
- **Cohort Progress** is a proxy - repeaters, private candidates and board changes mean counts are not exactly the same students.

### Updating the data
1. Replace the files in `data/source/`
2. Run `python data/build_combined.py`
3. Update `LAST_UPDATED` in `config/settings.py`
4. Commit and push - Streamlit Cloud redeploys automatically

---

## ☁️ Deploy on Streamlit Community Cloud

1. Push the repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**
3. Select the repo, branch `main`, main file `app.py`
4. Deploy

**Keep-alive:** `.github/workflows/Keep_alive.yml` visits the app every 6 hours so it does not go to sleep. Set `APP_URL` inside that file to your own app link.

---

## 📄 License & Disclaimer

Add a license of your choice (e.g. MIT). Figures are compiled from official BISE gazettes; please verify against the original gazette before official use.
