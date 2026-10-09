# BISE Results - Combined Dashboard (9th, 10th, 11th, 12th)

Template: the 12th class dashboard (theme, topbar, sidebar, KPI cards, Overview layout).
(change with the Year / Class pills). Each page ends with a **Compare All 4 Classes** section.

Run: `pip install -r requirements.txt` then `streamlit run app.py`

## Pages
Overview (map, top boards, province tiles, class comparison, Important Points) · Class Comparison · Board Comparison ·
Gender Analysis · Group Wise · Regular vs Private · Subject Wise · District Wise · Grade Distribution · Data Table ·
**Board Report Card** · **Province Comparison** · **Subject Difficulty**

## Data (data/processed/*.csv, built by `python data/build_combined.py` from data/source/)
overall, gender, category, group, subject, district, grade - all with Class, Board, Year.
Pass % = Passed / Appeared everywhere. Board names unified (DGK -> DG Khan, FSD -> Faisalabad, FBISE (Islamabad) -> FBISE).
10th tables were extracted with the 10th dashboard's own loader (`*_10th*.csv` in data/source/).
Split tables (gender/group/category) are kept only where they add up to the board's reported total.

## Not published for every class (see Important Points on the Home page)
11th: no Regular vs Private, no Grade Distribution. 9th/10th: few boards have district data.
11th Mardan and Bannu 2025 are "promoted" results (pass % near 99%).

To update: replace files in data/source/, re-run the build script, bump LAST_UPDATED in config/settings.py.

## Comparison tools
- **Class Comparison** - auto-generated Key Insights, board rank across classes (bump chart), board consistency, rank movement by year, ranking table + CSV.
- **Head to Head** - any two selections (class + year + province), like-for-like toggle, gap by board, totals, province, gender, comparison table + CSV.
- **Cohort Progress** - follows a batch 9th -> 10th -> 11th -> 12th (funnel, carry-over % and pass % change by board). A proxy: counts are not exactly the same students.

## Management pages
- **Board Report Card** - pick a board + year: all 4 classes with pass %, rank among boards, change vs previous year, 3-year trend, best/weakest subject and group, and a one-page **PDF download** (built with reportlab, see `components/report_pdf.py`; numbers in `data/board_report.py`). If a class is not published for the chosen year, its latest earlier year is shown and labelled.
- **Province Comparison** - Punjab vs Khyber Pakhtunkhwa vs Federal (FBISE only): pass % by class, trend, gender gap and Regular vs Private gap, plus a summary table + CSV.
- **Subject Difficulty** - Fail % (100 - Pass %) by subject: hardest subjects per class, and how a subject's difficulty moves 9th -> 12th (heatmap, lines, table). Like-for-like toggle limits it to boards that publish subjects for every class. Subject spelling variants are merged in `data/subject_names.py`.