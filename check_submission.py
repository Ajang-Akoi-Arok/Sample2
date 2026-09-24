"""Check the repo has everything the assignment asks for, before submitting.

Run it from the project root:

    python3 check_submission.py

It does not test whether the API works. Start the server and run
screenshots/run_tests.sh for that. This only checks that the files exist and
contain what the rubric asks for, which is the stuff that is easy to forget.
"""

import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))

PASS, FAIL, WARN = "PASS", "FAIL", "WARN"
results = []


def check(name, status, detail=""):
    results.append((name, status, detail))


def read(*parts):
    path = os.path.join(ROOT, *parts)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


# --- Task 1: data parsing ----------------------------------------------------

raw = read("data", "transactions.json")
if raw is None:
    check("Task 1  parsed JSON exists", FAIL, "data/transactions.json is missing")
else:
    try:
        records = json.loads(raw)
    except json.JSONDecodeError as exc:
        records = None
        check("Task 1  parsed JSON is valid", FAIL, str(exc))
    if records is not None:
        check("Task 1  parsed JSON exists", PASS, f"{len(records)} records")
        if isinstance(records, list) and records and isinstance(records[0], dict):
            check("Task 1  it is a list of dictionaries", PASS)
        else:
            check("Task 1  it is a list of dictionaries", FAIL)
        needed = ["id", "transaction_type", "amount", "sender", "receiver", "timestamp"]
        missing = [k for k in needed if not all(k in r for r in records)]
        if missing:
            check("Task 1  key fields on every record", FAIL,
                  "missing: " + ", ".join(missing))
        else:
            check("Task 1  key fields on every record", PASS, ", ".join(needed))

# --- Task 2: the API ---------------------------------------------------------

app = read("api", "app.py")
if app is None:
    check("Task 2  api/app.py exists", FAIL)
else:
    check("Task 2  api/app.py exists", PASS)
    handlers = {"GET": "do_GET", "POST": "do_POST", "PUT": "do_PUT", "DELETE": "do_DELETE"}
    absent = [verb for verb, fn in handlers.items() if f"def {fn}" not in app]
    if absent:
        check("Task 2  all four HTTP methods handled", FAIL,
              "no handler for: " + ", ".join(absent))
    else:
        check("Task 2  all four HTTP methods handled", PASS, "GET, POST, PUT, DELETE")
    codes = [c for c in ("200", "201", "400", "401", "404") if c in app]
    check("Task 2  uses proper status codes", PASS if len(codes) == 5 else WARN,
          "found: " + ", ".join(codes))

# --- Task 3: authentication --------------------------------------------------

if app:
    if "compare_digest" in app:
        check("Task 3  constant-time credential check", PASS, "hmac.compare_digest")
    else:
        check("Task 3  constant-time credential check", WARN, "plain == comparison")
    if "environ" in app:
        check("Task 3  credentials not hardcoded", PASS, "read from environment")
    else:
        check("Task 3  credentials not hardcoded", FAIL, "hardcoded in source")
    if "WWW-Authenticate" in app:
        check("Task 3  sends WWW-Authenticate on 401", PASS)
    else:
        check("Task 3  sends WWW-Authenticate on 401", WARN)

notes = read("docs", "security_notes.md")
if notes is None:
    check("Task 3  limitations written up", FAIL, "docs/security_notes.md is missing")
else:
    has_jwt = "JWT" in notes
    has_oauth = "OAuth" in notes
    if has_jwt and has_oauth:
        check("Task 3  limitations written up", PASS, "covers JWT and OAuth 2.0")
    else:
        gaps = [n for n, ok in (("JWT", has_jwt), ("OAuth", has_oauth)) if not ok]
        check("Task 3  limitations written up", FAIL, "does not mention: " + ", ".join(gaps))

# --- Task 4: documentation ---------------------------------------------------

docs = read("docs", "api_docs.md")
if docs is None:
    check("Task 4  docs/api_docs.md exists", FAIL)
else:
    endpoints = [
        "GET /transactions`", "GET /transactions/{id}`", "POST /transactions`",
        "PUT /transactions/{id}`", "DELETE /transactions/{id}`",
    ]
    undocumented = [e[:-1] for e in endpoints if e not in docs]
    if undocumented:
        check("Task 4  all five endpoints documented", FAIL,
              "missing: " + ", ".join(undocumented))
    else:
        check("Task 4  all five endpoints documented", PASS)
    curls = docs.count("curl -u")
    jsons = docs.count("```json")
    tables = docs.count("| Code |")
    check("Task 4  request examples", PASS if curls >= 5 else FAIL, f"{curls} curl examples")
    check("Task 4  response examples", PASS if jsons >= 5 else FAIL, f"{jsons} JSON blocks")
    check("Task 4  error code tables", PASS if tables >= 5 else FAIL, f"{tables} tables")

# --- Task 5: the DSA comparison ----------------------------------------------

dsa = read("dsa", "dsa_comparison.py")
if dsa is None:
    check("Task 5  dsa/dsa_comparison.py exists", FAIL)
else:
    both = "def linear_search" in dsa and "def dict_lookup" in dsa
    check("Task 5  both search methods implemented", PASS if both else FAIL)

out = read("screenshots", "dsa_results.txt")
if out is None:
    check("Task 5  benchmark output saved", FAIL, "screenshots/dsa_results.txt is missing")
else:
    rows = re.findall(r"^\s*\d+\s+\d+\s+[\d.]+\s+[\d.]+\s+[\d.]+x", out, re.M)
    if len(rows) >= 20:
        check("Task 5  at least 20 records measured", PASS, f"{len(rows)} ids")
    else:
        check("Task 5  at least 20 records measured", FAIL, f"only {len(rows)} ids")

# --- Task 6: testing ---------------------------------------------------------

transcript = read("screenshots", "api_test_results.txt")
if transcript is None:
    check("Task 6  curl test transcript saved", FAIL)
else:
    found = [c for c in ("200", "201", "400", "401", "404") if c in transcript]
    check("Task 6  curl test transcript saved", PASS,
          "status codes shown: " + ", ".join(found))

shots = []
shot_dir = os.path.join(ROOT, "screenshots")
if os.path.isdir(shot_dir):
    shots = sorted(f for f in os.listdir(shot_dir)
                   if f.lower().endswith((".png", ".jpg", ".jpeg")))
if len(shots) >= 5:
    check("Task 6  screenshots present", PASS, f"{len(shots)} images")
else:
    check("Task 6  screenshots present", FAIL,
          f"found {len(shots)}, the assignment asks for GET, 401, POST, PUT and DELETE")

# --- deliverables ------------------------------------------------------------

for label, parts in [
    ("Deliverable  README.md", ("README.md",)),
    ("Deliverable  docs/api_docs.md", ("docs", "api_docs.md")),
    ("Deliverable  docs/report.pdf", ("docs", "report.pdf")),
]:
    exists = os.path.exists(os.path.join(ROOT, *parts))
    check(label, PASS if exists else FAIL)

report = os.path.join(ROOT, "docs", "report.pdf")
if os.path.exists(report):
    size = os.path.getsize(report)
    check("Deliverable  report.pdf is not empty", PASS if size > 5000 else FAIL,
          f"{size:,} bytes")

# --- individual effort, the multiplier ---------------------------------------

try:
    log = subprocess.run(["git", "shortlog", "-sne", "HEAD"], cwd=ROOT,
                         capture_output=True, text=True, timeout=20)
    authors = [ln.strip() for ln in log.stdout.strip().splitlines() if ln.strip()]
except Exception:
    authors = []

if not authors:
    check("Multiplier  commit history", FAIL, "no commits found")
elif len(authors) == 1:
    check("Multiplier  commit history", WARN,
          f"only one author: {authors[0]}. Fine if you worked alone. "
          f"If this is a team, everyone else scores zero.")
else:
    check("Multiplier  commit history", PASS, f"{len(authors)} authors")
    for a in authors:
        check("             " + a, PASS)

build = read("docs", "build_report.py")
if build and 'TEAM_NAME = "Team dema3"' in build:
    check("Multiplier  team name on the report", FAIL,
          "docs/build_report.py still has the placeholder team name")

check("Multiplier  team participation sheet", WARN,
      "cannot be checked from here. Missing it is an automatic zero.")

# --- print -------------------------------------------------------------------

width = max(len(n) for n, _, _ in results) + 2
print()
print("=" * (width + 40))
print("  PRE-SUBMISSION CHECK")
print("=" * (width + 40))

current = None
for name, status, detail in results:
    group = name.split()[0]
    if group != current:
        print()
        current = group
    mark = {PASS: "[ok]  ", FAIL: "[FAIL]", WARN: "[warn]"}[status]
    line = f"  {mark} {name.ljust(width)}"
    if detail:
        line += f"  {detail}"
    print(line)

fails = sum(1 for _, s, _ in results if s == FAIL)
warns = sum(1 for _, s, _ in results if s == WARN)
print()
print("=" * (width + 40))
if fails:
    print(f"  {fails} problem(s) to fix, {warns} thing(s) to look at.")
else:
    print(f"  Nothing failing. {warns} thing(s) worth a look before you submit.")
print("=" * (width + 40))
print()

sys.exit(1 if fails else 0)
