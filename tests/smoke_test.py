#!/usr/bin/env python3
"""Season Book smoke test: cross-checks data/season.json, the offline snapshot and the PDFs against the source data
(data/raw calendar pulls, data/gmail search pages, data/results.json, data/geo.json). Exit 1 on any failure."""
import glob, json, math, os, re, subprocess, sys, tempfile, urllib.request
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import build  # noqa: E402

fails, passes = [], 0
def check(cond, msg):
    global passes
    if cond: passes += 1
    else: fails.append(msg)

D = json.load(open(os.path.join(HERE, "data", "season.json")))
raw = {}
for f in glob.glob(os.path.join(HERE, "data", "raw", "*.json")):
    for e in json.load(open(f))["events"]:
        raw[(os.path.relpath(f, HERE), e.get("id"))] = e
geo = json.load(open(os.path.join(HERE, "data", "geo.json")))
results = json.load(open(os.path.join(HERE, "data", "results.json")))["results"]
gmail_ids = {}
for f in glob.glob(os.path.join(HERE, "data", "gmail", "*.json")):
    for t in json.load(open(f)).get("threads", []):
        for m in t["messages"]:
            gmail_ids[m["id"]] = m

# 1. every book event traces back to a raw calendar event with the same title + start
for e in D["events"]:
    r = raw.get((e["source"]["file"], e["source"]["eventId"]))
    check(r is not None, f"event {e['id']} has no raw source")
    if not r: continue
    check(r.get("summary", "").strip() == e["title"], f"title mismatch {e['id']}: {e['title']!r}")
    rs = r["start"].get("dateTime") or r["start"].get("date")
    check(e["start"][:10] == rs[:10], f"date mismatch {e['id']}")
    # 2. opponents are copied, never made up
    if e.get("opponent"):
        check(e["opponent"].lower() in re.sub(r"\s+", " ", r["summary"]).lower(), f"opponent not in source title: {e['opponent']!r}")
    if e.get("location"):
        check(build.clean(r.get("location")) == e["location"], f"location mismatch {e['id']}")

# 3. no raw game-like event is dropped (team calendars, season window)
book_ids = {(e["source"]["file"], e["source"]["eventId"]) for e in D["events"]}
for (f, rid), r in raw.items():
    if not f.endswith(("alpha.json", "charlie.json", "teams.json")): continue
    title = r.get("summary", "")
    team = build.team_of(os.path.basename(f), title)
    s = (r["start"].get("dateTime") or r["start"].get("date"))[:10]
    if team and build.SEASON[0] <= s <= build.SEASON[1]:
        check((f, rid) in book_ids, f"dropped source event: {title} {s}")

# 4. results: nothing found unless results.json has a sourced entry
games = [e for e in D["events"] if e["kind"] in ("game", "scrimmage")]
by_id = {e["id"]: e for e in D["events"]}
for r in results:
    check(r.get("eventId") in by_id, f"result for unknown event {r.get('eventId')}")
    check(r.get("score") and r.get("quote") and r["score"] in r["quote"], f"result without verbatim quote: {r}")
    mid = (r.get("source") or {}).get("messageId")
    check(mid in gmail_ids, f"result source message {mid} not in saved Gmail pages")
res_ids = {r["eventId"] for r in results}
for g in games:
    found = g["result"]["found"]
    check(found == (g["id"] in res_ids), f"result flag mismatch {g['id']}")
    if not found: check(g["result"]["text"] == "result not found", f"missing 'result not found' {g['id']}")
check(D["gmail"]["resultsFound"] == len(results), "gmail resultsFound != results.json count")

# 5. stats add up
for k, t in D["teams"].items():
    tg = [e for e in games if e["team"] == k and e["kind"] == "game" and e["status"] != "canceled"]
    s = t["stats"]
    check(s["games"] == len(tg), f"{k} games stat")
    check(s["played"] == sum(e["status"] == "played" for e in tg), f"{k} played stat")
    check(s["upcoming"] == sum(e["status"] == "upcoming" for e in tg), f"{k} upcoming stat")
    check(s["played"] + s["upcoming"] == s["games"], f"{k} played+upcoming")
    check(s["resultsFound"] == sum(1 for e in games if e["team"] == k and e["result"]["found"] and e["status"] != "canceled"), f"{k} results stat")
for kd in D["kids"]:
    for stat in ("games", "played", "upcoming"):
        check(kd["stats"][stat] == sum(D["teams"][t]["stats"][stat] for t in kd["teams"]), f"{kd['key']} {stat} sum")
check({kd["key"]: kd["teams"] for kd in D["kids"]} == {"kida": ["alpha", "bravo"], "kidb": ["charlie", "delta"]}, "kid/team mapping")

# 6. distances recompute from geo.json
H = geo["Hometown, MD"]
for e in D["events"]:
    if e["town"] and geo.get(e["town"]):
        g = geo[e["town"]]
        check(abs(build.miles((H["lat"], H["lon"]), (g["lat"], g["lon"])) - e["miles"]) < 0.11, f"miles mismatch {e['id']}")
# played/upcoming vs generatedAt
from datetime import datetime
gen = datetime.fromisoformat(D["generatedAt"])
for e in games:
    if e["status"] == "canceled": continue
    check((e["status"] == "played") == (datetime.fromisoformat(e["start"]) < gen), f"status vs time {e['id']}")

# 7. email change log is real
for c in D["gmail"]["changeLog"]:
    m = gmail_ids.get(c["messageId"])
    check(m is not None and m["subject"].startswith(c["kind"]) and c["title"][:20] in m["subject"], f"change log entry not traceable {c['messageId']}")

# 8. offline snapshot: self-contained, renders, no ride assignments
snap = os.path.join(HERE, "dist", "season-book-snapshot.html")
html = open(snap).read()
check(not re.search(r"""(src|href)=["']https?://|url\(["']?https?://|<link[^>]+stylesheet""", html), "snapshot references external resources")
with tempfile.TemporaryDirectory() as prof:
    dom = subprocess.run(["google-chrome", "--headless=new", f"--user-data-dir={prof}", "--no-sandbox", "--disable-gpu",
                          "--virtual-time-budget=5000", "--dump-dom", "file://" + snap], capture_output=True, text=True, timeout=60).stdout
check("Season at a glance" in dom, "snapshot did not render")
played_no_res = sum(1 for e in games if e["status"] == "played" and not e["result"]["found"])
check(dom.count("result not found") >= played_no_res, f"'result not found' shown {dom.count('result not found')}x < {played_no_res} played games")
for e in games:
    if e["status"] != "canceled" and e.get("opponent"):
        check(e["opponent"].replace("&", "&amp;") in dom, f"opponent missing from page: {e['opponent']}")
for bad in ("Carpool", "needs a driver", "Family drive", "Parent B drives", "Parent A drives", "driver:"):
    check(bad.lower() not in dom.lower(), f"ride-assignment text found: {bad}")
for k, t in D["teams"].items():
    check(f'id="team-{k}"' in dom, f"team section missing {k}")

# 9. PDFs per kid
for kd in D["kids"]:
    p = os.path.join(HERE, "dist", f"season-book-{kd['key']}.pdf")
    check(os.path.exists(p), f"missing {p}")
    if os.path.exists(p):
        txt = subprocess.run(["pdftotext", p, "-"], capture_output=True, text=True).stdout
        pages = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", p], capture_output=True, text=True).stdout).group(1))
        check(pages >= 2, f"{p} too short")
        check(kd["name"] in txt and "result not found" in txt, f"{p} missing kid name / honesty text")
        other = [k for k in D["kids"] if k["key"] != kd["key"]][0]
        check(all(D["teams"][t]["name"].split(" (")[0] not in txt.split("Sources")[0] for t in other["teams"]), f"{p} contains the other kid's team")

# 10. live server (if running)
try:
    body = urllib.request.urlopen("http://127.0.0.1:4246/", timeout=3).read().decode()
    check("window.SB=" in body, "server / does not serve the book")
    api = json.load(urllib.request.urlopen("http://127.0.0.1:4246/api/season.json", timeout=3))
    check(api["generatedAt"] == D["generatedAt"], "server data is stale")
    print("server: up on 4246")
except Exception as ex:
    print("server: not reachable (skipped):", ex)

print(f"{passes} checks passed, {len(fails)} failed")
for f in fails[:40]: print("  FAIL", f)
sys.exit(1 if fails else 0)
