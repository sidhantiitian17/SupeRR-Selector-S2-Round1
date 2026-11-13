"""Small SVG chart functions for the deck. Every chart: one axis, recessive grid, direct labels, dashboard colours."""
import math
from lib import C, BAT, BOWL, esc, t

GRID = "#2c2438"
AX = dict(size=12, color=C["muted"])


def _ticks(lo, hi, n=5):
    span = hi - lo
    step = 10 ** math.floor(math.log10(span / n)) if span > 0 else 1
    for m in (1, 2, 2.5, 5, 10):
        if span / (step * m) <= n:
            step *= m; break
    v = math.floor(lo / step) * step
    out = []
    while v <= hi + 1e-9:
        out.append(round(v, 6)); v += step
    return out


def stacked_bars(bars, w, h, legend=()):
    pl, pr, pt, pb = 40, 10, 30, 30
    mx = max(sum(v for v, _ in segs) for _, segs in bars)
    ticks = _ticks(0, mx * 1.08, 5); top = ticks[-1]
    iw, ih = w - pl - pr, h - pt - pb
    o = []
    for tk in ticks:
        y = pt + ih - tk / top * ih
        o.append(f'<line x1="{pl}" x2="{w - pr}" y1="{y:.1f}" y2="{y:.1f}" stroke="{GRID}"/>' + t(pl - 6, y + 4, int(tk), 11, anchor="end"))
    bw = iw / len(bars) * 0.56
    for i, (lab, segs) in enumerate(bars):
        cx = pl + iw / len(bars) * (i + 0.5); y = pt + ih
        for v, col in segs:
            hh = v / top * ih
            o.append(f'<rect x="{cx - bw / 2:.1f}" y="{y - hh + 1:.1f}" width="{bw:.1f}" height="{max(hh - 2, 0):.1f}" rx="3" fill="{col}"/>')
            if hh > 20:
                o.append(t(cx, y - hh / 2 + 4, v, 12, "#fff", "middle", 700))
            y -= hh
        o.append(t(cx, pt + ih + 18, lab, 12, C["text"], "middle", 600))
        o.append(t(cx, y - 6, sum(v for v, _ in segs), 12, C["text"], "middle", 700))
    lx = pl
    for name, col in legend:
        o.append(f'<rect x="{lx}" y="4" width="12" height="12" rx="3" fill="{col}"/>' + t(lx + 18, 14, name, 12, C["text"]))
        lx += 70
    return "".join(o)


def chase_chart(balls, w, h, cut):
    pl, pr, pt, pb = 46, 14, 14, 34
    iw, ih = w - pl - pr, h - pt - pb
    top_h = ih * 0.58; gap = 26; bot_h = ih - top_h - gap
    n = len(balls); dx = iw / n
    o = []
    # WP panel
    for v in (0, .25, .5, .75, 1):
        y = pt + top_h - v * top_h
        o.append(f'<line x1="{pl}" x2="{w - pr}" y1="{y:.1f}" y2="{y:.1f}" stroke="{GRID}"/>' + t(pl - 6, y + 4, f"{int(v * 100)}%", 11, anchor="end"))
    pts = " ".join(f"{pl + dx * (i + .5):.1f},{pt + top_h - b['wp'] * top_h:.1f}" for i, b in enumerate(balls))
    o.append(f'<polyline points="{pts}" fill="none" stroke="{C["text"]}" stroke-width="2.4"/>')
    last = balls[-1]
    o.append(f'<circle cx="{pl + dx * (n - .5):.1f}" cy="{pt + top_h - last["wpa"] * top_h:.1f}" r="5" fill="{C["good"]}"/>')
    o.append(t(pl + 4, pt + 14, "Win probability (chasing side)", 12, C["text"], weight=700))
    # PI panel
    y0 = pt + top_h + gap
    mx = max(b["pi"] for b in balls)
    ycut = y0 + bot_h - cut / mx * bot_h
    for i, b in enumerate(balls):
        hh = b["pi"] / mx * bot_h
        o.append(f'<rect x="{pl + dx * i + .6:.1f}" y="{y0 + bot_h - hh:.1f}" width="{max(dx - 1.2, 1):.1f}" height="{hh:.1f}" fill="{C["pink"] if b["hp"] else "#3b3149"}"/>')
    o.append(f'<line x1="{pl}" x2="{w - pr}" y1="{ycut:.1f}" y2="{ycut:.1f}" stroke="{C["pink"]}" stroke-dasharray="5 4"/>')
    o.append(t(w - pr - 4, ycut - 6, f"top-30% cut-off (PI {cut:.2f})", 11, C["pink"], "end", 700))
    o.append(t(pl + 4, y0 - 6, "Pressure Index of each ball", 12, C["text"], weight=700))
    # over ticks
    seen = set()
    for i, b in enumerate(balls):
        if b["ov"] % 5 == 0 and b["ov"] not in seen:
            seen.add(b["ov"]); x = pl + dx * i
            o.append(t(x, h - 12, f"over {b['ov']}", 11, anchor="middle"))
    # annotate last over
    i0 = next(i for i, b in enumerate(balls) if b["ov"] == balls[-1]["ov"])
    x0 = pl + dx * i0
    o.append(f'<rect x="{x0 - 2:.1f}" y="{pt:.1f}" width="{dx * (n - i0) + 4:.1f}" height="{ih:.1f}" fill="none" stroke="{C["warn"]}" stroke-width="1.5" rx="4"/>')
    o.append(t(x0 - 8, pt + 34, f"Last over: needed {balls[i0]['need']} off {balls[i0]['left']}", 12, C["warn"], "end", 700))
    o.append(t(x0 - 8, pt + 50, f"{balls[-1]['s']} finishes it with a six", 12, C["warn"], "end", 600))
    return "".join(o)


def calibration(cal, w, h):
    pl, pr, pt, pb = 38, 22, 8, 30
    iw, ih = w - pl - pr, h - pt - pb
    o = [f'<line x1="{pl}" y1="{pt + ih}" x2="{pl + iw}" y2="{pt}" stroke="{C["faint"]}" stroke-dasharray="4 4"/>']
    for v in (0, .5, 1):
        o.append(t(pl - 5, pt + ih - v * ih + 4, f"{int(v * 100)}%", 10, anchor="end") + t(pl + v * iw, h - 12, f"{int(v * 100)}%", 10, anchor="middle"))
    for inn, col in (("1", C["blue"]), ("2", C["pink"])):
        pts = " ".join(f"{pl + p * iw:.1f},{pt + ih - ob * ih:.1f}" for p, ob, _ in cal[inn])
        o.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="2.2"/>')
        for p, ob, _ in cal[inn]:
            o.append(f'<circle cx="{pl + p * iw:.1f}" cy="{pt + ih - ob * ih:.1f}" r="3.5" fill="{col}" stroke="{C["panel"]}" stroke-width="1.5"/>')
    o.append(t(pl + 6, pt + 14, "chase", 11, C["pink"], weight=700) + t(pl + 6, pt + 28, "1st innings", 11, C["blue"], weight=700))
    o.append(t(pl + iw - 4, pt + ih - 6, "predicted →", 10, anchor="end"))
    return "".join(o)


def def_bars(rows, w, h):
    o = []; rowh = h / len(rows)
    for i, (lab, share, ratio, flagged) in enumerate(rows):
        y = i * rowh + 8; col = C["pink"] if i == 0 else C["faint"]
        o.append(t(0, y + 14, lab, 13.5, C["text"], weight=700))
        bw = (w - 150) * share / 100
        o.append(f'<rect x="0" y="{y + 24}" width="{w - 150}" height="22" rx="5" fill="{GRID}"/>')
        o.append(f'<rect x="0" y="{y + 24}" width="{bw:.1f}" height="22" rx="5" fill="{col}"/>')
        o.append(t(bw + 8 if share < 80 else bw - 8, y + 40, f"{share:.0f}% of decisive swing", 12, C["text"], "start", 700))
        o.append(t(w - 140, y + 40, f"{ratio:.2f}×", 22, col if i == 0 else C["muted"], "start", 850, extra='font-family="Archivo"'))
        o.append(t(0, y + 64, f"flags {flagged:.0f}% of balls", 11.5))
    return "".join(o)


def threshold(rows, w, h):
    pl, pr, pt, pb = 46, 70, 16, 44
    iw, ih = w - pl - pr, h - pt - pb
    cats = ["top 40%", "top 30%", "top 25%", "top 20%", "top 15%"]
    lo, hi = 0.15, 0.35
    o = []
    for v in (0.15, 0.2, 0.25, 0.3, 0.35):
        y = pt + ih - (v - lo) / (hi - lo) * ih
        o.append(f'<line x1="{pl}" x2="{pl + iw}" y1="{y:.1f}" y2="{y:.1f}" stroke="{GRID}"/>' + t(pl - 6, y + 4, f"{v:.2f}", 11, anchor="end"))
    xs = {c: pl + iw * i / (len(cats) - 1) for i, c in enumerate(cats)}
    xc = xs["top 30%"]
    o.append(f'<rect x="{xc - 26}" y="{pt}" width="52" height="{ih}" rx="6" fill="rgba(245,0,143,.12)"/>')
    nb = {r["top_share"]: r["n_players"] for r in rows if r["role"] == "bat"}; nw = {r["top_share"]: r["n_players"] for r in rows if r["role"] == "bowl"}
    for c in cats:
        on = c == "top 30%"
        o.append(t(xs[c], h - 18, c, 12, C["pink"] if on else C["muted"], "middle", 700 if on else 500))
        o.append(t(xs[c], h - 3, f"{nb[c]} / {nw[c]} players", 10.5, C["text"] if on else C["faint"], "middle", 600))
    for role, col in (("bat", BAT), ("bowl", BOWL)):
        pts = [(xs[r["top_share"]], pt + ih - (r["quality_rho"] - lo) / (hi - lo) * ih) for r in rows if r["role"] == role]
        pts.sort()
        o.append(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}" fill="none" stroke="{col}" stroke-width="2.4"/>')
        for x, y in pts:
            o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="{col}" stroke="{C["panel"]}" stroke-width="2"/>')
        x, y = pts[-1]
        o.append(t(x + 10, y + 4, "batters" if role == "bat" else "bowlers", 12, col, weight=700))
    o.append(t(pl, pt - 2, "reliability (split-half ρ)", 11))
    return "".join(o)


def heatmap(cells, w, h):
    pl, pt, pb = 74, 6, 30
    overs = sorted({c[0] for c in cells}); wk = sorted({c[1] for c in cells})
    cw = (w - pl - 10) / len(overs); chh = (h - pt - pb) / len(wk)
    mx = 3.0
    o = []
    for ov, wl, pi, nn in cells:
        if nn < 30:
            continue
        a = min(pi / mx, 1)
        x = pl + overs.index(ov) * cw; y = pt + wk.index(wl) * chh
        o.append(f'<rect x="{x + 1:.1f}" y="{y + 1:.1f}" width="{cw - 2:.1f}" height="{chh - 2:.1f}" rx="3" fill="rgba(245,0,143,{0.06 + 0.94 * a:.2f})"/>')
    for i, wl in enumerate(wk):
        o.append(t(pl - 8, pt + i * chh + chh / 2 + 4, f"{wl}{'+' if wl == wk[-1] else ''} down", 11, anchor="end"))
    for ov in overs:
        if ov in (1, 5, 10, 15, 20):
            o.append(t(pl + overs.index(ov) * cw + cw / 2, h - 10, f"over {ov}", 11, anchor="middle"))
    return "".join(o)


def hbars(items, w, h, unit="", maxv=None, fmt="{:.1f}", label_w=150):
    maxv = maxv or max(v for _, v, _ in items) * 1.1
    rowh = h / len(items); o = []
    for i, (lab, v, col) in enumerate(items):
        y = i * rowh + rowh / 2 - 16
        o.append(t(0, y + 22, lab, 14, C["text"], weight=700))
        bw = (w - label_w - 90) * v / maxv
        o.append(f'<rect x="{label_w}" y="{y}" width="{bw:.1f}" height="32" rx="6" fill="{col}"/>')
        o.append(t(label_w + bw + 10, y + 22, fmt.format(v) + unit, 16, C["text"], weight=800, extra='font-family="Archivo"'))
    return "".join(o)


def shrink(rows, w, h):
    pl, pr, pt, pb = 50, 16, 10, 36
    iw, ih = w - pl - pr, h - pt - pb
    xs = [r[1] for r in rows]; ys = [r[2] for r in rows] + [r[3] for r in rows]
    x0, x1 = 100, max(xs) * 1.04
    y0, y1 = min(ys) - 5, max(ys) + 5
    lx = lambda v: pl + (math.log(v) - math.log(x0)) / (math.log(x1) - math.log(x0)) * iw
    ly = lambda v: pt + ih - (v - y0) / (y1 - y0) * ih
    mean = sum(r[3] for r in rows) / len(rows)
    o = []
    for v in _ticks(y0, y1, 6):
        if y0 <= v <= y1:
            o.append(f'<line x1="{pl}" x2="{pl + iw}" y1="{ly(v):.1f}" y2="{ly(v):.1f}" stroke="{GRID}"/>' + t(pl - 6, ly(v) + 4, f"{v:+.0f}" if v else "0", 11, anchor="end"))
    for v in (150, 200, 300, 500, 800):
        if v <= x1:
            o.append(t(lx(v), h - 14, v, 11, anchor="middle"))
    o.append(t(pl + iw, h - 2, "pressure balls faced (log scale) →", 11, anchor="end"))
    o.append(t(pl + 4, pt + 12, "value per 100 pressure balls", 11))
    o.append(f'<line x1="{pl}" x2="{pl + iw}" y1="{ly(mean):.1f}" y2="{ly(mean):.1f}" stroke="{C["faint"]}" stroke-dasharray="5 4"/>')
    o.append(t(pl + iw - 4, ly(mean) - 6, "pool average", 11, anchor="end"))
    for name, balls, raw, sh in rows:
        x = lx(balls)
        if abs(raw - sh) > 1.5:
            o.append(f'<line x1="{x:.1f}" y1="{ly(raw):.1f}" x2="{x:.1f}" y2="{ly(sh):.1f}" stroke="#5a4c6c" stroke-width="1.2"/>')
        o.append(f'<circle cx="{x:.1f}" cy="{ly(raw):.1f}" r="3.2" fill="#6e6680"/>')
        o.append(f'<circle cx="{x:.1f}" cy="{ly(sh):.1f}" r="3.6" fill="{C["pink"]}"/>')
    # label the most-shrunk
    rows2 = sorted(rows, key=lambda r: -abs(r[2] - r[3]))[:3]
    for name, balls, raw, sh in rows2:
        o.append(t(lx(balls) + 7, ly(raw) + 4, f"{name}: {round(raw):+d} → {round(sh):+d}", 11.5, C["text"], weight=600))
    o.append(f'<circle cx="{pl + iw - 170}" cy="{pt + 12}" r="4" fill="#6e6680"/>' + t(pl + iw - 160, pt + 16, "raw", 11.5, C["text"]))
    o.append(f'<circle cx="{pl + iw - 110}" cy="{pt + 12}" r="4" fill="{C["pink"]}"/>' + t(pl + iw - 100, pt + 16, "shrunk (used)", 11.5, C["text"]))
    return "".join(o)


def staircase(stages, w, h, key_mean, key_worst, col):
    """stages: list of (label, mean, worst, kind)."""
    pl, pr, pt, pb = 44, 10, 18, 66
    iw, ih = w - pl - pr, h - pt - pb
    lo, hi = -0.3, 0.4
    y = lambda v: pt + ih - (v - lo) / (hi - lo) * ih
    o = []
    for v in (-0.2, 0, 0.2, 0.4):
        o.append(f'<line x1="{pl}" x2="{pl + iw}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke="{GRID if v else C["faint"]}"/>' + t(pl - 6, y(v) + 4, f"{v:+.1f}" if v else "0", 11, anchor="end"))
    n = len(stages); bw = iw / n * 0.36
    for i, (lab, m, wv, kind) in enumerate(stages):
        cx = pl + iw / n * (i + .5)
        c = C["pink"] if kind == "final" else (C["blue"] if kind == "A" else C["violet"] if kind == "B" else "#4a3f5c")
        o.append(f'<rect x="{cx - bw - 2:.1f}" y="{min(y(m), y(0)):.1f}" width="{bw:.1f}" height="{abs(y(m) - y(0)):.1f}" rx="3" fill="{c}"/>')
        o.append(f'<rect x="{cx + 2:.1f}" y="{min(y(wv), y(0)):.1f}" width="{bw:.1f}" height="{abs(y(wv) - y(0)):.1f}" rx="3" fill="none" stroke="{c}" stroke-width="2"/>')
        fm = lambda v: "≈0" if abs(v) < 0.005 else f"{v:+.2f}"
        o.append(t(cx - bw / 2 - 2, (y(m) - 6) if m >= 0 else (y(m) + 14), fm(m), 10.5, C["text"], "middle", 700))
        o.append(t(cx + bw / 2 + 2, (y(wv) - 6) if wv >= 0 else (y(wv) + 14), fm(wv), 10.5, C["muted"], "middle", 600))
        words = lab.split(" "); line = ""; lines = []
        for wd in words:
            if len(line + wd) > 12:
                lines.append(line.strip()); line = ""
            line += wd + " "
        lines.append(line.strip())
        for j, ln in enumerate(lines):
            o.append(t(cx, pt + ih + 18 + j * 14, ln, 11.5, C["text"] if kind == "final" else C["muted"], "middle", 700 if kind == "final" else 500))
    return "".join(o)


def tournament(points, w, h, role, col):
    pl, pr, pt, pb = 50, 14, 14, 40
    iw, ih = w - pl - pr, h - pt - pb
    pts = [p for p in points if p[1] == role]
    wx = [p[2] for p in pts]; my = [p[3] for p in pts]
    x0, x1 = min(wx) - .03, max(wx) + .03; y0, y1 = min(my) - .03, max(my) + .03
    X = lambda v: pl + (v - x0) / (x1 - x0) * iw; Y = lambda v: pt + ih - (v - y0) / (y1 - y0) * ih
    o = []
    for v in _ticks(x0, x1, 5):
        if x0 <= v <= x1:
            o.append(f'<line x1="{X(v):.1f}" x2="{X(v):.1f}" y1="{pt}" y2="{pt + ih}" stroke="{GRID}"/>' + t(X(v), h - 22, "0" if abs(v) < 1e-9 else f"{v:+.2f}", 10.5, anchor="middle"))
    for v in _ticks(y0, y1, 5):
        if y0 <= v <= y1:
            o.append(f'<line x1="{pl}" x2="{pl + iw}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="{GRID}"/>' + t(pl - 6, Y(v) + 4, f"{v:.2f}", 10.5, anchor="end"))
    o.append(t(pl + iw / 2, h - 4, "worst of 16 held-out cells →  (higher = safer)", 11.5, anchor="middle"))
    o.append(t(pl + 4, pt + 10, "average gain ↑", 11.5))
    lab = {}
    for name, r, wv, mv, chosen, has_u in pts:
        kind = "A" if name.startswith("A:") else "B" if name.startswith("B:") else "R" if name in ("random",) else "H"
        c = {"A": C["blue"], "B": C["violet"], "R": C["faint"]}.get(kind, "#5d5070")
        rad = 4
        if chosen:
            c, rad = C["pink"], 8
        o.append(f'<circle cx="{X(wv):.1f}" cy="{Y(mv):.1f}" r="{rad}" fill="{c}" stroke="{C["panel"]}" stroke-width="1.5"/>')
        if kind in "AB" or chosen or name == "random":
            lab[name] = (X(wv), Y(mv), c, chosen)
    for name, (x, y, c, chosen) in lab.items():
        txt = "Final hybrid" if chosen else ("Solution A" if name.startswith("A:") else "Solution B" if name.startswith("B:") else "Random 10")
        anchor = "end" if x > pl + iw * 0.7 else "start"
        dx = -12 if anchor == "end" else 12
        dy = -12 if chosen else (18 if txt == "Solution B" else 4)
        o.append(t(x + dx, y + dy, txt, 12.5, c if not chosen else C["text"], anchor, 800))
    return "".join(o)


def ptop_bars(rows, w, h, col, key="p_top10"):
    rowh = h / len(rows); o = []
    for i, r in enumerate(rows):
        y = i * rowh
        v = r[key]
        o.append(t(0, y + rowh / 2 + 5, f'{r["rank"]}. {r["player"]}', 13, C["text"], weight=600))
        x0 = 186; bw = (w - x0 - 120) * v / 100
        o.append(f'<rect x="{x0}" y="{y + rowh / 2 - 9:.1f}" width="{w - x0 - 120}" height="18" rx="4" fill="{GRID}"/>')
        o.append(f'<rect x="{x0}" y="{y + rowh / 2 - 9:.1f}" width="{bw:.1f}" height="18" rx="4" fill="{col}"/>')
        o.append(t(x0 + bw + 6, y + rowh / 2 + 5, f"{v}%", 12.5, C["text"], weight=800))
        sp = f'{r["specs"]}/{r["n_specs"]}'
        o.append(t(w - 4, y + rowh / 2 + 5, sp, 12.5, C["muted"], "end", 700))
    return "".join(o)


def phase_strip(phases, w, h, col, mode="bat"):
    """Three mini bars: share of pressure balls per phase with value label."""
    o = []; names = [("PP", "PP"), ("MID", "MID"), ("DEATH", "DTH")]
    bw = (w - 16) / 3
    for i, (k, lab) in enumerate(names):
        p = phases[k]; x = i * (bw + 8)
        share = p["share"]; hh = (h - 30) * share / 100
        o.append(f'<rect x="{x:.1f}" y="{0}" width="{bw:.1f}" height="{h - 30}" rx="4" fill="{GRID}"/>')
        o.append(f'<rect x="{x:.1f}" y="{h - 30 - hh:.1f}" width="{bw:.1f}" height="{hh:.1f}" rx="4" fill="{col}"/>')
        o.append(t(x + bw / 2, h - 16, lab, 10.5, C["muted"], "middle", 700))
        o.append(t(x + bw / 2, h - 3, f"{share}%", 10.5, C["text"], "middle", 700))
    return "".join(o)


def hist(hd, w, h, cut):
    pl, pr, pt, pb = 40, 10, 10, 34
    iw, ih = w - pl - pr, h - pt - pb
    cnt = hd["counts"]; ed = hd["edges"]; mx = max(cnt)
    o = []
    for v in _ticks(0, mx, 4):
        y = pt + ih - v / mx * ih
        if v <= mx:
            o.append(f'<line x1="{pl}" x2="{pl + iw}" y1="{y:.1f}" y2="{y:.1f}" stroke="{GRID}"/>' + t(pl - 6, y + 4, f"{int(v / 1000)}k" if v else "0", 10.5, anchor="end"))
    bw = iw / len(cnt)
    for i, c_ in enumerate(cnt):
        hh = c_ / mx * ih
        col = C["pink"] if ed[i] >= cut - 1e-9 else "#4a3f5c"
        o.append(f'<rect x="{pl + i * bw + .5:.1f}" y="{pt + ih - hh:.1f}" width="{bw - 1:.1f}" height="{hh:.1f}" rx="1.5" fill="{col}"/>')
    for v in (0, 1, 2, 3, 4):
        o.append(t(pl + v / 4 * iw, h - 16, f"{v}{'+' if v == 4 else ''}", 10.5, anchor="middle"))
    o.append(t(pl + iw / 2, h - 2, "Pressure Index (1 = average ball)", 11, anchor="middle"))
    xc = pl + cut / 4 * iw
    o.append(f'<line x1="{xc:.1f}" x2="{xc:.1f}" y1="{pt}" y2="{pt + ih}" stroke="{C["pink"]}" stroke-dasharray="4 4"/>' + t(xc + 6, pt + 14, f"top 30% ≥ {cut:.2f}", 11, C["pink"], weight=700))
    return "".join(o)


def season_bars(seasons, w, h, col):
    pl, pr, pt, pb = 40, 10, 20, 44
    iw, ih = w - pl - pr, h - pt - pb
    vals = [s["v"] for s in seasons]; lo = min(0, min(vals)) - 5; hi = max(vals) + 10
    Y = lambda v: pt + ih - (v - lo) / (hi - lo) * ih
    o = []
    for v in _ticks(lo, hi, 4):
        if lo <= v <= hi:
            o.append(f'<line x1="{pl}" x2="{pl + iw}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="{GRID if v else C["faint"]}"/>' + t(pl - 6, Y(v) + 4, f"{v:+.0f}" if v else "0", 10.5, anchor="end"))
    bw = iw / len(seasons) * 0.5
    for i, s in enumerate(seasons):
        cx = pl + iw / len(seasons) * (i + .5)
        o.append(f'<rect x="{cx - bw / 2:.1f}" y="{min(Y(s["v"]), Y(0)):.1f}" width="{bw:.1f}" height="{abs(Y(s["v"]) - Y(0)):.1f}" rx="4" fill="{col}"/>')
        o.append(t(cx, Y(s["v"]) - 7, f'{s["v"]:+.1f}', 12.5, C["text"], "middle", 800))
        o.append(t(cx, h - 24, s["y"], 12.5, C["text"], "middle", 700))
        o.append(t(cx, h - 8, f'{s["pb"]} balls · SR {s["sr"]:.0f}', 10.5, C["muted"], "middle"))
    return "".join(o)
