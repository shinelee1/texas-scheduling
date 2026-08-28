#!/usr/bin/env python3
"""
Coverage cascade / summary stats for the presentation.
  python3 summary_stats.py coded_schools.csv

Prints the funnel: target -> in dataset -> any data -> usable data -> policy stated,
at both campus and district level. Fill TARGET numbers (from target_schools_clean.csv)
and EMAILED/RESPONDED (from the outreach trackers) at the top.
"""
import sys, csv, collections

# ---- fill from target_schools_clean.csv and the outreach trackers ----
TARGET_CAMPUSES  = 353   # traditional HS after excluding 9th-grade/EC/alt
TARGET_DISTRICTS = 234
EMAILED_SHINE    = 82    # campuses (Email = TRUE)
EMAILED_GABE     = 73    # districts (Email Round 2 = Sent)
RESPONDED        = 16    # Gabe-tracked (Shine's not in tracker)
# ---------------------------------------------------------------------

PATH = sys.argv[1] if len(sys.argv) > 1 else "coded_schools.csv"
rows = list(csv.DictReader(open(PATH, encoding="utf-8")))
META = {"District","School","source_files","model","coded_date","_pathkey","Notes",
        "SIS/Scheduling Software","Use of Scheduling Software"}
varcols = [c for c in rows[0].keys() if c not in META]
def v(r,c): return (r.get(c,"") or "").strip()
def filled(r): return sum(1 for c in varcols if v(r,c) and v(r,c).lower()!="not stated")
def ndist(sub): return len(set(r["District"] for r in sub))

N = len(rows); D = ndist(rows)
usable   = [r for r in rows if filled(r) >= 3]      # usable
policy   = [r for r in rows if v(r,"Teacher Request Allowed") in ("Y","N")]

def line(label, camp, dist, denom_c=TARGET_CAMPUSES):
    pc = f"{round(100*camp/denom_c)}%" if denom_c else ""
    print(f"  {label:<34} {camp:>4} campuses  {pc:>5}   {dist:>3} districts")

print("="*66)
print("COVERAGE CASCADE")
print("="*66)
print(f"  {'Target population (traditional HS)':<34} {TARGET_CAMPUSES:>4} campuses         {TARGET_DISTRICTS:>3} districts")
line("In dataset (a row exists)", N, D)
line("With usable data (3+ fields)", len(usable), ndist(usable))
line("Teacher-request policy stated", len(policy), ndist(policy))
print("-"*66)
print("OUTREACH")
print(f"  Emailed:   {EMAILED_SHINE} campuses (Shine) + {EMAILED_GABE} districts (Gabe)")
print(f"  Responded: {RESPONDED} (Gabe-tracked; Shine's not recorded in tracker)")
print("="*66)
print("Note: shares are of the target population; 'known' policy denominators")
print("should be reported as 'of the N schools/districts where policy was stated.'")