"""
data/build_combined.py - builds the unified tables in data/processed/ from data/source/.
Run:  python data/build_combined.py

Every table has Class (9th/10th/11th/12th), Board, Year plus Appeared/Passed (or Count for grades).
Pass % is always recomputed as Passed / Appeared in data/loader.py.

Sources in data/source/:
  * 4 class workbooks (9th, 10th, 11th, 12th) - the originals
  * *_9th.csv / *_12th.csv  - tidy tables exported from the 9th and 12th dashboards
  * *_10th*.csv             - extracted from the 10th dashboard's own loader (data_loader.py)
  * *_11th*.csv             - read from the 11th workbook's "Combined ..." sheets
"""
import re
from pathlib import Path
import pandas as pd

S = Path(__file__).resolve().parent / "source"
O = Path(__file__).resolve().parent / "processed"
O.mkdir(exist_ok=True)

BOARD_MAP = {
    "DGK": "DG Khan", "D.G. Khan": "DG Khan", "FSD": "Faisalabad", "FBISE (Islamabad)": "FBISE",
    "Pes": "Peshawar", "Ban": "Bannu", "Abb": "Abbottabad", "Sar": "Sargodha", "Mar": "Mardan",
    "Koh": "Kohat", "SWL": "Sahiwal", "RWP": "Rawalpindi", "LHR": "Lahore", "BWP": "Bahawalpur",
    "GRW": "Gujranwala",
}
def board(x):
    x = str(x).strip()
    return BOARD_MAP.get(x, x)

def to_year(v):
    try:
        y = int(float(v)); return y if 2020 <= y <= 2030 else None
    except (TypeError, ValueError):
        return None

def num(df, cols):
    for c in cols: df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.dropna(subset=cols)

def tidy(df, cls, cols, extra=()):
    df = df.copy(); df["Board"] = df["Board"].map(board); df["Year"] = df["Year"].map(to_year)
    df = df.dropna(subset=["Year"]); df["Year"] = df["Year"].astype(int); df["Class"] = cls
    df = num(df, [c for c in cols if c in df.columns])
    return df[["Class", "Board", "Year", *extra, *cols]]

def sheet_tab(path, sheet, hdr):
    raw = pd.read_excel(path, sheet_name=sheet, header=None)
    d = raw.iloc[hdr + 1:].copy(); d.columns = raw.iloc[hdr].tolist(); return d

AP = ["Appeared", "Passed"]

# ------------------------------------------------------------------ overall
rows = []
d = pd.read_excel(S / "BISE_9th_MASTER_2025-2026.xlsx", sheet_name="Overall Summary")
rows.append(tidy(d, "9th", AP))
rows.append(tidy(pd.read_csv(S / "totals_10th.csv"), "10th", AP))
d11 = sheet_tab(S / "11th_Class_Boards_Results_Combined.xlsx", "Combined Overview", 2)
d11 = d11[d11["Board"].notna()]
rows.append(tidy(d11.rename(columns={"Total Appeared": "Appeared", "Total Passed": "Passed"}), "11th", AP))
rows.append(tidy(pd.read_csv(S / "overall_12th.csv"), "12th", AP))
overall = pd.concat(rows).drop_duplicates(["Class", "Board", "Year"]).sort_values(["Class", "Board", "Year"])
overall.to_csv(O / "overall.csv", index=False)
TOT = overall.set_index(["Class", "Board", "Year"])["Appeared"]

def reconcile(df, keys=("Class", "Board", "Year")):
    """Keep a split table only when it adds up to the board's reported total
    (x1 -> keep, x2 -> double counted so halve, otherwise drop that board-year)."""
    out = []
    for k, g in df.groupby(list(keys)):
        t = TOT.get(k)
        if t is None or t == 0: continue
        r = g["Appeared"].sum() / t
        if 0.9 <= r <= 1.1: out.append(g)
        elif 1.9 <= r <= 2.1:
            g = g.copy(); g[AP] = g[AP] / 2; out.append(g)
    return pd.concat(out) if out else df.iloc[0:0]

def agg(df, keys):
    return df.groupby(keys, as_index=False)[[c for c in df.columns if c in AP + ["Count"]]].sum()

# ------------------------------------------------------------------ gender / category / group (10th raw)
g10 = pd.read_csv(S / "gendertype_10th_raw.csv").rename(columns={"Candidate Type": "Type"})
g10["Board"] = g10["Board"].map(board)
g10 = num(g10, AP)
g10["Class"] = "10th"

# gender
gender = [tidy(pd.read_csv(S / "gender_9th.csv"), "9th", AP, ["Gender"]),
          tidy(pd.read_csv(S / "gender_12th.csv"), "12th", AP, ["Gender"])]
x = g10[g10["Type"].isin(["Regular", "Private", "All"])]
# rows with Group 'All' (or per-group rows when no 'All') - pick one consistent slice per board-year
gs = []
for k, g in x.groupby(["Class", "Board", "Year"]):
    for sel in (g[g["Group"] == "All"], g):
        s = sel.groupby("Gender", as_index=False)[AP].sum(); s[["Class", "Board", "Year"]] = k
        s = s[["Class", "Board", "Year", "Gender"] + AP]
        if not s.empty and 0.9 <= s["Appeared"].sum() / TOT.get(k, 1e18) <= 1.1: gs.append(s); break
        if not s.empty and 1.9 <= s["Appeared"].sum() / TOT.get(k, 1e18) <= 2.1:
            s[AP] = s[AP] / 2; gs.append(s); break
if gs: gender.append(pd.concat(gs))
for sx in ("Male", "Female"):
    t = d11.rename(columns={f"{sx} Appeared": "Appeared", f"{sx} Passed": "Passed"}).copy()
    t["Gender"] = sx; gender.append(tidy(t, "11th", AP, ["Gender"]))
gender = pd.concat(gender); gender = gender[gender["Gender"].isin(["Male", "Female"])]
gender = agg(gender, ["Class", "Board", "Year", "Gender"]); gender.to_csv(O / "gender.csv", index=False)

# category (Regular / Private)
cat = [tidy(pd.read_csv(S / "category_9th.csv"), "9th", AP, ["Category"]),
       tidy(pd.read_csv(S / "category_12th.csv"), "12th", AP, ["Category"])]
c10 = agg(g10[g10["Type"].isin(["Regular", "Private"])].rename(columns={"Type": "Category"}), ["Class", "Board", "Year", "Category"])
keep = []
for k, g in c10.groupby(["Class", "Board", "Year"]):
    r = g["Appeared"].sum() / TOT.get(k, 1e18)
    if 0.9 <= r <= 1.1: keep.append(g)
    elif 1.9 <= r <= 2.1: g = g.copy(); g[AP] = g[AP] / 2; keep.append(g)
if keep: cat.append(pd.concat(keep))
category = agg(pd.concat(cat), ["Class", "Board", "Year", "Category"]); category.to_csv(O / "category.csv", index=False)

# group
STREAM = {"Science": "Science", "Pre-Medical": "Science", "Pre-Engineering": "Science", "General Science": "Science",
          "Humanities": "Humanities", "Commerce": "Commerce", "Home Economics": "Other", "Other": "Other"}
def canon_group(t):
    t = str(t).lower()
    t = re.sub(r"\((regular|private)\)", "", t).strip()
    if "pre-med" in t: return "Pre-Medical"
    if "pre-eng" in t: return "Pre-Engineering"
    if "commerce" in t: return "Commerce"
    if "home" in t: return "Home Economics"
    if "islamic" in t: return "Other"
    if "humanit" in t or "arts" in t: return "Humanities"
    if "general" in t or "computer" in t: return "General Science"
    if t.strip() == "science": return "Science"
    return "Other"
grp = [tidy(pd.read_csv(S / "group_9th.csv"), "9th", AP, ["Group"]),
       tidy(pd.read_csv(S / "group_12th.csv"), "12th", AP, ["Group"])]
g = g10[(g10["Group"] != "All")].copy(); g["Group"] = g["Group"].map(canon_group)
g = agg(g, ["Class", "Board", "Year", "Group"])
grp.append(reconcile(g))
r11 = pd.read_csv(S / "group_11th_raw.csv")
r11 = r11[~r11["Category (Gender/Type)"].astype(str).str.lower().isin(["total", "grand total"])]
r11["Group"] = r11["Group"].map(canon_group)
g11 = agg(tidy(r11, "11th", AP, ["Group"]), ["Class", "Board", "Year", "Group"])
grp.append(reconcile(g11))
group = agg(pd.concat(grp), ["Class", "Board", "Year", "Group"])
group["Stream"] = group["Group"].map(STREAM).fillna("Other")
group.to_csv(O / "group.csv", index=False)

# subject
def canon_subject(s):
    s = str(s).strip()
    s = re.sub(r"\(.*?\)", "", s)
    s = re.sub(r"[-\s]+(i{1,3}|iv|1|2)$", "", s, flags=re.I)
    s = s.replace("&", "And").strip().title()
    return {"Islamiyat": "Islamic Education", "Islamic Studies": "Islamic Education", "Pak Studies": "Pakistan Studies",
            "Maths": "Mathematics", "Math": "Mathematics"}.get(s, s)
subj = [tidy(pd.read_csv(S / "subject_9th.csv"), "9th", AP, ["Subject"]),
        tidy(pd.read_csv(S / "subject_12th.csv"), "12th", AP, ["Subject"]),
        tidy(pd.read_csv(S / "subject_11th.csv"), "11th", AP, ["Subject"]),
        tidy(pd.read_csv(S / "subject_10th_raw.csv"), "10th", AP, ["Subject"])]
subject = pd.concat(subj); subject["Subject"] = subject["Subject"].map(canon_subject)
subject = agg(subject, ["Class", "Board", "Year", "Subject"])
subject = subject[subject["Appeared"] > 0]; subject.to_csv(O / "subject.csv", index=False)

# district
dist = [tidy(pd.read_csv(S / "district_9th.csv"), "9th", AP, ["District"]),
        tidy(pd.read_csv(S / "district_12th.csv"), "12th", AP, ["District"]),
        tidy(pd.read_csv(S / "district_11th.csv"), "11th", AP, ["District"]),
        tidy(pd.read_csv(S / "district_10th_raw.csv"), "10th", AP, ["District"])]
district = agg(pd.concat(dist), ["Class", "Board", "Year", "District"])
district = district[district["Appeared"] > 0]; district.to_csv(O / "district.csv", index=False)

# grade
GMAP = {"A1": "A+", "A-1": "A+", "A+": "A+", "A": "A", "B": "B", "C": "C", "D": "D", "E": "E", "E (Pass)": "E"}
gr = [tidy(pd.read_csv(S / "grade_9th.csv"), "9th", ["Count"], ["Grade"]),
      tidy(pd.read_csv(S / "grade_12th.csv"), "12th", ["Count"], ["Grade"]),
      tidy(pd.read_csv(S / "grade_10th_raw.csv"), "10th", ["Count"], ["Grade"])]
grade = pd.concat(gr); grade["Grade"] = grade["Grade"].map(GMAP); grade = grade.dropna(subset=["Grade"])
grade = agg(grade, ["Class", "Board", "Year", "Grade"]); grade.to_csv(O / "grade.csv", index=False)

for n, t in [("overall", overall), ("gender", gender), ("category", category), ("group", group),
             ("subject", subject), ("district", district), ("grade", grade)]:
    print(f"{n:9s} rows={len(t):5d}  " + "  ".join(f"{c}:{t[t.Class==c].Board.nunique()}b" for c in ["9th", "10th", "11th", "12th"]))
