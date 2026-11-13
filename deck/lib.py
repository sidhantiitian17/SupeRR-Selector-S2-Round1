"""Slide-building helpers: frame (title band, logo, footer nav), positioned boxes, SVG connectors, charts.

Coordinates are slide pixels on a 1600 x 900 canvas. Boxes are absolutely positioned HTML (so text wraps
naturally); connectors and charts are SVG drawn from the same coordinates, so arrows land on box edges.
Colours follow the dashboard (css/styles.css) exactly; no gradients anywhere.
"""
import html, base64, pathlib, math, io

W, H = 1600, 900
C = dict(bg="#0b0610", frame="#120c1a", panel="#1a1424", panel2="#221b30", line="#3a3048", border="rgba(255,255,255,0.08)",
         magenta="#c4007a", pink="#f5008f", jersey="#1f5fd6", blue="#4c8dff", violet="#a78bfa",
         good="#22c55e", bad="#f43f5e", warn="#f59e0b", text="#f5f3f8", muted="#a39bb3", faint="#6e6680")
BAT, BOWL = C["pink"], C["blue"]          # role colour coding used on every slide
SA, SB, HY = C["blue"], C["violet"], C["pink"]   # solution A, solution B, hybrid

ROOT = pathlib.Path(__file__).parent
REPO = ROOT.parent
SECTIONS = ["PROBLEM", "DATA & PRESSURE", "METHOD", "ITERATIONS", "RESULTS", "RR STRATEGY", "REPRODUCE"]

esc = html.escape


def data_uri(path, mime=None):
    p = pathlib.Path(path)
    mime = mime or {".png": "image/png", ".webp": "image/webp", ".jpg": "image/jpeg", ".svg": "image/svg+xml", ".woff2": "font/woff2"}[p.suffix]
    return f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"


def photo(pid_name):
    hits = list((REPO / "dashboard/assets/players").glob(f"{pid_name}_*.webp")) if isinstance(pid_name, int) else []
    return data_uri(hits[0]) if hits else None


LOGO = None


def logo():
    global LOGO
    LOGO = LOGO or data_uri(REPO / "dashboard/assets/rr-logo.png")
    return LOGO


# ---------------------------------------------------------------- icons (Lucide-style strokes, 24px grid)
ICON = {
    "bat": '<path d="M4 20 14 10"/><path d="m14 10 4-4 2 2-4 4"/><path d="M3 21l2-2"/>',
    "ball": '<circle cx="12" cy="12" r="8"/><path d="M7 6c3 3 3 9 0 12M17 6c-3 3-3 9 0 12"/>',
    "target": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.5"/>',
    "gauge": '<path d="M4 16a8 8 0 1 1 16 0"/><path d="m12 16 4-5"/>',
    "db": '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/><path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/>',
    "filter": '<path d="M3 4h18l-7 8v7l-4 2v-9z"/>',
    "chart": '<path d="M3 3v18h18"/><path d="m7 15 4-5 3 3 5-7"/>',
    "scale": '<path d="M12 3v18M5 7h14M3 14l2-7 2 7a2.8 2.8 0 0 1-4 0zM17 14l2-7 2 7a2.8 2.8 0 0 1-4 0z"/>',
    "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/>',
    "trophy": '<path d="M8 21h8M12 17v4M7 4h10v5a5 5 0 0 1-10 0z"/><path d="M17 5h3v2a3 3 0 0 1-3 3M7 5H4v2a3 3 0 0 0 3 3"/>',
    "users": '<circle cx="9" cy="8" r="3.5"/><path d="M2 21a7 7 0 0 1 14 0"/><circle cx="17" cy="9" r="2.5"/><path d="M17 14a5 5 0 0 1 5 5"/>',
    "split": '<path d="M12 3v6M12 9 5 16v5M12 9l7 7v5"/>',
    "dice": '<rect x="3" y="3" width="18" height="18" rx="3"/><circle cx="8" cy="8" r="1.3"/><circle cx="16" cy="16" r="1.3"/><circle cx="12" cy="12" r="1.3"/><circle cx="16" cy="8" r="1.3"/><circle cx="8" cy="16" r="1.3"/>',
    "check": '<path d="m5 12 5 5 9-10"/>',
    "x": '<path d="M6 6l12 12M18 6 6 18"/>',
    "zap": '<path d="M13 2 4 14h7l-1 8 9-12h-7z"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "code": '<path d="m8 8-5 4 5 4M16 8l5 4-5 4M14 4l-4 16"/>',
    "github": '<path d="M9 19c-4 1.3-4-2-6-2.5M15 21v-3.5c0-1 .1-1.4-.5-2 2.8-.3 5.5-1.4 5.5-6a4.6 4.6 0 0 0-1.3-3.2 4.2 4.2 0 0 0-.1-3.2s-1-.3-3.4 1.3a11.6 11.6 0 0 0-6 0C6.8 2.8 5.8 3.1 5.8 3.1a4.2 4.2 0 0 0-.1 3.2A4.6 4.6 0 0 0 4.4 9.5c0 4.6 2.7 5.7 5.5 6-.6.6-.6 1.2-.5 2V21"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="m21 21-5-5"/>',
    "flag": '<path d="M5 21V4M5 4h11l-2 4 2 4H5"/>',
    "repeat": '<path d="M17 2l3 3-3 3"/><path d="M4 11V9a4 4 0 0 1 4-4h12M7 22l-3-3 3-3"/><path d="M20 13v2a4 4 0 0 1-4 4H4"/>',
    "alert": '<path d="M12 3 2 21h20z"/><path d="M12 10v5M12 18v.5"/>',
    "brain": '<path d="M9 4a3 3 0 0 0-3 3 3 3 0 0 0-2 5 3 3 0 0 0 2 5 3 3 0 0 0 6 1V5a3 3 0 0 0-3-1zM15 4a3 3 0 0 1 3 3 3 3 0 0 1 2 5 3 3 0 0 1-2 5 3 3 0 0 1-6 1"/>',
    "layers": '<path d="m12 3 9 5-9 5-9-5z"/><path d="m3 13 9 5 9-5"/>',
    "eye": '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
    "cart": '<circle cx="9" cy="20" r="1.5"/><circle cx="18" cy="20" r="1.5"/><path d="M2 3h3l3 12h11l2-8H6"/>',
    "swap": '<path d="M7 4 3 8l4 4M3 8h14M17 20l4-4-4-4M21 16H7"/>',
    "lock": '<rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
    "file": '<path d="M6 2h9l5 5v15H6z"/><path d="M14 2v6h6M9 13h7M9 17h7"/>',
    "play": '<circle cx="12" cy="12" r="9"/><path d="m10 8 6 4-6 4z"/>',
    "star": '<path d="m12 3 2.8 5.8 6.2.9-4.5 4.4 1 6.2L12 17.4 6.5 20.3l1-6.2L3 9.7l6.2-.9z"/>',
    "bug": '<rect x="7" y="7" width="10" height="13" rx="5"/><path d="M12 7V4M9 4l1 3M15 4l-1 3M3 12h4M17 12h4M4 18l3-2M20 18l-3-2M4 7l3 2M20 7l-3 2"/>',
}


def icon(name, size=20, color="currentColor", sw=2):
    return (f'<svg class="ic" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{sw}" '
            f'stroke-linecap="round" stroke-linejoin="round">{ICON[name]}</svg>')


def icon_svg(name, x, y, size=20, color="#fff", sw=2):
    s = size / 24
    return f'<g transform="translate({x},{y}) scale({s})" fill="none" stroke="{color}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round">{ICON[name]}</g>'


# ---------------------------------------------------------------- positioned HTML
def box(x, y, w, h=None, inner="", cls="", style=""):
    hh = f"height:{h}px;" if h else ""
    return f'<div class="abs {cls}" style="left:{x}px;top:{y}px;width:{w}px;{hh}{style}">{inner}</div>'


def pill(x, y, w, text, color=None, h=34, fs=15, ic=None, cls=""):
    color = color or C["jersey"]
    i = icon(ic, 17, "#fff") + " " if ic else ""
    return box(x, y, w, h, f"{i}{text}", f"pill {cls}", f"background:{color};font-size:{fs}px;line-height:{h}px")


def card(x, y, w, h, inner, cls="", style=""):
    return box(x, y, w, h, inner, f"card {cls}", style)


def chip(text, color, filled=False):
    if filled:
        return f'<span class="chip" style="background:{color};color:#fff;border-color:{color}">{text}</span>'
    return f'<span class="chip" style="color:{color};border-color:{color}">{text}</span>'


# ---------------------------------------------------------------- connectors
class Graph:
    """Collects node rectangles and connector paths for one slide; nodes are HTML, edges are one SVG layer."""

    def __init__(self):
        self.nodes, self.html, self.edges = {}, [], []

    def node(self, key, x, y, w, h, inner, cls="node", style=""):
        self.nodes[key] = (x, y, w, h)
        self.html.append(box(x, y, w, h, inner, cls, style))
        return self

    def anchor(self, key, side, t=0.5):
        x, y, w, h = self.nodes[key]
        return {"l": (x, y + h * t), "r": (x + w, y + h * t), "t": (x + w * t, y), "b": (x + w * t, y + h)}[side]

    def edge(self, a, b, sa="r", sb="l", color=None, dash=False, label=None, ta=0.5, tb=0.5, via=None, lw=2.2, lab_dx=0, lab_dy=-8):
        color = color or C["faint"]
        (x1, y1), (x2, y2) = self.anchor(a, sa, ta), self.anchor(b, sb, tb)
        self.edges.append(path_between(x1, y1, x2, y2, sa, sb, color, dash, label, via, lw, lab_dx, lab_dy))
        return self

    def raw_edge(self, pts, color=None, dash=False, label=None, lw=2.2):
        color = color or C["faint"]
        self.edges.append(poly(pts, color, dash, label, lw))
        return self

    def render(self):
        return "".join(self.html) + svg_layer("".join(self.edges))


def _mid(sa, sb, x1, y1, x2, y2):
    if sa in "lr" and sb in "lr":
        mx = (x1 + x2) / 2
        return [(x1, y1), (mx, y1), (mx, y2), (x2, y2)]
    if sa in "tb" and sb in "tb":
        my = (y1 + y2) / 2
        return [(x1, y1), (x1, my), (x2, my), (x2, y2)]
    if sa in "lr":
        return [(x1, y1), (x2, y1), (x2, y2)]
    return [(x1, y1), (x1, y2), (x2, y2)]


def path_between(x1, y1, x2, y2, sa, sb, color, dash, label, via, lw, lab_dx=0, lab_dy=-8):
    pts = [(x1, y1)] + (via or []) + [(x2, y2)] if via else _mid(sa, sb, x1, y1, x2, y2)
    return poly(pts, color, dash, label, lw, lab_dx, lab_dy)


def poly(pts, color, dash, label, lw, lab_dx=0, lab_dy=-8):
    # drop zero-length segments, round the corners slightly
    clean = [pts[0]]
    for p in pts[1:]:
        if abs(p[0] - clean[-1][0]) > 0.5 or abs(p[1] - clean[-1][1]) > 0.5:
            clean.append(p)
    pts = clean
    r = 10
    d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
    for i in range(1, len(pts) - 1):
        (ax, ay), (bx, by), (cx, cy) = pts[i - 1], pts[i], pts[i + 1]
        l1 = math.hypot(bx - ax, by - ay); l2 = math.hypot(cx - bx, cy - by)
        rr = min(r, l1 / 2, l2 / 2)
        p1 = (bx - (bx - ax) / l1 * rr, by - (by - ay) / l1 * rr) if l1 else (bx, by)
        p2 = (bx + (cx - bx) / l2 * rr, by + (cy - by) / l2 * rr) if l2 else (bx, by)
        d += f" L{p1[0]:.1f},{p1[1]:.1f} Q{bx:.1f},{by:.1f} {p2[0]:.1f},{p2[1]:.1f}"
    d += f" L{pts[-1][0]:.1f},{pts[-1][1]:.1f}"
    mk = marker_id(color)
    da = ' stroke-dasharray="6 5"' if dash else ""
    out = f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{lw}"{da} marker-end="url(#{mk})"/>'
    if label:
        # label on the longest segment
        segs = [(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]), i) for i in range(len(pts) - 1)]
        _, i = max(segs)
        lx = (pts[i][0] + pts[i + 1][0]) / 2 + lab_dx; ly = (pts[i][1] + pts[i + 1][1]) / 2 + lab_dy
        out += f'<text x="{lx:.1f}" y="{ly:.1f}" class="elab" text-anchor="middle">{esc(label)}</text>'
    return out


_MARKERS = {}


def marker_id(color):
    k = "m" + color.strip("#").replace("(", "").replace(")", "").replace(",", "").replace(" ", "").replace(".", "")
    _MARKERS[k] = color
    return k


def svg_layer(content, z=1):
    defs = "".join(f'<marker id="{k}" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
                   f'<path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>' for k, c in _MARKERS.items())
    return f'<svg class="layer" style="z-index:{z}" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><defs>{defs}</defs>{content}</svg>'


def svg_abs(x, y, w, h, content, extra=""):
    defs = "".join(f'<marker id="{k}" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
                   f'<path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>' for k, c in _MARKERS.items())
    return f'<svg class="abs" style="left:{x}px;top:{y}px;{extra}" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><defs>{defs}</defs>{content}</svg>'


def t(x, y, s, size=13, color=None, anchor="start", weight=500, cls="", extra=""):
    color = color or C["muted"]
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{color}" text-anchor="{anchor}" font-weight="{weight}" class="{cls}" {extra}>{esc(str(s))}</text>'


# ---------------------------------------------------------------- frame
def slide(num, title, section, body, notes="", subtitle=None):
    nav = "".join(f'<span class="{"on" if s == section else ""}">{s}</span>' for s in SECTIONS) if section else ""
    sub = f'<div class="sub">{subtitle}</div>' if subtitle else ""
    foot = f'<nav class="foot">{nav}<b class="pg">{num:02d}</b></nav>' if section else ""
    band = (f'<header class="band"><h1>{title}</h1>{sub}</header><div class="logo-tile"><img src="{logo()}" alt="Rajasthan Royals"/></div>'
            if title else "")
    return f'<section class="slide" data-n="{num}" data-title="{esc(strip_tags(title or "Cover"))}">{band}{body}{foot}<aside class="notes">{esc(notes)}</aside></section>'


def strip_tags(s):
    import re
    return re.sub("<[^>]+>", "", s)


def css():
    f = ROOT / "fonts"
    return f"""
@font-face{{font-family:Archivo;src:url({data_uri(f/'archivo-latin-wdth-normal.woff2')}) format('woff2');font-weight:100 900;font-stretch:62% 125%}}
@font-face{{font-family:Inter;src:url({data_uri(f/'inter-latin-standard-normal.woff2')}) format('woff2');font-weight:100 900}}
@font-face{{font-family:Bebas;src:url({data_uri(f/'bebas-neue-latin-400-normal.woff2')}) format('woff2')}}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{background:{C['bg']};}}
body{{font-family:Inter,Arial,sans-serif;color:{C['text']};-webkit-font-smoothing:antialiased}}
.slide{{position:relative;width:{W}px;height:{H}px;background:{C['frame']};overflow:hidden;page-break-after:always;break-after:page}}
.abs{{position:absolute}}
.layer{{position:absolute;left:0;top:0;pointer-events:none}}
.band{{position:absolute;left:0;top:0;width:{W - 124}px;height:78px;background:{C['magenta']};padding:0 34px;display:flex;align-items:center;gap:22px}}
.band h1{{font-family:Archivo;font-stretch:118%;font-weight:850;font-size:34px;letter-spacing:.01em;color:#fff;text-transform:uppercase;white-space:nowrap}}
.band .sub{{font-size:15px;color:#ffe3f3;font-weight:500;margin-top:4px}}
.logo-tile{{position:absolute;right:0;top:0;width:124px;height:78px;background:{C['panel']};display:grid;place-items:center}}
.logo-tile img{{height:62px}}
.foot{{position:absolute;left:0;right:0;bottom:0;height:40px;border-top:2px solid {C['line']};display:flex;align-items:center;padding:0 30px;gap:0;justify-content:space-between}}
.foot span{{font-family:Archivo;font-stretch:112%;font-weight:750;font-size:13px;letter-spacing:.06em;color:{C['faint']};position:relative;height:40px;line-height:40px}}
.foot span.on{{color:{C['pink']}}}
.foot span.on:before{{content:"";position:absolute;left:-10px;right:-10px;top:-2px;height:4px;background:{C['pink']}}}
.foot .pg{{font-family:Archivo;font-weight:800;color:{C['muted']};font-size:13px}}
.notes{{display:none}}
.pill{{border-radius:9px;color:#fff;font-family:Archivo;font-stretch:112%;font-weight:800;letter-spacing:.04em;text-align:center;text-transform:uppercase;white-space:nowrap;display:flex;align-items:center;justify-content:center;gap:8px}}
.card{{background:{C['panel']};border:1px solid {C['border']};border-radius:14px;padding:16px 18px}}
.card.tint{{background:{C['panel2']}}}
.node{{background:{C['panel']};border:1.5px solid {C['line']};border-radius:12px;padding:10px 12px;font-size:14px;line-height:1.35;z-index:2;display:flex;flex-direction:column;justify-content:center}}
.node>b{{font-family:Archivo;font-stretch:110%;font-weight:800;font-size:15px;letter-spacing:.01em;display:flex;align-items:center;gap:7px}}
.node small{{color:{C['muted']};font-size:12.5px;line-height:1.35;display:block;margin-top:3px}}
.node.hot{{border-color:{C['pink']}}}
.node.blue{{border-color:{C['blue']}}}
.node.violet{{border-color:{C['violet']}}}
.node.good{{border-color:{C['good']}}}
.node.bad{{border-color:{C['bad']}}}
.node.solid{{background:{C['jersey']};border-color:{C['jersey']}}}
.node.solid small{{color:#dbe7ff}}
.node.pinkfill{{background:{C['magenta']};border-color:{C['magenta']}}}
.node.pinkfill small{{color:#ffe3f3}}
.h2{{font-family:Archivo;font-stretch:115%;font-weight:850;font-size:18px;letter-spacing:.03em;text-transform:uppercase;color:{C['text']}}}
.h3{{font-family:Archivo;font-stretch:110%;font-weight:800;font-size:15px;letter-spacing:.02em;color:{C['text']}}}
.p{{font-size:14.5px;line-height:1.5;color:{C['text']}}}
.m{{color:{C['muted']}}}
.s{{font-size:13px;line-height:1.45}}
.xs{{font-size:12px;line-height:1.4}}
ul.b{{list-style:none;font-size:14px;line-height:1.45}}
ul.b li{{position:relative;padding-left:16px;margin:0 0 6px}}
ul.b li:before{{content:"";position:absolute;left:2px;top:8px;width:6px;height:6px;border-radius:50%;background:{C['pink']}}}
ul.b.blue li:before{{background:{C['blue']}}}
ul.b.good li:before{{background:{C['good']}}}
ul.b.bad li:before{{background:{C['bad']}}}
.chip{{display:inline-block;border:1.5px solid;border-radius:999px;padding:1px 9px;font-size:12px;font-weight:700;line-height:18px;white-space:nowrap}}
.big{{font-family:Archivo;font-stretch:118%;font-weight:900;line-height:1}}
.pk{{color:{C['pink']}}} .bl{{color:{C['blue']}}} .vi{{color:{C['violet']}}} .gd{{color:{C['good']}}} .bd{{color:{C['bad']}}} .wn{{color:{C['warn']}}}
.elab{{font:600 12px Inter,Arial;fill:{C['muted']};paint-order:stroke;stroke:{C['frame']};stroke-width:5px}}
svg text{{font-family:Inter,Arial,sans-serif}}
.ic{{flex:none;vertical-align:-3px}}
.mono{{font-family:ui-monospace,Menlo,Consolas,monospace}}
table.t{{border-collapse:collapse;width:100%;font-size:13px}}
table.t th{{background:{C['jersey']};color:#fff;font-weight:700;padding:6px 8px;text-align:left;font-size:12px;letter-spacing:.02em}}
table.t td{{padding:6px 8px;border-bottom:1px solid {C['line']};color:{C['text']}}}
table.t tr.hl td{{background:rgba(245,0,143,.13);font-weight:700}}
.ph{{border-radius:12px;background:{C['panel2']};overflow:hidden}}
.ph:not(.abs){{position:relative}}
.ph img{{position:absolute;left:0;right:0;bottom:0;width:100%;height:100%;object-fit:contain;object-position:center bottom}}
.mono-ini{{display:grid;place-items:center;font-family:Archivo;font-weight:900;font-size:30px;color:#fff;background:{C['jersey']};width:100%;height:100%}}
a{{color:inherit}}
"""
