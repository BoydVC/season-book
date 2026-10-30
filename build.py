"""Season Book data build: data/raw/*.json (read-only calendar pulls) + data/gmail/*.json (read-only searches)
+ data/results.json (scores stated in email/app notifications; empty unless a source says so) -> data/season.json.
Pure local processing. No network. Never invents scores, opponents or results."""
import glob, hashlib, json, math, os, re, sys
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from venues import clean, split_venue, town_of, venue_key, TOWN_HINTS

ET = ZoneInfo("America/New_York")
HOME = ("Hometown, MD", 39.0000000, -76.6000000)
TRAVEL_MILES = 25  # straight-line miles from Hometown that count as a "travel venue"
SEASON = ("2026-08-01", "2026-12-31")

KIDS = [
    {"key": "kida", "name": "Kid A", "full": "Kid A", "born": "2015-01-01", "color": "#0f766e",
     "teams": ["alpha", "bravo"]},
    {"key": "kidb", "name": "Kid B", "full": "Kid B", "born": "2013-01-01", "color": "#be185d",
     "teams": ["charlie", "delta"]},
]
TEAMS = {
    "alpha": {"name": "Team Alpha 12U", "sport": "Soccer", "emoji": "⚽", "color": "#15803d", "kid": "kida",
                "calendar": "Team Alpha 12U (imported calendar)", "raw": "alpha.json", "prefix": r"^Team Alpha 12U\s*"},
    "bravo": {"name": "Bravo 11u Blue", "sport": "Baseball", "emoji": "⚾", "color": "#1d4ed8", "kid": "kida",
            "calendar": "Parent A team-schedules calendar (TeamSnap import)", "raw": "teams.json", "prefix": r"^Bravo 11u\s*-\s*Blue\s*(-\s*)?"},
    "charlie": {"name": "U14G Charlie (12/13 Charlie, Copa)", "sport": "Soccer", "emoji": "⚽", "color": "#7c3aed", "kid": "kidb",
               "calendar": "360Player Event calendar (U14G Charlie)", "raw": "charlie.json", "prefix": r"^(U14G Charlie|12/13 Charlie)\s*"},
    "delta": {"name": "Delta 2031 Green", "sport": "Lacrosse", "emoji": "🥍", "color": "#0e7490", "kid": "kidb",
                  "calendar": "Parent A team-schedules calendar (TeamSnap import)", "raw": "teams.json", "prefix": r"^Delta 2031 Green\s*(-\s*)?",
                  "bonus": "Also on Kid B's calendar this fall (girls' lacrosse); included so her book is complete."},
}
TYPO = {"colombia fall classic": "Columbia Fall Classic"}


def team_of(cal, title):
    t = re.sub(r"^\[CANCELED\]\s*", "", title, flags=re.I)
    if cal == "teams.json":
        if t.startswith("Bravo 11u"): return "bravo"
        if t.startswith("Delta 2031"): return "delta"
        return None
    return {"alpha.json": "alpha", "charlie.json": "charlie"}.get(cal)


def parse_dt(d):
    if "dateTime" in d:
        return datetime.fromisoformat(d["dateTime"]).astimezone(ET), False
    return datetime.fromisoformat(d["date"]).replace(tzinfo=ET), True


def classify(core, all_day, start, end):
    lo = core.lower()
    if re.search(r"\bpractice\b", lo): return "practice"
    if "scrimmage" in lo: return "scrimmage"
    if re.search(r"(^|\s)(vs\.?|@|at)\s+\S", lo) and not re.search(r"training|meeting", lo): return "game"
    if re.search(r"training|stickwork|academy", lo): return "training"
    if "meeting" in lo: return "meeting"
    if re.search(r"paintball|holiday event|team event", lo): return "team_event"
    if "championships game" in lo: return "game"
    if re.search(r"(^|\s)(vs\.?|@|at)\s+\S", lo): return "game"
    day_long = all_day or (start.hour == 0 and start.minute == 0 and (end - start) >= timedelta(hours=20))
    if day_long or re.search(r"tournament|cup|copa|classic|fest|showcase|rivalry|brawl", lo): return "tournament"
    return "other"


def opponent_of(core):
    m = re.search(r"(?:^|\s)(vs\.?|@|at)\s+(.+)$", core.strip(), flags=re.I)
    if not m: return None, None
    mark = {"vs": "vs", "vs.": "vs", "@": "@", "at": "@"}[m.group(1).lower()]
    opp = re.sub(r"\s+", " ", m.group(2)).strip()
    return opp, mark


def notes_of(desc, kind):
    d = re.sub(r"https?://\S+", "", desc or "")
    d = d.replace("[CANCELED]", "").strip()
    out = {}
    m = re.search(r"Arrival Time:\s*([0-9: ]+[AP]M)", d)
    if m: out["arrival"] = re.sub(r"\s+", " ", m.group(1)).strip()
    m = re.search(r"Uniform:\s*([^\n(]+)", d)
    if m: out["kit"] = m.group(1).strip()
    m = re.search(r"Location:\s*(.+?)(?:\s{2,}|Uniform:|\(Arrival|$)", d, flags=re.S)
    if m: out["spot"] = re.sub(r"\s+", " ", m.group(1)).strip()
    m = re.search(r"DIRECTIONS AT THE SCHOOL:\s*(.+)", d, flags=re.S)
    if m: out["directions"] = re.sub(r"\s+", " ", m.group(1)).strip()[:400]
    if not out and kind in ("game", "scrimmage") and d:
        first = re.sub(r"\s+", " ", d.split("DIRECTIONS")[0]).strip()
        km = re.search(r"((?:Blue|White|Black|Gray|Grey|Green)[^.]*?(?:kits?|/[A-Za-z]+/[A-Za-z]+[^.]*)|(?:Green|White) [Kk]its)", first)
        fm = re.search(r"(Field\s+\w+|Upper Kinder \w|\b\d+[AB]\b)", first, flags=re.I)
        if km: out["kit"] = km.group(1).strip()
        if fm: out["spot"] = fm.group(1).strip()
        if "BRING ALL JERSEYS" in first: out["extra"] = "Bring all jerseys"
        if "Wear" in first and "kit" not in out:
            out["kit"] = first.replace("Wear", "").strip()[:80]
    return out


def miles(a, b):
    R = 3958.8
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def load_results():
    p = os.path.join(HERE, "data", "results.json")
    if not os.path.exists(p): return []
    return json.load(open(p)).get("results", [])


def build(now=None):
    now = now or datetime.now(ET)
    geo = json.load(open(os.path.join(HERE, "data", "geo.json")))
    results = {r["eventId"]: r for r in load_results()}
    events, seen = [], set()
    for t in TEAMS.values():
        pass
    for raw in sorted({t["raw"] for t in TEAMS.values()}):
        data = json.load(open(os.path.join(HERE, "data", "raw", raw)))
        for e in data["events"]:
            title = (e.get("summary") or "").strip()
            team = team_of(raw, title)
            if not team: continue
            start, all_day = parse_dt(e["start"]); end, _ = parse_dt(e["end"])
            if not (SEASON[0] <= start.date().isoformat() <= SEASON[1]): continue
            canceled = bool(re.match(r"^\[CANCELED\]", title, re.I)) or e.get("status") == "cancelled"
            core = re.sub(r"^\[CANCELED\]\s*", "", title, flags=re.I)
            core = re.sub(TEAMS[team]["prefix"], "", core).strip(" -")
            kind = classify(core, all_day, start, end)
            opp, mark = opponent_of(core) if kind in ("game", "scrimmage") else (None, None)
            if kind == "game" and "championships game" in core.lower():
                opp, mark = None, None
            loc = clean(e.get("location"))
            vname, vfield, vaddr = split_venue(loc)
            town, town_note = town_of(loc)
            g = geo.get(town) if town else None
            mi = round(miles(HOME[1:], (g["lat"], g["lon"])), 1) if g else None
            eid = hashlib.sha1(f"{raw}|{e.get('id')}".encode()).hexdigest()[:10]
            key = (team, title, start.isoformat())
            if key in seen: continue
            seen.add(key)
            status = "canceled" if canceled else ("played" if start < now and kind != "tournament" or (kind == "tournament" and end <= now) else ("in progress" if kind == "tournament" and start <= now < end else "upcoming"))
            if kind != "tournament" and not canceled:
                status = "played" if start < now else "upcoming"
            ev = {
                "id": eid, "team": team, "kid": TEAMS[team]["kid"], "kind": kind, "status": status,
                "title": title, "core": core, "opponent": opp, "mark": mark,
                "start": start.isoformat(), "end": end.isoformat(), "allDay": all_day,
                "date": start.date().isoformat(),
                "location": loc, "venueName": vname or None, "field": vfield or None, "address": vaddr or None,
                "venueKey": venue_key(loc) if town else None, "town": town, "townNote": town_note, "miles": mi,
                "notes": notes_of(e.get("description"), kind),
                "source": {"calendar": TEAMS[team]["calendar"], "eventId": e.get("id"), "file": f"data/raw/{raw}"},
            }
            if kind in ("game", "scrimmage"):
                r = results.get(eid)
                ev["result"] = ({"found": True, **r} if r else {"found": False, "text": "result not found"})
            events.append(ev)
    events.sort(key=lambda x: (x["start"], x["team"]))

    # tournaments: group tournament-day markers per team by normalized name
    tours = []
    for team in TEAMS:
        groups = {}
        for ev in events:
            if ev["team"] != team or ev["kind"] != "tournament": continue
            base = re.sub(r"^\d{4}\s+", "", ev["core"]).strip()
            base = TYPO.get(base.lower(), base)
            base = re.sub(r"\s*\(both days\)", "", base)
            groups.setdefault(base.lower(), {"name": base, "days": [], "titles": set(), "locs": set(), "canceled": [], "spots": {}})
            gr = groups[base.lower()]
            gr["days"].append(ev["date"]); gr["titles"].add(ev["core"])
            if ev["location"] and ev["location"].lower() not in ("tbd",): gr["locs"].add(ev["location"])
            gr["canceled"].append(ev["status"] == "canceled")
            sp = ev["notes"].get("spot")
            if sp and ev["location"] and re.search(r"\d", ev["location"]): gr["spots"][ev["location"]] = sp
        for gr in groups.values():
            days = sorted(set(gr["days"]))
            gm = [ev for ev in events if ev["team"] == team and ev["kind"] in ("game", "scrimmage") and ev["date"] in days]
            locs = sorted(gr["locs"]) or sorted({g["location"] for g in gm if g["location"]})
            first = datetime.fromisoformat(days[0]).date()
            last = datetime.fromisoformat(days[-1]).date()
            st = "canceled" if all(gr["canceled"]) else ("past" if last < now.date() else ("in progress" if first <= now.date() <= last else "upcoming"))
            towns = sorted({g["town"] for g in gm if g["town"]}) or sorted({town_of(l)[0] for l in locs if town_of(l)[0]})
            mi = max([g["miles"] for g in gm if g["miles"] is not None] or [None] if gm else [None], key=lambda x: x or 0)
            if mi is None and towns and geo.get(towns[0]):
                gg = geo[towns[0]]; mi = round(miles(HOME[1:], (gg["lat"], gg["lon"])), 1)
            vnames = []
            for l in locs:
                n, _f, a = split_venue(l)
                lab = gr["spots"].get(l) or n or a or l
                if l in TOWN_HINTS and not re.search(r"\d", l):
                    if l not in vnames: vnames.append(l)
                    continue
                tn = town_of(l)[0]
                lab = f"{lab}, {tn.split(',')[0]}" if tn and tn.split(",")[0] not in lab else lab
                if lab not in vnames: vnames.append(lab)
            tours.append({"team": team, "kid": TEAMS[team]["kid"], "name": gr["name"], "days": days, "status": st,
                          "titles": sorted(gr["titles"]), "locations": locs, "venues": vnames, "towns": towns, "miles": mi,
                          "games": [g["id"] for g in gm if g["status"] != "canceled"],
                          "resultsFound": sum(1 for g in gm if g.get("result", {}).get("found"))})
    tours.sort(key=lambda t: (t["days"][0], t["team"]))
    for ev in events:
        ev["tournament"] = next((t["name"] for t in tours if t["team"] == ev["team"] and ev["date"] in t["days"] and ev["kind"] != "tournament"), None)

    # venues
    vmap = {}
    for ev in events:
        if not ev["venueKey"] or ev["status"] == "canceled": continue
        if ev["kind"] == "tournament" and not re.search(r"\d", ev["location"] or ""): continue  # 'Loudoun, VA'-style placeholders
        v = vmap.setdefault(ev["venueKey"], {"key": ev["venueKey"], "names": set(), "address": ev["address"] or ev["location"], "town": ev["town"],
                                             "townNote": ev["townNote"], "miles": ev["miles"], "teams": set(), "kids": set(), "kinds": {}, "fields": set(),
                                             "notes": set(), "directions": None, "dates": []})
        if ev["venueName"]: v["names"].add(ev["venueName"])
        if ev["notes"].get("spot"):
            sp = ev["notes"]["spot"]
            v["notes"].add(sp)
            if not ev["venueName"] and not re.match(r"^(Field|\d|Upper)", sp): v["names"].add(re.split(r"\s+-\s+", sp)[0])
        if ev["field"]: v["fields"].add(ev["field"])
        if ev["notes"].get("directions"): v["directions"] = ev["notes"]["directions"]
        v["teams"].add(ev["team"]); v["kids"].add(ev["kid"])
        v["kinds"][ev["kind"]] = v["kinds"].get(ev["kind"], 0) + 1
        v["dates"].append(ev["date"])
    venues = []
    for v in vmap.values():
        g = geo.get(v["town"]) if v["town"] else None
        names = sorted(v["names"], key=len)
        venues.append({**v, "name": names[0] if names else v["address"], "aka": names[1:], "teams": sorted(v["teams"]), "kids": sorted(v["kids"]),
                       "fields": sorted(v["fields"]), "notes": sorted(v["notes"])[:6], "lat": g and g["lat"], "lon": g and g["lon"],
                       "names": None, "visits": len(v["dates"]), "first": min(v["dates"]), "last": max(v["dates"]),
                       "travel": (v["miles"] or 0) >= TRAVEL_MILES,
                       "gameDays": len({d for d, k in zip(v["dates"], [1]*len(v["dates"]))})})
    venues.sort(key=lambda v: (v["miles"] is None, v["miles"] or 0))

    def stats(evs, trs):
        games = [e for e in evs if e["kind"] == "game"]
        live = [e for e in games if e["status"] != "canceled"]
        played = [e for e in live if e["status"] == "played"]
        upcoming = [e for e in live if e["status"] == "upcoming"]
        scr = [e for e in evs if e["kind"] == "scrimmage" and e["status"] != "canceled"]
        prac = [e for e in evs if e["kind"] in ("practice", "training") and e["status"] != "canceled"]
        trav_keys = {e["venueKey"] for e in live + scr if e["venueKey"] and (e["miles"] or 0) >= TRAVEL_MILES}
        for t in trs:
            if t["status"] != "canceled" and (t["miles"] or 0) >= TRAVEL_MILES and not t["games"]:
                trav_keys.add("tour:" + t["name"])
        far = max(live + scr, key=lambda e: e["miles"] or 0, default=None)
        states = sorted({(e["town"] or "")[-2:] for e in live + scr if e["town"]})
        wk = {}
        for e in live:
            d = datetime.fromisoformat(e["date"]).date()
            wk.setdefault(d - timedelta(days=(d.weekday() - 5) % 7), []).append(e)
        busiest = max(wk.items(), key=lambda kv: len(kv[1]), default=(None, []))
        return {
            "games": len(live), "played": len(played), "upcoming": len(upcoming),
            "canceled": len([e for e in games if e["status"] == "canceled"]), "scrimmages": len(scr),
            "practices": len(prac), "practicesPlayed": len([e for e in prac if e["status"] == "played"]),
            "tournaments": len([t for t in trs if t["status"] != "canceled"]),
            "travelVenues": len(trav_keys), "resultsFound": sum(1 for e in live + scr if e.get("result", {}).get("found")),
            "farthest": far and {"opponent": far["opponent"], "town": far["town"], "miles": far["miles"], "date": far["date"]},
            "states": states, "venues": len({e["venueKey"] for e in live + scr if e["venueKey"]}),
            "busiestWeekend": busiest[0] and {"start": busiest[0].isoformat(), "games": len(busiest[1])},
        }

    teams_out = {}
    for k, t in TEAMS.items():
        evs = [e for e in events if e["team"] == k]
        trs = [x for x in tours if x["team"] == k]
        teams_out[k] = {**{kk: vv for kk, vv in t.items() if kk not in ("raw", "prefix")}, "key": k, "stats": stats(evs, trs)}
    kids_out = []
    for kd in KIDS:
        evs = [e for e in events if e["kid"] == kd["key"]]
        trs = [x for x in tours if x["kid"] == kd["key"]]
        b = datetime.fromisoformat(kd["born"]).date(); n = now.date()
        age = n.year - b.year - ((n.month, n.day) < (b.month, b.day))
        kids_out.append({**kd, "age": age, "stats": stats(evs, trs)})

    gmail = gmail_summary()
    return {
        "_note": "Built by Season Book from read-only calendar + Gmail searches. Scores appear only when a team email/app notification states them.",
        "generatedAt": now.isoformat(timespec="seconds"), "season": SEASON, "home": HOME[0], "travelMiles": TRAVEL_MILES,
        "kids": kids_out, "teams": teams_out, "events": events, "tournaments": tours, "venues": venues, "gmail": gmail,
        "results": list(results.values()),
    }


def gmail_summary():
    files = sorted(glob.glob(os.path.join(HERE, "data", "gmail", "*.json")))
    searches, changes, seenmsg = [], [], set()
    log = json.load(open(os.path.join(HERE, "data", "gmail_searches.json")))
    for f in files:
        d = json.load(open(f))
        for t in d.get("threads", []):
            for m in t.get("messages", []):
                if m["id"] in seenmsg: continue
                seenmsg.add(m["id"])
                if "calendar-notification@google.com" not in (m.get("sender") or ""): continue
                subj = m.get("subject") or ""
                mm = re.match(r"^(New event|Updated invitation|Canceled event|Invitation):\s*(.+?)\s*@\s*(.+?)\s*\((?:Parent A|Family Events)\)\s*$", subj)
                if not mm: continue
                what, title, when = mm.groups()
                team = "bravo" if "Bravo 11u" in title else ("delta" if "Delta 2031" in title else None)
                if not team: continue
                ch = re.search(r"Changed:\s*([a-z, ]+?)(?:\s+Location|\s+Description|$)", m.get("snippet") or "")
                changes.append({"received": m["date"], "team": team, "kind": what, "title": title, "when": when,
                                "changed": ch.group(1).strip() if ch else None, "messageId": m["id"]})
    changes.sort(key=lambda c: c["received"], reverse=True)
    return {"searches": log["searches"], "resultsFound": log["resultsFound"], "changeLog": changes,
            "messagesScanned": len(seenmsg)}


if __name__ == "__main__":
    now = datetime.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else None
    data = build(now)
    out = os.path.join(HERE, "data", "season.json")
    json.dump(data, open(out + ".tmp", "w"), indent=1, ensure_ascii=False, default=list)
    os.replace(out + ".tmp", out)
    for k, t in data["teams"].items():
        s = t["stats"]; print(f"{t['name']:<34} games {s['games']:>2} (played {s['played']}, upcoming {s['upcoming']}, canceled {s['canceled']}) scrim {s['scrimmages']} tours {s['tournaments']} travel {s['travelVenues']} results {s['resultsFound']}")
    print(len(data["events"]), "events,", len(data["venues"]), "venues,", len(data["tournaments"]), "tournaments,", len(data["gmail"]["changeLog"]), "email schedule changes")
