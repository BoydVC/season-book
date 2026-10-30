"""Render data/season.json + web/ into self-contained offline HTML files in dist/ (fonts subset + inlined)."""
import base64, io, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(HERE, "dist"); os.makedirs(DIST, exist_ok=True)
FONTS = [("SB Serif", "Fraunces.ttf", "100 900"), ("SB Grotesk", "SpaceGrotesk.ttf", "300 700"), ("SB Mono", "JetBrainsMono.ttf", "100 800")]


def font_b64(fn):
    cache = os.path.join(HERE, "web", "fonts", fn.replace(".ttf", ".subset.woff"))
    src = os.path.join(HERE, "web", "fonts", fn)
    if not os.path.exists(cache) or os.path.getmtime(cache) < os.path.getmtime(src):
        try:
            from fontTools import subset
            opts = subset.Options(); opts.flavor = "woff"; opts.layout_features = ["*"]
            f = subset.load_font(src, opts)
            s = subset.Subsetter(opts); s.populate(unicodes=list(range(0x20, 0x7F)) + list(range(0xA0, 0x180)) + [0x2013, 0x2014, 0x2018, 0x2019, 0x201C, 0x201D, 0x2022, 0x2026, 0x00B7, 0x2192, 0x2191, 0x2193, 0x2009, 0x00D7])
            s.subset(f); subset.save_font(f, cache, opts); mime = "font/woff"
        except Exception as ex:  # brotli missing etc -> embed full ttf
            print("subset failed, embedding full font:", ex)
            return "font/ttf", base64.b64encode(open(src, "rb").read()).decode()
    return "font/woff", base64.b64encode(open(cache, "rb").read()).decode()


def page(data, preset):
    css = open(os.path.join(HERE, "web", "style.css")).read()
    js = open(os.path.join(HERE, "web", "app.js")).read()
    ff = ""
    for fam, fn, w in FONTS:
        mime, b = font_b64(fn)
        fmt = {'font/woff': 'woff', 'font/woff2': 'woff2'}.get(mime, 'truetype')
        ff += f"@font-face{{font-family:'{fam}';src:url(data:{mime};base64,{b}) format('{fmt}');font-weight:{w};font-display:block}}\n"
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    title = "Season Book · Fall 2026" if not preset.get("kid") else f"{preset['kid'].title()}'s Season Book · Fall 2026"
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><style>{ff}{css}</style></head><body><div class="wrap" id="app"><p style="padding:40px">Loading Season Book…</p></div>
<script>window.SB={blob};window.SB_PRESET={json.dumps(preset)};</script><script>{js}</script></body></html>"""


if __name__ == "__main__":
    data = json.load(open(os.path.join(HERE, "data", "season.json")))
    outs = {"season-book-snapshot.html": {}, "print-kida.html": {"kid": "kida", "print": True}, "print-kidb.html": {"kid": "kidb", "print": True}}
    for name, preset in outs.items():
        html = page(data, preset)
        with open(os.path.join(DIST, name + ".tmp"), "w") as f: f.write(html)
        os.replace(os.path.join(DIST, name + ".tmp"), os.path.join(DIST, name))
        print(name, f"{len(html)/1024:.0f} KB")
