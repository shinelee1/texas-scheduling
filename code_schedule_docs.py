#!/usr/bin/env python3
"""
Code Texas scheduling docs (Guide + Call Notes) into one record per high school.
Output columns are exactly the summary-sheet variables (plus a trailing
provenance block: source_files / model / coded_date / _pathkey, which you can delete).

Setup:  pip install anthropic python-docx
        export ANTHROPIC_API_KEY=sk-...
Run:    python code_schedule_docs.py ~/data_collection_docx --limit 3   # test first
        python code_schedule_docs.py ~/data_collection_docx             # full run
        python code_schedule_docs.py ~/data_collection_docx --force     # re-code all
"""
import sys, os, re, json, csv, glob, datetime, collections

MODEL = "claude-sonnet-5"
OUT   = "coded_schools.csv"

# ---- variables, in the sheet's column order ----
VARS = [
 "District","School","Date(s) of Collection",
 "First Day of School (2026-27)","SIS/Scheduling Software",
 "Days before start of school schedules are available (Latest possible day)",
 "Named Arena Selection Process","Preliminary/Unofficial Schedule Before Summer","Teacher Request Allowed",
 "Days after start of school to submit schedule changes (Earliest possible deadline)",
 "Disallowed Reason - To be with a friend","Disallowed Reason - Teacher Changes","Disallowed Reason - Different Lunch period",
 "Disallowed Reason - Elective Change",
 "Disallowed Reason - Dropping an application course after a student has been accepted and enrolled",
 "Disallowed Reason - Dropped Course","Disallowed Reason - Changing between AP and IB",
 "Disallowed Reason - Changing of a privilege period","Disallowed Reason - Improving GPA",
 "AP/Honors/Advanced Level-Down Allowed",
 "Level-Down Deadline/Trigger - End of first 6 weeks","Level-Down Deadline/Trigger - End of first semester",
 "Level-Down Deadline/Trigger - Automatic if Failing After 6 weeks","Level-Down Deadline/Trigger - Teacher Initiated",
 "Reason - Change needed for graduation","Reason - Already completed credit","Reason - Missing/Failed Prerequisites",
 "Reason - Incomplete Schedule, Duplicate Classes, or other Schedule Error","Reason - Balancing Class Loads, or other School Need",
 "Reason - Did not apply / enrolled by mistake","Reason - Add/Drop Athletics/Performing Arts",
 "Reason - Alignment with College Admission Requirements","Reason - Change Needed to Complete an Endorsement",
 "Reason - Needs Placement in Special Education","Reason - 504 plan, or ESL/ELL services",
 "Reason - Adjustment for Medical/Physical Health","Reason - Relevant Credit earned in Summer School",
 "Reason - Student Elected or Assigned to Conflicting Activity by the Administration",
 "Reason - Remedial Coursework Needed for State Assessment","Reason - Previously Failed Class with Teacher",
 "Reason - Student Enrolled in Dual-Credit Class","Reason - Teacher Initiated Changes","Reason - ARD Meeting Recommendation",
 "Reason - Student Did Not Meet Standard on STAAR or EOC Exams",
 # from the call/email-only tab
 "Use of Scheduling Software","Teacher Request Prior to Schedule Build","Possible to Switch Core Classes","Notes",
]
# free-text (short value or "Not stated"); everything else is Y / N / Not stated
TEXT = {
 "Date(s) of Collection","First Day of School (2026-27)","SIS/Scheduling Software",
 "Days before start of school schedules are available (Latest possible day)",
 "Days after start of school to submit schedule changes (Earliest possible deadline)","Notes",
}
YN = [v for v in VARS if v not in TEXT and v not in ("District","School")]
PROV = ["source_files","model","coded_date","_pathkey"]
ALL_COLS = VARS + PROV

def build_prompt(text):
    yn = "\n".join(f'  "{f}": "Y" | "N" | "Not stated"' for f in YN if f != "SIS/Scheduling Software")
    tx = "\n".join(f'  "{f}": "<short value or Not stated>"' for f in VARS if f in TEXT and f != "SIS/Scheduling Software")
    return f"""You are coding a Texas high school's scheduling documents into structured research variables.
Below is the combined text of that school's data-collection guide and/or call notes. Much of the
content is pasted course-change / schedule-change POLICY prose from a student handbook.

Rules:
- Infer the Y/N reason and disallowed-reason fields from the POLICY PROSE, not just from explicit
  checkboxes or filled cells. If the policy affirms a reason is an accepted basis for a schedule
  change, mark that "Reason - ..." field "Y". If the policy states a reason is NOT allowed
  (e.g. "schedules will not be changed to accommodate teacher or lunch preferences"), mark the
  matching "Disallowed Reason - ..." field "Y" and set "Teacher Request Allowed" = "N" accordingly.
- "Not stated" = the documents genuinely do not address it. Use "N" ONLY when the text explicitly
  rules it out. When the prose is vague or ambiguous, choose "Not stated" — do NOT guess or invent
  a distinction the handbook does not make.
- Y/N fields: "Y" if affirmed by policy or text, "N" if explicitly denied/prohibited, else "Not stated".
- Extract District and School from the DOCUMENT CONTENT. If it's a district-wide guide for a single
  high school, School = that high school (or the district name if the school is unnamed).

Return JSON ONLY (no prose, no code fences), exactly these keys:
{{
  "District": "<>", "School": "<>",
{tx}
{yn}
}}

DOCUMENTS:
{text[:18000]}
"""

def code_with_llm(text):
    import anthropic
    client = anthropic.Anthropic()
    for attempt in range(2):
        msg = client.messages.create(model=MODEL, max_tokens=6000,
              messages=[{"role":"user","content":build_prompt(text)}])
        raw = "".join(b.text for b in msg.content if b.type=="text").strip()
        m = re.search(r'\{.*\}', raw, re.DOTALL)   # grab the outermost {...}
        if m:
            try: return json.loads(m.group(0))
            except json.JSONDecodeError: pass
        if attempt==0: continue
        return {"_parse_error": raw[:400]}

def read_docx(path):
    import docx
    try:
        d = docx.Document(path)
        parts = [p.text for p in d.paragraphs]
        for t in d.tables:
            for row in t.rows:
                parts.append(" | ".join(c.text for c in row.cells))
        return "\n".join(x for x in parts if x.strip())
    except Exception as e:
        return f"[READ ERROR: {e}]"

def school_key(path, root):
    rel=os.path.relpath(path,root); parts=rel.split(os.sep)
    district=parts[0].strip(); fname=os.path.splitext(parts[-1])[0]
    if len(parts)>=3: campus=parts[1].strip()
    else:
        c=fname
        for junk in ["Data Collection Guide","Call Notes","Call NOtes","Copy of","Data Collection",
                     district,district.replace(" ISD",""),"  "]:
            c=c.replace(junk,"")
        c=re.sub(r'\(\d+\)','',c).strip(" -")
        campus=c if c else district
    return (district,campus)

def load_existing(force):
    if force or not os.path.exists(OUT): return set(),[]
    rows=list(csv.DictReader(open(OUT,encoding="utf-8")))
    return {r.get("_pathkey","") for r in rows}, rows

def main():
    if len(sys.argv)<2: print(__doc__); return
    root=os.path.expanduser(sys.argv[1]); force="--force" in sys.argv
    limit=int(sys.argv[sys.argv.index("--limit")+1]) if "--limit" in sys.argv else None

    groups=collections.defaultdict(list)
    for p in glob.glob(os.path.join(root,"**","*.docx"),recursive=True):
        if os.path.basename(p).startswith("~$"): continue
        if "call note" in os.path.basename(p).lower(): continue
        groups[school_key(p,root)].append(p)

      

    done, rows = load_existing(force)
    todo=[k for k in sorted(groups) if f"{k[0]}||{k[1]}" not in done]
    if limit: todo=todo[:limit]
    print(f"{len(groups)} schools found | {len(done)} already coded | coding {len(todo)} now\n")

    warnings=[]
    skipped_empty=[]
    for i,key in enumerate(todo,1):
        files=groups[key]; prov_d,prov_c=key
        text="\n\n".join(f"=== {os.path.basename(f)} ===\n{read_docx(f)}" for f in files)

        # skip blank/near-empty guides: strip the template boilerplate, then measure
        boiler = ["texas school scheduling data collection guide","school district","school name",
                  "date of collection","contact info and titles","counselor","peims coordinator",
                  "registrar","other","does the school use software","which software","powerschool",
                  "skyward","ascender","first day of school","not stated"]
        probe = text.lower()
        for b in boiler: probe = probe.replace(b,"")
        probe = re.sub(r'[^a-z0-9]','',probe)
        if len(probe) < 40:
            skipped_empty.append(f"{prov_d} / {prov_c}  ({', '.join(os.path.basename(f) for f in files)})")
            print(f"[{i}/{len(todo)}] {prov_d} / {prov_c}  -- SKIPPED (empty guide)")
            continue

        print(f"[{i}/{len(todo)}] {prov_d} / {prov_c}  ({len(files)} doc(s))")
        rec=code_with_llm(text)
        if rec.get("_parse_error"):
            warnings.append(f"PARSE_ERROR: {prov_d}/{prov_c}"); rec={}
        row={c:"" for c in ALL_COLS}
        for c in VARS: row[c]=rec.get(c,"")
        row["District"]=rec.get("District") or prov_d
        row["School"]=rec.get("School") or prov_c
        cd=str(rec.get("District","")).replace(" ISD","").lower()
        if rec.get("District") and cd and cd not in prov_d.lower() and prov_d.replace(" ISD","").lower() not in cd:
            warnings.append(f"DISTRICT MISMATCH: path={prov_d} vs content={rec.get('District')} ({row['School']})")
        row["_pathkey"]=f"{prov_d}||{prov_c}"
        row["source_files"]=" | ".join(os.path.basename(f) for f in files)
        row["model"]=MODEL; row["coded_date"]=datetime.date.today().isoformat()
        rows.append(row)
        with open(OUT,"w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=ALL_COLS); w.writeheader(); w.writerows(rows)

    if skipped_empty:
        print(f"\n-- SKIPPED as empty (collection gap, {len(skipped_empty)}) --")
        for s in skipped_empty: print("  ",s)
        with open("empty_guides.txt","w") as f: f.write("\n".join(skipped_empty))
        print("  (written to empty_guides.txt)")

    print(f"\nWrote {OUT} ({len(rows)} rows).")
    if warnings:
        print("\n-- WARNINGS to check by hand --")
        for w in warnings: print("  ",w)

if __name__=="__main__": main()
