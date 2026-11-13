#!/usr/bin/env python3
"""Bundle the whole site (landing + dashboard) into ONE self-contained HTML file.

    python3 scripts/build_single_file.py
    -> dist/under-pressure-rating.html

CSS, JS, data, photos, figures, logo and the methodology PDF are inlined as data URIs, so the file
works when double-clicked (and player photos are not blocked by file:// canvas tainting).
Only Google Fonts stay as a link (falls back to system fonts offline).
"""
import base64, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "dist" / "under-pressure-rating.html"
MIME = {".webp": "image/webp", ".png": "image/png", ".jpg": "image/jpeg", ".pdf": "application/pdf", ".csv": "text/csv"}


def uri(p: pathlib.Path) -> str:
    return f"data:{MIME[p.suffix]};base64," + base64.b64encode(p.read_bytes()).decode()


def inline_assets(text: str) -> str:
    def sub(m):
        p = ROOT / m.group(0)
        return uri(p) if p.exists() else m.group(0)
    return re.sub(r"assets/(?:players/|figures/)?[A-Za-z0-9_.\-]+\.(?:webp|png|jpg|pdf)", sub, text)


def single_file_links(body: str) -> str:
    """In the one-file build the deck is embedded as a data: URL; big downloads point at the GitHub copies."""
    gh = re.search(r'github: "([^"]+)"', body).group(1)
    live = re.search(r'live: "([^"]+)"', body).group(1)
    deck = ROOT / "deck" / "index.html"
    if deck.exists():
        # Chrome refuses data: URLs over 2 MB in an iframe, so the page sets iframe.srcdoc from this base64 copy.
        body = re.sub(r'deck: "[^"]+"', 'deck: "about:blank", deckHtmlB64: "' + base64.b64encode(deck.read_bytes()).decode() + '", deckOpen: "' + live + '/deck/"', body)
    for key in ("pdf", "pptx"):
        body = re.sub(rf'{key}: "deck/([^"]+)"', lambda m: f'{key}: "{gh}/raw/main/dashboard/deck/{m.group(1)}"', body)
    return body


def main() -> None:
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    for css in re.findall(r'<link rel="stylesheet" href="(css/[^"]+)"\s*/?>', html):
        body = (ROOT / css).read_text(encoding="utf-8")
        html = re.sub(rf'<link rel="stylesheet" href="{re.escape(css)}"\s*/?>', lambda _: f"<style>\n{body}\n</style>", html)
    for js in re.findall(r'<script src="((?:js|data)/[^"]+)"></script>', html):
        body = (ROOT / js).read_text(encoding="utf-8").replace("</script", "<\\/script")
        if js == "data/links.js":
            body = single_file_links(body)
        html = html.replace(f'<script src="{js}"></script>', "<script>\n" + body + "\n</script>")
    html = inline_assets(html)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
