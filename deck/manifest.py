"""Slide titles, speaker notes and clickable link areas for pptx.js (read back from build/deck.html)."""
import re, json, html, pathlib
from deck import LIVE, GITHUB
H = pathlib.Path(__file__).parent / "build"
h = (H / "deck.html").read_text()
secs = re.findall(r'<section class="slide" data-n="(\d+)" data-title="([^"]*)">.*?<aside class="notes">(.*?)</aside></section>', h, re.S)
links = {1: [(70, 636, 470, 110, LIVE), (70, 756, 470, 110, GITHUB)], 19: [(34, 96, 504, 250, LIVE), (554, 96, 504, 250, GITHUB)],
         20: [(640, 620, 420, 124, LIVE), (1080, 620, 420, 124, GITHUB)]}
man = [{"n": int(n), "title": html.unescape(t), "notes": html.unescape(no), "img": f"build/png/slide-{int(n):02d}.png", "links": links.get(int(n), [])} for n, t, no in secs]
(H / "manifest.json").write_text(json.dumps(man, indent=1))
print("manifest:", len(man), "slides")
