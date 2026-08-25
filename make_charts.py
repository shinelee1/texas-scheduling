#!/usr/bin/env python3
"""
Presentation charts from coded_schools.csv.
  pip install pandas matplotlib
  python make_charts.py coded_schools.csv

Writes:
  fig_district_funnel.png     district-level coverage & findings (share of districts)
  fig_teacher_request.png     teacher-request policy (school level)
  fig_coverage.png            data coverage by variable
  fig_disallowed_reasons.png  reasons schools explicitly disallow changes

All framed descriptively ("of schools/districts where policy was stated"), not as
claims about all Texas schools. District rollup uses the ANY-SCHOOL rule: a district
'knows' a variable if >=1 of its schools stated it (teacher-request policy is
district-wide, so one school's stated policy identifies the district).
"""
import sys, csv, collections
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

PATH = sys.argv[1] if len(sys.argv) > 1 else "coded_schools.csv"
rows = list(csv.DictReader(open(PATH, encoding="utf-8")))
N = len(rows)
META = {"District","School","source_files","model","coded_date","_pathkey","Notes","SIS/Scheduling Software"}
def v(r, c): return (r.get(c, "") or "").strip()
varcols = [c for c in rows[0].keys() if c not in META]

# ============ 1. DISTRICT-LEVEL SHARES (funnel) ============
byd = collections.defaultdict(list)
for r in rows: byd[r["District"]].append(r)
D = len(byd)
def any_school(drows, test): return any(test(r) for r in drows)
def has_data(r): return any(v(r,c) and v(r,c).lower() != "not stated" for c in varcols)

have_data = sum(1 for d in byd.values() if any_school(d, has_data))
tr_known  = sum(1 for d in byd.values() if any_school(d, lambda r: v(r,"Teacher Request Allowed") in ("Y","N")))
tr_no     = sum(1 for d in byd.values() if any_school(d, lambda r: v(r,"Teacher Request Allowed") == "N"))
arena     = sum(1 for d in byd.values() if any_school(d, lambda r: v(r,"Named Arena Selection Process").upper() == "Y"))

print(f"Districts: {D}")
print(f"  any coded data:            {have_data} ({round(100*have_data/D)}%)")
print(f"  teacher-request known:     {tr_known} ({round(100*tr_known/D)}%)")
print(f"  don't allow teacher sel.:  {tr_no} ({round(100*tr_no/D)}% of all; {round(100*tr_no/tr_known)}% of known)")
print(f"  arena/self-select:         {arena} ({round(100*arena/D)}%)")

stages = ["All districts","Any data","Teacher policy\nknown","Don't allow\nteacher selection"]
vals   = [D, have_data, tr_known, tr_no]
fig, ax = plt.subplots(figsize=(8, 4.5))
bars = ax.barh(stages[::-1], vals[::-1], color=["#c62828","#1f3864","#3a6ea5","#2e7d32"][::-1])
ax.bar_label(bars, labels=[f"{x}  ({round(100*x/D)}%)" for x in vals[::-1]], padding=4)
ax.set_title(f"District-level coverage & findings (N = {D} districts)\n'known' = stated at \u22651 school (policy is district-wide)")
ax.set_xlabel("Districts"); ax.spines[['top','right']].set_visible(False)
plt.tight_layout(); plt.savefig("fig_district_funnel.png", dpi=200); plt.close()

# ============ 2. TEACHER-REQUEST (school level) ============
tr = collections.Counter(v(r,"Teacher Request Allowed") or "blank" for r in rows)
order = ["N","Y","Not stated","blank"]
lab = {"N":"No \u2014 not allowed","Y":"Yes \u2014 allowed","Not stated":"Not stated","blank":"No data"}
counts = [tr.get(k,0) for k in order]
fig, ax = plt.subplots(figsize=(7,4))
bars = ax.bar([lab[k] for k in order], counts, color=["#2e7d32","#c62828","#bdbdbd","#e0e0e0"])
ax.bar_label(bars, padding=3)
stated = tr.get("N",0)+tr.get("Y",0)
ax.set_title(f"Can students/parents request a specific teacher? (school level)\n(of {stated} schools where policy stated: {tr.get('N',0)} no, {tr.get('Y',0)} yes)")
ax.set_ylabel("Schools"); ax.spines[['top','right']].set_visible(False)
plt.tight_layout(); plt.savefig("fig_teacher_request.png", dpi=200); plt.close()

# ============ 3. COVERAGE ============
fill = {c: sum(1 for r in rows if v(r,c) and v(r,c).lower()!="not stated") for c in varcols}
top = sorted(fill.items(), key=lambda x: x[1], reverse=True)[:15]
names = [c.replace("Reason - ","").replace("Disallowed Reason - ","(disallow) ")[:42] for c,_ in top]
tv = [x for _,x in top]
fig, ax = plt.subplots(figsize=(8,6))
bars = ax.barh(names[::-1], tv[::-1], color="#1f3864")
ax.bar_label(bars, labels=[f"{x} ({round(100*x/N)}%)" for x in tv[::-1]], padding=3, fontsize=8)
ax.set_title(f"Data coverage by variable (of {N} schools) \u2014 most-populated fields")
ax.set_xlabel("Schools with a value"); ax.spines[['top','right']].set_visible(False)
plt.tight_layout(); plt.savefig("fig_coverage.png", dpi=200); plt.close()

# ============ 4. DISALLOWED REASONS ============
dis = [c for c in rows[0].keys() if c.startswith("Disallowed Reason")]
freq = {c.replace("Disallowed Reason - ",""): sum(1 for r in rows if v(r,c).upper()=="Y") for c in dis}
freq = {k:x for k,x in sorted(freq.items(), key=lambda i:i[1], reverse=True) if x>0}
if freq:
    fig, ax = plt.subplots(figsize=(8,5))
    bars = ax.barh(list(freq.keys())[::-1], list(freq.values())[::-1], color="#c62828")
    ax.bar_label(bars, padding=3, fontsize=8)
    ax.set_title("Reasons schools explicitly DISALLOW a schedule change\n(count of schools stating each)")
    ax.set_xlabel("Schools"); ax.spines[['top','right']].set_visible(False)
    plt.tight_layout(); plt.savefig("fig_disallowed_reasons.png", dpi=200); plt.close()

print("\nWrote: fig_district_funnel.png, fig_teacher_request.png, fig_coverage.png" + (", fig_disallowed_reasons.png" if freq else ""))