"""One-time town-level geocode via OpenStreetMap Nominatim (public, ~1 req/s). Cached in data/geo.json.
Only town names are sent (e.g. "Aldie, VA"), never street addresses or anything personal."""
import json, os, sys, time, urllib.parse, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from venues import clean, town_of
out = os.path.join(HERE, "data", "geo.json")
geo = json.load(open(out)) if os.path.exists(out) else {}
towns = {"Hometown, MD"}
for k in ("alpha", "charlie", "teams"):
    for e in json.load(open(os.path.join(HERE, "data", "raw", f"{k}.json")))["events"]:
        t = town_of(clean(e.get("location")))[0]
        if t: towns.add(t)
for t in sorted(towns):
    if t in geo: continue
    q = urllib.parse.urlencode({"q": t + ", USA", "format": "json", "limit": 1})
    req = urllib.request.Request("https://nominatim.openstreetmap.org/search?" + q, headers={"User-Agent": "TokenMax-SeasonBook/1.0 (personal family scorebook)"})
    try:
        r = json.load(urllib.request.urlopen(req, timeout=15))
        geo[t] = {"lat": float(r[0]["lat"]), "lon": float(r[0]["lon"]), "osm": r[0].get("display_name")} if r else None
    except Exception as ex:
        geo[t] = None; print("fail", t, ex)
    print(t, geo[t] and (geo[t]["lat"], geo[t]["lon"]))
    time.sleep(1.1)
json.dump(geo, open(out, "w"), indent=1)
