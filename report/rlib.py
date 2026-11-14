"""Helpers for the end-to-end guide: page CSS, callout boxes, tables, light flow diagrams, dark chart panels."""
import base64, html, json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parent
sys.path.insert(0, str(REPO / "deck"))
import lib as dlib          # noqa: E402  (deck palette + icons)
import charts as ch         # noqa: E402  (dark SVG charts, reused inside dark panels)

esc = html.escape
D = json.loads((REPO / "deck/build/data.json").read_text())
OUT = REPO / "pipeline/outputs"

PINK, MAG, JER, BLUE, VIO = "#f5008f", "#c4007a", "#1f5fd6", "#4c8dff", "#7c5cd6"
GOOD, BAD, WARN = "#15803d", "#be123c", "#b45309"
INK, MUTED, LINE, PAPER, TINT = "#1b1424", "#5d5470", "#d9d2e3", "#ffffff", "#f6f2fa"


def uri(p):
    p = pathlib.Path(p)
    mime = {".png": "image/png", ".webp": "image/webp", ".woff2": "font/woff2", ".jpg": "image/jpeg"}[p.suffix]
    return f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"


def photo(pid):
    hits = list((REPO / "dashboard/assets/players").glob(f"{pid}_*.webp"))
    return uri(hits[0]) if hits else None


LOGO = uri(REPO / "dashboard/assets/rr-logo.png")
FONTS = REPO / "deck/fonts"


def css():
    f = lambda n: uri(FONTS / n)
    return f"""
@font-face{{font-family:Archivo;src:url({f('archivo-latin-wdth-normal.woff2')}) format('woff2');font-weight:100 900;font-stretch:62% 125%}}
@font-face{{font-family:Inter;src:url({f('inter-latin-standard-normal.woff2')}) format('woff2');font-weight:100 900}}
@page{{size:A4;margin:16mm 15mm 18mm 15mm}}
@page cover{{margin:0}}
*{{box-sizing:border-box}}
html{{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
body{{margin:0;font-family:Inter,sans-serif;font-size:10.6pt;line-height:1.55;color:{INK};background:{PAPER}}}
h1,h2,h3,h4{{font-family:Archivo;font-stretch:112%;margin:0;color:{INK};break-after:avoid}}
h1{{font-size:25pt;font-weight:850;line-height:1.08;letter-spacing:.005em}}
h2{{font-size:15pt;font-weight:820;margin:20px 0 8px;padding-top:2px}}
h3{{font-size:12pt;font-weight:800;margin:14px 0 5px}}
p{{margin:0 0 9px}}
ul,ol{{margin:0 0 10px;padding-left:20px}} li{{margin:0 0 4px}}
b,strong{{font-weight:700}}
code,.mono{{font-family:'DejaVu Sans Mono',monospace;font-size:.86em;background:{TINT};border-radius:4px;padding:1px 4px}}
pre{{font-family:'DejaVu Sans Mono',monospace;font-size:8.6pt;line-height:1.5;background:#1a1424;color:#f5f3f8;border-radius:10px;padding:12px 14px;white-space:pre-wrap;break-inside:avoid;margin:6px 0 12px}}
.pk{{color:{PINK}}} .bl{{color:{JER}}} .m{{color:{MUTED}}} .gd{{color:{GOOD}}} .bd{{color:{BAD}}}
.chapter{{break-before:page}}
.chead{{display:flex;align-items:flex-end;gap:16px;border-bottom:3px solid {PINK};padding-bottom:10px;margin-bottom:14px}}
.chead .num{{font-family:Archivo;font-weight:900;font-size:44pt;line-height:.85;color:{PINK}}}
.chead .kick{{font-family:Archivo;font-weight:800;font-size:9pt;letter-spacing:.14em;color:{MUTED};text-transform:uppercase;margin-bottom:3px}}
.lead{{font-size:11.6pt;color:#3b3149;margin-bottom:12px}}
.box{{border-radius:12px;padding:11px 14px 4px;margin:10px 0 12px;break-inside:avoid;border:1.5px solid}}
.box .bt{{font-family:Archivo;font-weight:850;font-size:9pt;letter-spacing:.12em;text-transform:uppercase;margin-bottom:5px;display:flex;align-items:center;gap:7px}}
.kid{{background:#fff4fa;border-color:#f7b5d9}} .kid .bt{{color:{MAG}}}
.math{{background:#f1f5ff;border-color:#bcd0fb}} .math .bt{{color:{JER}}}
.why{{background:#f2fbf4;border-color:#b6e2c1}} .why .bt{{color:{GOOD}}}
.warn{{background:#fff8ec;border-color:#f5d39b}} .warn .bt{{color:{WARN}}}
.mist{{background:#fff1f3;border-color:#f6b8c4}} .mist .bt{{color:{BAD}}}
.eq{{font-family:'DejaVu Sans Mono',monospace;font-size:9.4pt;background:#fff;border:1px solid #d6e0f7;border-radius:8px;padding:8px 10px;margin:6px 0 9px;white-space:pre-wrap;line-height:1.55}}
table.t{{width:100%;border-collapse:collapse;font-size:9pt;margin:6px 0 12px;break-inside:avoid}}
table.t th{{background:{JER};color:#fff;text-align:left;padding:5px 7px;font-weight:700;font-size:8.6pt}}
table.t td{{padding:4.5px 7px;border-bottom:1px solid {LINE};vertical-align:top}}
table.t tr:nth-child(even) td{{background:#faf8fc}}
table.t.pinkh th{{background:{MAG}}}
table.t td.n,table.t th.n{{text-align:right;font-variant-numeric:tabular-nums}}
figure{{margin:10px 0 14px;break-inside:avoid}}
figcaption{{font-size:8.8pt;color:{MUTED};margin-top:5px;line-height:1.45}}
figcaption b{{color:{INK}}}
.panel{{background:#1a1424;border-radius:12px;padding:12px 12px 8px;break-inside:avoid}}
.panel .pt{{font-family:Archivo;font-weight:850;font-stretch:112%;font-size:10pt;color:#f5f3f8;text-transform:uppercase;letter-spacing:.03em}}
.panel .ps{{font-size:8.4pt;color:#a39bb3;margin-bottom:4px}}
.panel svg{{display:block;width:100%;height:auto}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:12px;break-inside:avoid}}
.grid3{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px}}
.stat{{border:1.5px solid {LINE};border-radius:12px;padding:10px 12px;break-inside:avoid}}
.stat .v{{font-family:Archivo;font-weight:900;font-size:21pt;color:{PINK};line-height:1}}
.stat .l{{font-size:8.6pt;color:{MUTED};margin-top:4px;line-height:1.35}}
.chip{{display:inline-block;border-radius:999px;padding:0 8px;font-size:8pt;font-weight:700;color:#fff;line-height:16px;vertical-align:1px}}
.toc{{columns:1;font-size:10.4pt}}
.toc div{{display:flex;gap:10px;padding:4px 0;border-bottom:1px dotted {LINE}}}
.toc .tn{{font-family:Archivo;font-weight:900;color:{PINK};width:36px;flex:none}}
.toc .tp{{margin-left:auto;color:{MUTED}}}
.pcard{{display:flex;gap:10px;border:1.5px solid {LINE};border-radius:12px;padding:8px 10px;break-inside:avoid;align-items:center}}
.pcard img{{width:54px;height:54px;object-fit:cover;object-position:top;border-radius:10px;background:#efe9f5}}
.cover{{page:cover;width:210mm;height:297mm;position:relative;background:#120c1a;color:#fff;overflow:hidden}}
.cover h1{{color:#fff}}
.flow foreignObject div{{font-family:Inter;font-size:11px;line-height:1.35;color:{INK}}}
.flow foreignObject b{{font-family:Archivo;font-weight:800;font-size:12px;display:block;margin-bottom:2px}}
.small{{font-size:9pt}}
.nobreak{{break-inside:avoid}}
.tag{{font-family:Archivo;font-weight:800;font-size:8pt;letter-spacing:.1em;color:{MUTED};text-transform:uppercase}}
"""


# ----------------------------------------------------------------------------------------- building blocks
ICON = {"kid": "🧒", "math": "∑", "why": "✓", "warn": "!", "mist": "✗"}
TITLE = {"kid": "Explain it simply", "math": "The maths", "why": "Why this choice", "warn": "Watch out", "mist": "Mistake we caught"}


def box(kind, body, title=None):
    return f'<div class="box {kind}"><div class="bt">{TITLE[kind] if title is None else title}</div>{body}</div>'


def eq(s):
    return f'<div class="eq">{esc(s.replace(chr(92) + "n", chr(10)))}</div>'


def table(head, rows, cls="", num=()):
    th = "".join(f'<th class="{"n" if i in num else ""}">{h}</th>' for i, h in enumerate(head))
    tr = "".join("<tr>" + "".join(f'<td class="{"n" if i in num else ""}">{c}</td>' for i, c in enumerate(r)) + "</tr>" for r in rows)
    return f'<table class="t {cls}"><tr>{th}</tr>{tr}</table>'


def fig(inner, cap):
    return f'<figure>{inner}<figcaption>{cap}</figcaption></figure>'


def panel(title, sub, svg_inner, w, h):
    defs = '<defs><marker id="ah" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#a39bb3"/></marker></defs>'
    head = (f'<div class="pt">{title}</div>' if title else "") + (f'<div class="ps">{sub}</div>' if sub else "")
    return f'<div class="panel">{head}<svg viewBox="0 0 {w} {h}" style="font-family:Inter">{defs}{svg_inner}</svg></div>'


def chapter(num, kicker, title, lead):
    return (f'<section class="chapter"><div class="chead"><div class="num">{num}</div><div><div class="kick">{kicker}</div>'
            f'<h1>{title}</h1></div></div><p class="lead">{lead}</p>')


def stats(items, cols=4):
    return f'<div style="display:grid;grid-template-columns:repeat({cols},1fr);gap:10px;margin:8px 0 14px">' + "".join(
        f'<div class="stat"><div class="v">{v}</div><div class="l">{l}</div></div>' for v, l in items) + "</div>"


def chip(text, color):
    return f'<span class="chip" style="background:{color}">{text}</span>'


# ----------------------------------------------------------------------------------------- light flow diagrams
FILL = {"n": ("#ffffff", "#bfb4cf"), "p": ("#fff0f8", PINK), "b": ("#eef4ff", JER), "g": ("#effaf2", GOOD),
        "r": ("#fff1f3", BAD), "y": ("#fff8ea", WARN), "v": ("#f4f0ff", VIO), "d": ("#1a1424", "#1a1424"), "s": (PINK, PINK), "j": (JER, JER)}


class Flow:
    """Boxes with wrapped text (foreignObject) and orthogonal arrows. Coordinates in px of a W x H canvas."""

    def __init__(self, w, h):
        self.w, self.h, self.nodes, self.parts = w, h, {}, []

    def node(self, k, x, y, w, h, title, sub="", kind="n", fs=11, align="left"):
        self.nodes[k] = (x, y, w, h)
        bg, bd = FILL[kind]
        txt = "#fff" if kind in ("d", "s", "j") else INK
        sc = "#ffe3f3" if kind == "s" else ("#dbe7ff" if kind == "j" else ("#c9c1d6" if kind == "d" else MUTED))
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{bg}" stroke="{bd}" stroke-width="1.6"/>'
                          f'<foreignObject x="{x + 8}" y="{y + 5}" width="{w - 16}" height="{h - 10}"><div xmlns="http://www.w3.org/1999/xhtml" '
                          f'style="height:100%;display:flex;flex-direction:column;justify-content:center;text-align:{align};color:{txt};font-size:{fs}px">'
                          f'<b style="font-size:{fs + 1}px">{title}</b>{f"<span style=color:{sc}>{sub}</span>" if sub else ""}</div></foreignObject>')
        return self

    def text(self, x, y, s, size=10.5, color=MUTED, anchor="start", weight=600):
        self.parts.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" text-anchor="{anchor}" font-weight="{weight}" font-family="Inter">{esc(s)}</text>')
        return self

    def raw(self, s):
        self.parts.append(s)
        return self

    def _pt(self, k, side, t=0.5):
        x, y, w, h = self.nodes[k]
        return {"r": (x + w, y + h * t), "l": (x, y + h * t), "t": (x + w * t, y), "b": (x + w * t, y + h)}[side]

    def edge(self, a, b, sa="r", sb="l", color="#8a7f9c", label="", ta=0.5, tb=0.5, dash=False, via=None, lab_dy=-5, lab_dx=0):
        x1, y1 = self._pt(a, sa, ta)
        x2, y2 = self._pt(b, sb, tb)
        if via is not None:
            pts = [(x1, y1)] + via + [(x2, y2)]
        elif sa in "lr" and sb in "lr":
            mx = (x1 + x2) / 2 if via is None else via
            pts = [(x1, y1), (mx, y1), (mx, y2), (x2, y2)] if abs(y1 - y2) > 1 else [(x1, y1), (x2, y2)]
        elif sa in "tb" and sb in "tb":
            my = (y1 + y2) / 2
            pts = [(x1, y1), (x1, my), (x2, my), (x2, y2)] if abs(x1 - x2) > 1 else [(x1, y1), (x2, y2)]
        elif sa in "lr":
            pts = [(x1, y1), (x2, y1), (x2, y2)]
        else:
            pts = [(x1, y1), (x1, y2), (x2, y2)]
        d = "M" + " L".join(f"{px:.1f},{py:.1f}" for px, py in pts)
        col = color.replace("#", "")
        da = 'stroke-dasharray="5 4"' if dash else ""
        self.parts.insert(0, f'<path d="{d}" fill="none" stroke="{color}" stroke-width="1.8" {da} marker-end="url(#m{col})"/>')
        self._markers = getattr(self, "_markers", set()) | {color}
        if label:
            i = len(pts) // 2
            lx, ly = (pts[i - 1][0] + pts[i][0]) / 2, (pts[i - 1][1] + pts[i][1]) / 2
            self.parts.append(f'<text x="{lx + lab_dx:.1f}" y="{ly + lab_dy:.1f}" font-size="9.5" fill="{color}" text-anchor="middle" font-weight="700" font-family="Inter" '
                              f'paint-order="stroke" stroke="#fff" stroke-width="3">{esc(label)}</text>')
        return self

    def svg(self):
        mk = "".join(f'<marker id="m{c.replace("#", "")}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
                     f'<path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>' for c in getattr(self, "_markers", set()))
        return f'<svg class="flow" viewBox="0 0 {self.w} {self.h}" style="width:100%;height:auto;display:block"><defs>{mk}</defs>{"".join(self.parts)}</svg>'
