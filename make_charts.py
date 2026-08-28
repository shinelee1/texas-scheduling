#!/usr/bin/env python3
"""
Presentation charts from coded_schools.csv.
  python3 make_charts.py coded_schools.csv     (pandas/matplotlib required)

Writes:
  fig_district_funnel.png     district-level coverage & findings
  fig_teacher_request.png     teacher-request policy (school level)
  fig_coverage.png            data coverage by variable
  fig_disallowed_reasons.png  reasons schools explicitly disallow changes

Notes:
- "Use of Scheduling Software" is excluded from charts: every school that stated it
  said Yes (no variation), so it's a talking-point fact, not a chartable variable.
  The script prints that fact instead.
- District rollup uses the ANY-SCHOOL rule: a district 'knows' a variable if >=1 of
  its schools stated it (teacher-request policy is district-wide).
- Framed descriptively ("of schools/districts where policy was stated").
"""
import sys, csv, collections, textwrap
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

PATH = sys.argv[1] if len(sys.argv) > 1 else "coded_schools.csv"
rows = list(csv.DictReader(open(PATH, encoding="utf-8")))
N = len(rows)
# excluded from coverage/has-data: identifiers, provenance, empty-by-design SIS,
# and the constant "Use of Scheduling Software"
META = {"District","School","source_files","model","coded_date","_pathkey","Notes",
        "SIS/Scheduling Software","Use of Scheduling Software"}
def v(r, c): return (r.get(c, "") or "").strip()
varcols = [c for c in rows[0].keys() if c not in META]

def short(lbl, n=30):
    lbl = lbl.replace("Reason - ", "").replace("Disallowed Reason - ", "")
    return lbl if len(lbl) <= n else lbl[:n-1] + "\u2026"

# ---- software fact (printed, not charted) ----
sw = collections.Counter(v(r,"Use of Scheduling Software") for r in rows)
sw_yes = sw.get("Y",0); sw_no = sw.get("N",0); sw_stated = sw_yes + sw_no
print(f"Scheduling software: of {sw_stated} schools that stated it, {sw_yes} use it, {sw_no} do not "
      f"({'100% Yes, no exceptions' if sw_no==0 and sw_stated else ''})")

# ============ 1. DISTRICT FUNNEL (Any-data stage dropped) ============
byd = collections.defaultdict(list)
for r in rows: byd[r["District"]].append(r)
D = len(byd)
def any_school(drows, test): return any(test(r) for r in drows)
tr_known = sum(1 for d in byd.values() if any_school(d, lambda r: v(r,"Teacher Request Allowed") in ("Y","N")))
tr_no    = sum(1 for d in byd.values() if any_school(d, lambda r: v(r,"Teacher Request Allowed") == "N"))
arena    = sum(1 for d in byd.values() if any_school(d, lambda r: v(r,"Named Arena Selection Process").upper() == "Y"))
print(f"Districts: {D} | teacher-request known: {tr_known} ({round(100*tr_known/D)}%) | "
      f"don't allow: {tr_no} ({round(100*tr_no/D)}% of all, {round(100*tr_no/tr_known) if tr_known else 0}% of known) | arena: {arena}")

stages = ["All districts", "Teacher policy\nknown", "Don't allow\nteacher selection"]
vals   = [D, tr_known, tr_no]
fig, ax = plt.subplots(figsize=(8, 4))
bars = ax.barh(stages[::-1], vals[::-1], color=["#c62828","#3a6ea5","#2e7d32"][::-1])
ax.bar_label(bars, labels=[f"{x}  ({round(100*x/D)}%)" for x in vals[::-1]], padding=5)
ax.set_xlim(0, D*1.18)
ax.set_title("District-level coverage & findings", fontsize=13, pad=10)
ax.set_xlabel(f"Districts (N = {D}; 'known' = stated at \u22651 school)")
ax.spines[['top','right']].set_visible(False)
plt.tight_layout(); plt.savefig("fig_district_funnel.png", dpi=200); plt.close()

# ============ 2. TEACHER-REQUEST (school level) ============
tr = collections.Counter(v(r,"Teacher Request Allowed") or "blank" for r in rows)
order = ["N","Y","Not stated","blank"]
lab = {"N":"No \u2014 not allowed","Y":"Yes \u2014 allowed","Not stated":"Not stated","blank":"No data"}
counts = [tr.get(k,0) for k in order]
fig, ax = plt.subplots(figsize=(7,4.2))
bars = ax.bar([lab[k] for k in order], counts, color=["#2e7d32","#c62828","#bdbdbd","#e0e0e0"])
ax.bar_label(bars, padding=3)
ax.set_ylim(0, max(counts)*1.15)
stated = tr.get("N",0)+tr.get("Y",0)
ax.set_title("Can students/parents request a specific teacher?", fontsize=13, pad=10)
ax.set_xlabel(f"of {stated} schools where policy was stated: {tr.get('N',0)} no, {tr.get('Y',0)} yes")
ax.set_ylabel("Schools"); ax.spines[['top','right']].set_visible(False)
plt.tight_layout(); plt.savefig("fig_teacher_request.png", dpi=200); plt.close()

# ============ 3. COVERAGE ============
fill = {c: sum(1 for r in rows if v(r,c) and v(r,c).lower()!="not stated") for c in varcols}
top = sorted(fill.items(), key=lambda x: x[1], reverse=True)[:14]
names = [c.replace("Reason - ","").replace("Disallowed Reason - ","(disallow) ") for c,_ in top]; tv = [x for _,x in top]
fig, ax = plt.subplots(figsize=(11,6))
bars = ax.barh(names[::-1], tv[::-1], color="#1f3864")
ax.bar_label(bars, labels=[f"{x} ({round(100*x/N)}%)" for x in tv[::-1]], padding=3, fontsize=8)
ax.set_xlim(0, N*1.15)
ax.set_title(f"Data coverage by variable (of {N} schools)", fontsize=13, pad=10)
ax.set_xlabel("Schools with a value"); ax.spines[['top','right']].set_visible(False)
plt.tight_layout(); plt.savefig("fig_coverage.png", dpi=200); plt.close()

# ============ 4. DISALLOWED REASONS ============
dis = [c for c in rows[0].keys() if c.startswith("Disallowed Reason")]
freq = {c.replace("Disallowed Reason - ","").replace("Dropping an application course after a student has been accepted and enrolled","Dropping an accepted application course"): sum(1 for r in rows if v(r,c).upper()=="Y") for c in dis}
freq = {k:x for k,x in sorted(freq.items(), key=lambda i:i[1], reverse=True) if x>0}
if freq:
    fig, ax = plt.subplots(figsize=(10,5))
    bars = ax.barh(list(freq.keys())[::-1], list(freq.values())[::-1], color="#c62828")
    ax.bar_label(bars, padding=3, fontsize=9)
    ax.set_xlim(0, max(freq.values())*1.12)
    ax.set_title("Reasons schools explicitly disallow a change", fontsize=13, pad=10)
    ax.set_xlabel("Schools stating each"); ax.spines[['top','right']].set_visible(False)
    plt.tight_layout(); plt.savefig("fig_disallowed_reasons.png", dpi=200); plt.close()

print("\nWrote: fig_district_funnel.png, fig_teacher_request.png, fig_coverage.png" +
      (", fig_disallowed_reasons.png" if freq else ""))


# ---- 5. ALLOWABLE (accepted) REASONS ----
acc = [c for c in rows[0].keys() if c.startswith("Reason - ")]
afreq = {c.replace("Reason - ",""): sum(1 for r in rows if v(r,c).upper()=="Y") for c in acc}
afreq = {k:x for k,x in sorted(afreq.items(), key=lambda i:i[1], reverse=True) if x>0}
if afreq:
    fig, ax = plt.subplots(figsize=(10,6.5))
    bars = ax.barh(list(afreq.keys())[::-1], list(afreq.values())[::-1], color="#2e7d32")
    ax.bar_label(bars, padding=3, fontsize=9); ax.set_xlim(0, max(afreq.values())*1.12)
    ax.set_title("Reasons schools accept for a schedule change", fontsize=13, pad=10)
    ax.set_xlabel("Schools stating each"); ax.spines[['top','right']].set_visible(False)
    plt.tight_layout(); plt.savefig("fig_allowable_reasons.png", dpi=200); plt.close()
 
print("\nWrote: fig_district_funnel, fig_teacher_request, fig_coverage" +
      (", fig_disallowed_reasons" if freq else "") + (", fig_allowable_reasons" if afreq else "") + " (.png)")
 