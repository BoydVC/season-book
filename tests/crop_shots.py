#!/usr/bin/env python3
"""Full-page screenshot of the offline snapshot, then crop named sections into screenshots/*.png."""
import json, os, re, subprocess, tempfile, html
from PIL import Image
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
snap = "file://" + os.path.join(HERE, "dist", "season-book-snapshot.html")
W = 1440
def chrome(*args):
    with tempfile.TemporaryDirectory() as p:
        return subprocess.run(["google-chrome", "--headless=new", f"--user-data-dir={p}", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
                               "--virtual-time-budget=5000", "--run-all-compositor-stages-before-draw", *args], capture_output=True, text=True, timeout=90).stdout
dom = chrome(f"--window-size={W},1000", "--dump-dom", snap)
o = json.loads(html.unescape(re.search(r'data-offsets="([^"]+)"', dom).group(1)))
full = os.path.join(HERE, "screenshots", "02-full-book.png")
chrome(f"--window-size={W},{o['total']}", f"--screenshot={full}", snap)
im = Image.open(full)
def crop(name, top, h):
    im.crop((0, max(0, top), W, min(im.height, top + h))).save(os.path.join(HERE, "screenshots", name)); print("screenshots/" + name)
crop("01-overview.png", 0, o["kid-kida"][0] - 10)
crop("03-kida-hornets-scorebook.png", o["kid-kida"][0] - 20, min(o["team-alpha"][1] + 90, 1500))
crop("04-kidb-aspire-scorebook.png", o["kid-kidb"][0] - 20, min(o["team-charlie"][1] + 90, 1700))
crop("05-tournaments.png", o["tournaments"][0] - 20, o["tournaments"][1] + 30)
crop("06-venues-map.png", o["venues"][0] - 20, 1100)
crop("07-sources-honesty.png", o["sources"][0] - 20, min(o["sources"][1] + 30, 1400))
print("screenshots/02-full-book.png", im.size)
