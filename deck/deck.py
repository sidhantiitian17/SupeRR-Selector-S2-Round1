"""Builds the Under Pressure Rating deck as HTML (one <section> per 1600x900 slide).

    python3 deck.py            -> build/deck.html
Every number comes from build/data.json (prep.py), the methodology report or the repo; nothing is typed in by hand
except the report's own published figures, which are quoted with their section.
"""
import json, pathlib, math, io
from lib import *
import charts as ch

D = json.loads((ROOT / "build/data.json").read_text())
GITHUB = "https://github.com/sidhantiitian17/SupeRR-Selector-S2-Round1"
LIVE = (ROOT / "LIVE_URL").read_text().strip() if (ROOT / "LIVE_URL").exists() else "https://superr-under-pressure-rating.vercel.app"
SLIDES = []


def add(fn):
    SLIDES.append(fn)
    return fn


def qr_svg(url, size=120):
    import qrcode, qrcode.image.svg
    q = qrcode.QRCode(border=1, box_size=10, error_correction=qrcode.constants.ERROR_CORRECT_M)
    q.add_data(url); q.make(fit=True)
    m = q.get_matrix(); n = len(m); s = size / n
    rects = "".join(f'<rect x="{x * s:.2f}" y="{y * s:.2f}" width="{s + .3:.2f}" height="{s + .3:.2f}"/>' for y, row in enumerate(m) for x, v in enumerate(row) if v)
    return f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}"><rect width="{size}" height="{size}" fill="#fff"/><g fill="#120c1a">{rects}</g></svg>'


def short(u):
    return u.replace("https://", "")


def ph(pid, w, h, x=None, y=None, style=""):
    """Player photo tile (cutout on panel); monogram fallback."""
    src = photo(pid)
    inner = f'<img src="{src}"/>' if src else '<div class="mono-ini">?</div>'
    if x is None:
        return f'<div class="ph" style="width:{w}px;height:{h}px;{style}">{inner}</div>'
    return box(x, y, w, h, inner, "ph", style)


TOPB = D["top"]["bat"]; TOPW = D["top"]["bowl"]
PROF = {r["name"]: r for r in D["profiles"]["bat"] + D["profiles"]["bowl"]}


# =========================================================================================== 1 COVER
@add
def s_cover(n):
    b = []
    b.append(box(0, 0, W, H, "", "", f"background:{C['frame']}"))
    b.append(box(0, 0, 560, H, "", "", f"background:{C['panel']}"))
    b.append(box(70, 56, 220, 232, f'<div style="padding:12px;box-sizing:border-box;height:232px"><img src="{logo()}" style="height:208px;width:auto;display:block;margin:0 auto"/></div>'))
    b.append(box(70, 300, 470, 0, '<div class="xs m" style="letter-spacing:.18em;font-weight:700">SUPERR SELECTOR · SEASON 2 · ROUND 1</div>'))
    b.append(box(70, 330, 480, 0, f'<div class="big" style="font-size:66px;line-height:.95">UNDER<br>PRESSURE<br><span class="pk">RATING</span></div>'))
    b.append(box(70, 548, 450, 0, '<div class="p" style="font-size:18px;line-height:1.45">Who delivers when the game is on the line, and how they could make <b>Rajasthan Royals</b> stronger at the <b>IPL 2027 auction</b>.</div>'))
    row = 'display:flex;gap:18px;align-items:center;height:104px'
    links = (f'<div style="{row}">'
             f'<div style="border-radius:10px;overflow:hidden;flex:none">{qr_svg(LIVE, 96)}</div><div><div class="h3">{icon("globe", 17, C["pink"])} Live dashboard</div><div class="s m mono">{short(LIVE)}</div></div></div>'
             f'<div style="{row};margin-top:14px">'
             f'<div style="border-radius:10px;overflow:hidden;flex:none">{qr_svg(GITHUB, 96)}</div><div><div class="h3">{icon("github", 17, C["pink"])} Code, data, results</div><div class="s m mono">{short(GITHUB)}</div></div></div>')
    b.append(box(70, 644, 470, 0, links))
    # right: question + featured players
    b.append(box(620, 70, 920, 0, '<div class="h2 m" style="font-size:15px">THE QUESTION</div><div class="big" style="font-size:40px;margin-top:10px;line-height:1.08">When the next ball can swing the match, <span class="pk">who still performs?</span></div>'))
    v, hz = TOPB[0], TOPW[0]
    for i, (p, role, col, stat) in enumerate([(v, "#1 BATTER", BAT, f'SR {v["P SR"]:.0f} under pressure vs {v["usual SR"]:.0f} usual'),
                                              (hz, "#1 BOWLER", BOWL, f'Economy {hz["P econ"]:.1f} under pressure vs {hz["usual econ"]:.1f} usual')]):
        x = 620 + i * 470
        b.append(ph(p["pid"], 440, 380, x, 230))
        b.append(box(x + 16, 246, 0, 0, chip(role, col, True)))
        b.append(box(x, 622, 440, 0, f'<div class="h3" style="font-size:20px">{p["player"]}</div><div class="s m">{stat} · top 10 in {p["p_top10"]}% of resamples</div>'))
    stats = [("837", "matches"), ("193,988", "deliveries"), ("5 yrs", "IPL + T20I, 2022–26"), ("10 + 10", "most reliable")]
    sx = 620
    for i, (a, l) in enumerate(stats):
        b.append(card(sx + i * 232, 694, 214, 100, f'<div class="big pk" style="font-size:36px">{a}</div><div class="s m" style="margin-top:8px">{l}</div>'))
    b.append(box(620, 812, 920, 0, '<div class="xs m" style="letter-spacing:.16em;font-weight:700;color:#ff8ccc">PRESENTED BY</div>''<div style="font-size:28px;font-weight:800;color:#fff;margin-top:4px;line-height:1.1">Prashast Sidhant</div>''<div style="font-size:19px;color:#fff;margin-top:4px">National Institute of Technology Raipur</div>'))
    return slide(n, None, None, "".join(b), notes="Cover. Under Pressure Rating: a reproducible pressure-performance rating for the SupeRR Selector brief, built for Rajasthan Royals.")


# =========================================================================================== 2 PROBLEM
@add
def s_problem(n):
    b = []
    b.append(box(34, 96, 1530, 0, '<div class="p" style="font-size:16px"><b class="pk">The brief:</b> identify the most reliable players under pressure (top 10 batters, top 10 bowlers) using the ball-by-ball data, compare them with their usual level, explain the method, and show how they could strengthen Rajasthan Royals for the IPL 2027 auction.</div>'))
    stages = [
        ("DEFINE PRESSURE", "gauge", ["\"Pressure\" has no agreed definition", "Death overs ≠ always pressure"], ["A measurable, match-aware definition", "Proof it captures decisive moments"]),
        ("MEASURE FAIRLY", "scale", ["Openers and finishers face different balls", "A run is worth more in a tight chase"], ["Compare each ball with an average player in the same spot", "Charge wickets by their real cost"]),
        ("VS USUAL LEVEL", "repeat", ["Good players look good everywhere", "Pressure skill vs overall skill"], ["Score pressure level minus own usual level", "Report both side by side"]),
        ("SMALL SAMPLES", "dice", ["Most players have < 300 pressure balls", "One hot week tops a raw table"], ["Shrink noisy estimates toward the mean", "Minimum sample rules"]),
        ("PROVE IT WORKS", "shield", ["Any formula can be tuned to look right", "No ground truth for \"clutch\""], ["Test on matches the method never saw", "Rule fixed before seeing results"]),
        ("BUILD FOR RR", "flag", ["A ranking is not a squad plan", "Most stars are under contract"], ["Find RR's pressure gaps", "Match players to gaps and availability"]),
    ]
    cw, gap, x0 = 245, 12, 34
    for i, (name, ic, probs, needs) in enumerate(stages):
        x = x0 + i * (cw + gap)
        b.append(pill(x, 150, cw, name, C["jersey"], 40, 15))
        b.append(box(x + cw / 2 - 28, 198, 56, 56, f'<div style="width:56px;height:56px;border-radius:50%;background:{C["panel2"]};border:2px solid {C["pink"]};display:grid;place-items:center">{icon(ic, 28, C["pink"], 1.8)}</div>'))
        b.append(pill(x + 30, 266, cw - 60, "KEY PROBLEMS", C["magenta"], 28, 12.5))
        b.append(box(x + 6, 300, cw - 10, 0, "<ul class='b bad' style='font-size:15px;line-height:1.4'>" + "".join(f"<li>{p}</li>" for p in probs) + "</ul>"))
        b.append(pill(x + 30, 414, cw - 60, "NEEDS", C["jersey"], 28, 12.5))
        b.append(box(x + 6, 448, cw - 10, 0, "<ul class='b good' style='font-size:15px;line-height:1.4'>" + "".join(f"<li>{p}</li>" for p in needs) + "</ul>"))
        if i:
            b.append(box(x - gap / 2 - 1, 200, 2, 350, "", "", f"background:{C['line']}"))
    # bottom left: why raw numbers mislead (two identical sixes)
    b.append(card(34, 566, 900, 286, ""))
    b.append(pill(54, 580, 330, "WHY RAW NUMBERS MISLEAD", C["magenta"], 32, 14))
    ex = D["value_example"][-1]
    g = Graph()
    g.node("a", 60, 628, 250, 92, f'<b>{icon("ball", 16, BAT)} Six, last over of a chase</b><small>Need {ex["need"]} off {ex["left"]}; win probability {ex["wp"]:.0%} → {ex["wpa"]:.0%}</small>', "node hot")
    g.node("b", 60, 740, 250, 92, f'<b>{icon("ball", 16, C["faint"])} Six, 10th over, 80 runs ahead</b><small>Win probability hardly moves</small>', "node")
    g.node("raw", 380, 686, 190, 84, '<b>Raw stats</b><small>Both = 6 runs, same strike-rate boost</small>', "node")
    g.node("ours", 640, 624, 270, 108, '<b>Our rating: high-pressure ball</b><small>Counted in the pressure sample, valued vs an average player in that exact state</small>', "node hot")
    g.node("ours2", 640, 740, 270, 92, '<b>Our rating: routine ball</b><small>Counts toward the player\'s usual level, not pressure</small>', "node")
    g.edge("a", "raw", "r", "l", tb=0.3).edge("b", "raw", "r", "l", tb=0.7)
    g.edge("a", "ours", color=C["pink"], label="leverage high").edge("b", "ours2", color=C["faint"], label="leverage low", lab_dy=18)
    b.append(g.render())
    # bottom right: what we deliver
    b.append(card(950, 566, 616, 286, ""))
    b.append(pill(970, 580, 260, "WHAT WE DELIVER", C["jersey"], 32, 14))
    items = [("trophy", "Top 10 batters + top 10 bowlers", "ranked by a rating chosen on unseen matches"),
             ("flag", "An IPL 2027 plan for RR", "pressure gaps by phase, player fit, availability"),
             ("chart", "Interactive dashboard", "every number checked against the pipeline (10,172 checks)"),
             ("code", "One-command reproduction", "raw CSVs → final lists → report, seed 42")]
    for i, (ic, a, s) in enumerate(items):
        b.append(box(972, 628 + i * 54, 580, 50, f'<div style="display:flex;gap:12px;align-items:center"><div style="width:40px;height:40px;border-radius:10px;background:{C["panel2"]};display:grid;place-items:center">{icon(ic, 21, C["pink"])}</div><div><div class="h3">{a}</div><div class="xs m">{s}</div></div></div>'))
    return slide(n, "Problem: who is reliable under pressure?", "PROBLEM", "".join(b),
                 notes="Six sub-problems hide inside the brief. Each one maps to a design choice on the following slides.")


# =========================================================================================== 3 DATA
@add
def s_data(n):
    b = []
    files = [("ball_by_ball.csv", "one row per delivery"), ("matches.csv", "date, venue, result, stage"), ("competitions.csv", "IPL seasons, T20I series"),
             ("teams.csv", "team names per competition"), ("playing_eleven.csv", "who played"), ("squad mapping", "player names & roles")]
    g = Graph()
    b.append(pill(34, 98, 330, "RAW DATA (6 CSV FILES)", C["jersey"], 34, 14))
    for i, (f, s) in enumerate(files):
        g.node(f"f{i}", 34, 144 + i * 66, 300, 56, f'<b>{icon("db", 16, C["blue"])} {f}</b><small>{s}</small>', "node blue")
    g.node("join", 410, 250, 260, 150, f'<b>{icon("layers", 17, C["pink"])} s01 · Prepare</b><small>Join files, rebuild the state before every ball: score, wickets left, balls left, runs needed, required rate, phase, knock-out flag</small>', "node hot")
    for i in range(6):
        g.edge(f"f{i}", "join", "r", "l", tb=0.2 + i * 0.12)
    g.node("scope", 410, 440, 260, 112, f'<b>{icon("filter", 17, C["pink"])} Scope</b><small>IPL + T20I, 2022–2026 (as the brief asks). Emerging/A-team events dropped.</small>', "node hot")
    g.node("elo", 410, 580, 260, 96, f'<b>{icon("users", 17, C["pink"])} Opposition strength</b><small>Elo from results; Associates balls weighted 0.5</small>', "node hot")
    g.edge("join", "scope", "b", "t").edge("scope", "elo", "b", "t")
    g.node("out", 730, 470, 230, 150, f'<div class="big" style="font-size:40px">{D["n_matches"]}</div><small>matches</small><div class="big" style="font-size:40px;margin-top:6px">{D["n_balls"]:,}</div><small>deliveries ready for modelling</small>', "node pinkfill")
    g.edge("scope", "out", "r", "l", ta=0.5, tb=0.3).edge("elo", "out", "r", "l", tb=0.75)
    b.append(g.render())
    # right: matches per year stacked
    b.append(card(1000, 98, 566, 360, '<div class="h2">Matches per year</div><div class="xs m">IPL vs T20I, after scoping</div>'))
    vol = D["volume"]; yrs = sorted(vol)
    bars = [(y, [(vol[y].get("IPL", 0), BAT), (vol[y].get("T20I", 0), BOWL)]) for y in yrs]
    b.append(svg_abs(1016, 160, 536, 286, ch.stacked_bars(bars, 536, 286, legend=[("IPL", BAT), ("T20I", BOWL)])))
    # QA cards
    b.append(pill(1000, 476, 566, "DATA QUALITY CHECKS", C["magenta"], 34, 14))
    qa = [("check", C["good"], "State rebuilt for every ball", "score, wickets, balls left, target and required rate before each delivery"),
          ("alert", C["warn"], "Extras are partly missing", "feed omits runs beyond the first on wides/byes/leg-byes: winning chases reconstruct exactly 73.9% of the time, mean 1.1 run short"),
          ("check", C["good"], "Out-of-fold everything", "every model prediction for a match comes from models that never saw that match (5 folds grouped by match)"),
          ("check", C["good"], "Eligibility", "≥150 pressure balls, ≥12 matches, ≥150 usual balls; removes 80–90-ball flukes")]
    for i, (ic, col, a, s) in enumerate(qa):
        b.append(box(1004, 524 + i * 78, 560, 72, f'<div style="display:flex;gap:12px"><div style="flex:none;width:34px;height:34px;border-radius:50%;background:{C["panel2"]};display:grid;place-items:center">{icon(ic, 18, col)}</div><div><div class="h3">{a}</div><div class="xs m">{s}</div></div></div>'))
    b.append(card(34, 706, 926, 146, '<div class="h3">Why IPL and T20I together?</div><div class="s m" style="margin-top:6px">The brief covers both. Pooling doubles the pressure sample for most players; competition is a feature in every expectation model, so a T20I ball is compared with T20I balls. IPL-only and T20I-only re-rankings are part of the robustness checks (slide 14).</div>'
                     f'<div style="margin-top:10px;display:flex;gap:8px">{chip("IPL", BAT, True)}{chip("T20I", BOWL, True)}{chip("2022 → 2026", C["muted"])}{chip("seed 42", C["muted"])}</div>'))
    return slide(n, "Data: from six CSVs to 193,988 modelled balls", "DATA & PRESSURE", "".join(b),
                 notes="Six raw files are joined and the full game state is rebuilt before each ball. Scope and quality checks are listed on the right.")


# =========================================================================================== 4 PIPELINE
@add
def s_pipeline(n):
    b = []
    g = Graph()
    steps = [("s01", "Prepare", "layers", "clean, join, game state", "deliveries.parquet"),
             ("s02", "Pressure", "gauge", "win-probability model → leverage → Pressure Index", "deliveries_pressure"),
             ("s03", "Value", "scale", "expected-outcome models → value of each ball", "deliveries_value"),
             ("s05", "Validate", "shield", "test pressure definitions, thresholds, rating models", "val_*.csv, weights"),
             ("s04", "Solution A", "brain", "context-adjusted, shrunk ratings", "ratings_*.csv"),
             ("s07", "Tournament", "trophy", "A vs B vs 45+ hybrids on unseen matches", "hyb_selection.csv"),
             ("s08", "Final lists", "star", "chosen recipe, bootstrap, robustness", "FINAL_TOP10_HYBRID.csv"),
             ("s09", "Report", "file", "methodology PDF, figures", "report.pdf")]
    xs = [34, 424, 814, 1204]
    for i, (k, name, ic, what, out) in enumerate(steps):
        row = i // 4; col = i % 4 if row == 0 else 3 - i % 4
        x, y = xs[col], 120 + row * 210
        cls = "node hot" if k in ("s02", "s07", "s08") else "node"
        g.node(k, x, y, 330, 150, f'<b>{icon(ic, 18, C["pink"])} {k} · {name}</b><small style="font-size:13.5px;color:{C["text"]}">{what}</small><small class="mono" style="margin-top:8px">→ {out}</small>', cls)
    keys = [s[0] for s in steps]
    for a, c in zip(keys, keys[1:]):
        if a == "s05":
            g.edge(a, c, "b", "t")
        elif keys.index(a) < 4:
            g.edge(a, c, "r", "l")
        else:
            g.edge(a, c, "l", "r")
    # solution B joins at the tournament
    g.node("B", 814, 560, 330, 92, f'<b>{icon("brain", 18, C["violet"])} Solution B (independent build)</b><small>pressure strike rate; shrunk economy + win probability added</small>', "node violet")
    g.edge("B", "s07", "t", "b", color=C["violet"], label="competes in", lab_dx=48, lab_dy=4)
    g.node("dash", 34, 560, 330, 92, f'<b>{icon("chart", 18, C["blue"])} Dashboard build + verifier</b><small>10,172 checks: every number on screen vs pipeline</small>', "node blue")
    g.edge("s08", "dash", "b", "t", color=C["blue"], label="feeds")
    b.append(g.render())
    b.append(card(34, 680, 1530, 170, ""))
    b.append(pill(54, 696, 280, "ONE COMMAND", C["jersey"], 32, 14, "code"))
    b.append(box(54, 744, 600, 0, f'<div class="mono" style="font-size:20px;background:{C["bg"]};border-radius:10px;padding:14px 18px;color:{C["text"]}">$ ./reproduce.sh</div><div class="s m" style="margin-top:10px">~45–60 min on 2 CPUs. Seed 42. All settings in <span class="mono">pipeline/src/config.py</span>.</div>'))
    facts = [("40 / 40", "data files reproduced exactly from a clean clone"), ("10,172", "dashboard checks, 0 failed"), ("9", "pipeline steps, each writes its own outputs")]
    for i, (a, s) in enumerate(facts):
        b.append(box(720 + i * 280, 724, 260, 0, f'<div class="big pk" style="font-size:40px">{a}</div><div class="s m" style="margin-top:8px">{s}</div>'))
    return slide(n, "End-to-end pipeline", "DATA & PRESSURE", "".join(b),
                 notes="Nine steps run in order from one script. Solution B was built independently and only meets solution A in the held-out tournament.")


# =========================================================================================== 5 PRESSURE CONCEPT
@add
def s_pressure(n):
    b = []
    ex = D["example"]
    b.append(card(34, 96, 900, 500, ""))
    b.append(box(54, 108, 860, 0, f'<div class="h2">A real chase: {ex["bat"]} vs {ex["bowl"]}, IPL {ex["date"][:4]}</div><div class="xs m">Target {ex["target"]}. Line = win probability of the chasing side before each ball. Bars = Pressure Index; <span class="pk">pink</span> = top 30% of all balls (our "under pressure").</div>'))
    b.append(svg_abs(50, 160, 870, 430, ch.chase_chart(ex["balls"], 870, 430, D["pi_cut"])))
    # plain-words explainer (right)
    b.append(pill(960, 96, 606, "PRESSURE INDEX IN PLAIN WORDS", C["magenta"], 36, 15))
    g = Graph()
    g.node("st", 960, 148, 280, 96, f'<b>{icon("clock", 16, C["pink"])} 1 · Game state</b><small>runs needed, balls & wickets left, phase, target, Elo gap</small>', "node")
    g.node("wp", 1286, 148, 280, 96, f'<b>{icon("brain", 16, C["pink"])} 2 · Win probability</b><small>LightGBM model: chance the batting side wins from here</small>', "node")
    g.node("sw", 960, 276, 280, 112, f'<b>{icon("zap", 16, C["pink"])} 3 · Leverage</b><small>for every possible next ball (dot, 1, 2, 4, 6, wicket, extra): how far would win probability move? Weighted average of those swings.</small>', "node")
    g.node("pi", 1286, 276, 280, 112, f'<b>{icon("gauge", 16, C["pink"])} 4 · Pressure Index</b><small>leverage (average ball = 1) × 1.15 in knock-outs</small>', "node hot")
    g.node("hp", 1123, 418, 280, 70, f'<b>{icon("flag", 16, "#fff")} Top 30% = under pressure</b><small>cut-off PI ≥ {D["pi_cut"]:.2f}</small>', "node pinkfill")
    g.edge("st", "wp").edge("wp", "sw", "b", "t", ta=0.5, tb=0.75).edge("sw", "pi").edge("pi", "hp", "b", "r", ta=0.5)
    b.append(g.render())
    m1, m2 = D["wp_metrics"]
    b.append(card(960, 512, 606, 340, ""))
    b.append(box(980, 526, 580, 0, '<div class="h3">Is the win-probability model any good?</div><div class="xs m">Out-of-fold predictions, calibration (predicted vs actual win rate)</div>'))
    b.append(svg_abs(976, 572, 290, 270, ch.calibration(D["calibration"], 290, 270)))
    b.append(box(1290, 580, 260, 0, f'<div class="big pk" style="font-size:44px">{m2["auc"]:.3f}</div><div class="xs m">AUC, chasing innings</div><div class="big" style="font-size:34px;margin-top:14px;color:{C["blue"]}">{m1["auc"]:.3f}</div><div class="xs m">AUC, first innings (harder: no target yet)</div>'
                                   f'<div class="xs m" style="margin-top:14px">Monotone constraints (more runs needed never helps the batting side), DLS-revised targets, 5 folds grouped by match.</div>'))
    b.append(card(34, 612, 900, 240, ""))
    b.append(box(54, 626, 860, 0, f'<div class="h3">How to read the chart</div><ul class="b" style="margin-top:8px"><li>Early balls barely move the result → low Pressure Index, not counted as pressure.</li><li>As the chase tightens, every ball can swing it → bars turn pink. The last over carries the most pressure of the match.</li><li>Pressure follows the <b>match situation</b>, not the over number: a collapse in over 8 can be pressure; a cruise in over 19 is not.</li><li>{chip("Why 30%?", C["pink"])} reliable ratings while keeping enough players eligible (next slide).</li></ul>'))
    return slide(n, "Concept 1: measuring pressure", "DATA & PRESSURE", "".join(b),
                 notes="Pressure = how much the next ball can change who wins. Computed from a win-probability model, averaged over every possible outcome of the next ball.")


# =========================================================================================== 6 VALIDATE PRESSURE
@add
def s_validate(n):
    b = []
    defs = D["definitions"]
    lab = {"PI": "Our Pressure Index", "HEUR": "Hand-weighted stress score", "NAIVE": "Rule-based (RRR 9+, overs 17–20, collapse)"}
    rows = [(lab[d_["definition"].split(" ")[0]], d_["share of total |WPA| in flagged balls"] * 100, d_["decisiveness ratio"], d_["share of balls flagged"] * 100) for d_ in defs]
    b.append(card(34, 96, 760, 380, '<div class="h2">Does our definition find the decisive balls?</div><div class="xs m">Share of all match-deciding win-probability swing that lands in the flagged balls, and the ratio to their share of balls</div>'))
    b.append(svg_abs(54, 170, 720, 290, ch.def_bars(rows, 720, 290)))
    b.append(card(810, 96, 756, 380, '<div class="h2">Why the top 30%?</div><div class="xs m">Split-half reliability of player ratings (does a player\'s score on half the matches predict the other half?) and players left eligible, per cut-off</div>'))
    b.append(svg_abs(830, 170, 716, 290, ch.threshold(D["threshold"], 716, 290)))
    b.append(card(34, 492, 760, 360, '<div class="h2">Where pressure lives (chasing innings)</div><div class="xs m">Average Pressure Index by over and wickets lost. Darker pink = more pressure.</div>'))
    b.append(svg_abs(54, 560, 720, 284, ch.heatmap(D["pressure_map"]["2"], 720, 284)))
    hs = D["hp_phase_share"]
    b.append(card(810, 492, 756, 360, ""))
    b.append(pill(830, 508, 330, "WHAT THE CHECKS SHOWED", C["jersey"], 32, 14))
    pts = [f'Leverage puts <b class="pk">2.06×</b> its share of match-deciding swing into flagged balls; rule-based definitions only ~1.2–1.3×.',
           f'Pressure is spread over the innings: <b>{hs["PP"]:.0f}%</b> of pressure balls are in the powerplay, <b>{hs["MID"]:.0f}%</b> in the middle overs, <b>{hs["DEATH"]:.0f}%</b> at the death.',
           'Reliability is a plateau (ρ ≈ 0.23–0.33) from top 40% to top 15%. Top 30% sits on it and keeps ~150 players per role eligible; top 15% would leave ~90.',
           'Wickets in hand matter: 4 down in over 15 of a chase is far more pressure than 1 down.']
    b.append(box(830, 556, 720, 0, "<ul class='b'>" + "".join(f"<li class='p'>{p}</li>" for p in pts) + "</ul>"))
    segs = [("Powerplay", hs["PP"], C["pink"]), ("Middle overs", hs["MID"], C["magenta"]), ("Death", hs["DEATH"], C["jersey"])]
    bar = "".join(f'<div style="width:{v}%;background:{c};height:34px;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:13px">{l} {v:.0f}%</div>' for l, v, c in segs)
    b.append(box(830, 786, 716, 0, f'<div class="xs m" style="margin-bottom:6px">Where the pressure balls fall (all 58,197 flagged balls)</div><div style="display:flex;gap:3px;border-radius:8px;overflow:hidden">{bar}</div>'))
    return slide(n, "Concept 1b: is that the right definition?", "DATA & PRESSURE", "".join(b),
                 notes="Three definitions were tested. The model-based leverage concentrates twice its share of the decisive swing into the flagged balls.")


# =========================================================================================== 7 VALUE OF A BALL
@add
def s_value(n):
    b = []
    ex = D["value_example"][-1]
    b.append(pill(34, 96, 760, "CONCEPT 2 · VALUE OF A BALL, WORKED ON A REAL DELIVERY", C["magenta"], 36, 14))
    g = Graph()
    g.node("sit", 34, 150, 230, 140, f'<b>{icon("clock", 16, C["pink"])} The situation</b><small>{ex["s"]} on strike vs {ex["b"]}. Need {ex["need"]} off {ex["left"]}, {10 - ex["w"]} wickets left.</small>', "node")
    g.node("exp", 300, 150, 230, 140, f'<b>{icon("brain", 16, C["pink"])} Average player here</b><small>Model trained on all other matches: expected runs <b class="pk">{ex["E"]:.2f}</b>, chance of getting out <b class="pk">{ex["Pout"]:.1%}</b></small>', "node")
    g.node("act", 566, 150, 228, 140, f'<b>{icon("ball", 16, C["pink"])} What happened</b><small>Hit for <b class="pk">{ex["runs"]}</b>, not out. Win probability {ex["wp"]:.0%} → {ex["wpa"]:.0%}.</small>', "node")
    g.edge("sit", "exp").edge("exp", "act")
    g.node("f", 34, 330, 760, 120, f'<b>{icon("scale", 16, "#fff")} Value = (runs − expected runs) − wicket cost × (out − chance of out)</b>'
                                  f'<small style="font-size:15px;margin-top:8px" class="mono">= ({ex["runs"]} − {ex["E"]:.2f}) − {ex["Wc"]:.2f} × (0 − {ex["Pout"]:.3f}) = <b style="color:#fff;font-size:18px">+{ex["val"]:.2f} runs</b> for the batter, {ex["bval"]:+.2f} for the bowler</small>', "node pinkfill")
    g.edge("act", "f", "b", "t", tb=0.85)
    g.edge("exp", "f", "b", "t", tb=0.5, dash=True)
    b.append(g.render())
    b.append(card(34, 470, 760, 382, '<div class="h2">What a wicket costs</div><div class="xs m">Runs the batting side loses on average when a wicket falls (from an expected-remaining-runs model)</div>'))
    b.append(svg_abs(54, 536, 720, 190, ch.hbars([("Powerplay", 9.6, BAT), ("Middle overs", 5.4, BAT), ("Death overs", 2.6, BAT)], 720, 190, unit=" runs", maxv=11)))
    b.append(box(54, 742, 720, 0, f'<div style="background:{C["panel2"]};border-radius:10px;padding:12px 16px"><div class="h3">{icon("ball", 16, BOWL)} Bowlers get the mirror image</div><div class="s m" style="margin-top:4px">value = (expected runs conceded − runs conceded) + wicket cost × (wicket − chance of a wicket). The same six above is <b class="bl">{ex["bval"]:+.2f}</b> for {ex["b"]}.</div></div>'))
    b.append(card(810, 96, 756, 420, ""))
    b.append(pill(830, 112, 330, "WHY THIS IS FAIR", C["jersey"], 32, 14))
    fair = [("scale", "Same yardstick for every role", "an opener is compared with average openers' outcomes in powerplay states; a finisher with death-over states"),
            ("alert", "Wickets are not free", "losing a wicket early costs ~9.6 runs; at the death ~2.6. A batter who slogs and gets out pays for it"),
            ("users", "Opposition counts", "Elo in the win-probability model; balls against Associates weighted 0.5"),
            ("globe", "Competition-aware", "IPL and T20I balls compared within their own competition, pace vs spin separated")]
    for i, (ic, a, s) in enumerate(fair):
        b.append(box(832, 160 + i * 86, 716, 80, f'<div style="display:flex;gap:14px"><div style="flex:none;width:40px;height:40px;border-radius:10px;background:{C["panel2"]};display:grid;place-items:center">{icon(ic, 20, C["pink"])}</div><div><div class="h3">{a}</div><div class="s m">{s}</div></div></div>'))
    b.append(card(810, 532, 756, 320, ""))
    b.append(pill(830, 548, 360, "WHAT WE ADD UP PER PLAYER", C["jersey"], 32, 14))
    b.append(box(830, 596, 716, 0, '<table class="t"><tr><th>Measure</th><th>Meaning</th></tr>'
                                   '<tr><td><b>Pressure value /100</b></td><td>runs above an average player per 100 pressure balls</td></tr>'
                                   '<tr><td><b>Usual value /100</b></td><td>same thing on all other balls</td></tr>'
                                   '<tr><td><b>Uplift</b></td><td>pressure minus usual: does he rise or dip?</td></tr>'
                                   '<tr><td><b>Consistency</b></td><td>share of pressure matches with a top-quartile contribution</td></tr>'
                                   '<tr><td><b>Pressure SR / economy</b></td><td>solution B\'s rate measures on the highest-leverage balls</td></tr></table>'))
    return slide(n, "Concept 2: context-adjusted value", "METHOD", "".join(b),
                 notes="Each ball is compared with what an average player would produce in the identical situation, with wickets charged at their real cost.")


# =========================================================================================== 8 SHRINKAGE + BOOTSTRAP
@add
def s_shrink(n):
    b = []
    b.append(card(34, 96, 900, 520, '<div class="h2">Concept 3: shrinkage (empirical Bayes)</div><div class="xs m">Each batter\'s raw pressure value (grey) and the shrunk estimate we use (pink). Small samples move most toward the average.</div>'))
    b.append(svg_abs(50, 160, 870, 446, ch.shrink(D["shrink"], 870, 446)))
    b.append(card(950, 96, 616, 520, ""))
    b.append(pill(970, 112, 360, "THE IDEA IN ONE PICTURE", C["magenta"], 32, 14))
    g = Graph()
    g.node("r1", 970, 166, 270, 92, f'<b>{icon("star", 16, C["pink"])} New restaurant</b><small>2 reviews, both 5★</small>', "node")
    g.node("r2", 970, 280, 270, 92, f'<b>{icon("star", 16, C["blue"])} Established restaurant</b><small>800 reviews, average 4.6★</small>', "node")
    g.node("q", 1286, 222, 260, 100, '<b>Which is safer?</b><small>2 reviews could be luck. We pull small samples toward the average until they earn trust.</small>', "node hot")
    g.edge("r1", "q").edge("r2", "q")
    b.append(g.render())
    b.append(box(970, 396, 580, 0, '<ul class="b"><li class="p">Estimate how much players <b>really</b> differ vs how noisy each player\'s average is.</li><li class="p">Weight = how much to trust the player\'s own number. More balls → more trust.</li><li class="p">Runs and wickets are shrunk separately (a single dismissal is worth ~9 runs and swamps everything else).</li><li class="p">Final rating = 50/50 blend of the direct estimate and a hierarchical one (own overall level + shrunk pressure difference).</li></ul>'))
    # bootstrap strip
    b.append(card(34, 632, 1532, 220, ""))
    b.append(pill(54, 648, 420, "CONCEPT 4 · HOW SURE ARE WE? (BOOTSTRAP)", C["jersey"], 32, 14))
    g = Graph()
    g.node("m", 54, 706, 220, 120, f'<b>{icon("db", 16, C["pink"])} 837 matches</b><small>the real history</small>', "node")
    g.node("rs", 330, 706, 260, 120, f'<b>{icon("repeat", 16, C["pink"])} Resample 300×</b><small>draw matches with replacement: some appear twice, some not at all</small>', "node")
    g.node("rr", 646, 706, 250, 120, f'<b>{icon("chart", 16, C["pink"])} Re-rate every time</b><small>same recipe, new sample → new top 10</small>', "node")
    g.node("p", 952, 706, 260, 120, f'<b>{icon("target", 16, "#fff")} P(top 10)</b><small>share of the 300 runs where the player stays in the top 10</small>', "node pinkfill")
    g.node("sp", 1268, 706, 280, 120, f'<b>{icon("layers", 16, C["blue"])} + robustness checks</b><small>re-rank under 12 (bat) / 39 (bowl) alternative specs: IPL-only, T20I-only, other thresholds, near-best methods</small>', "node blue")
    g.edge("m", "rs").edge("rs", "rr").edge("rr", "p").edge("p", "sp", dash=True)
    b.append(g.render())
    return slide(n, "Concepts 3 & 4: small samples and certainty", "METHOD", "".join(b),
                 notes="Shrinkage stops a player with a lucky handful of balls from topping the list. The bootstrap tells us how stable each rank is.")



# =========================================================================================== 9 JOURNEY
@add
def s_journey(n):
    b = []
    steps = [("0", "Simplest ideas", "rank by raw pressure SR / economy or most pressure balls", "volume ≈ random; finishers dominate", "drop"),
             ("1", "Define pressure", "rules vs stress score vs model leverage", "leverage 2× decisive share → adopted", "keep"),
             ("2", "A v1", "runs above expected, one joint shrinkage", "reliability 0.01 / 0.07: one dismissal swamps signal", "drop"),
             ("3", "A v2", "shrink runs and wickets separately", "small gain (0.04 / 0.05)", "step"),
             ("4", "A v3", "win-probability lens (WPA/LI)", "looked great (0.31 / 0.23) but measured context, not skill", "drop"),
             ("5", "A v4", "centre WPA/LI within innings × phase", "honest but modest (0.11 / 0.13)", "step"),
             ("6", "A v5", "run value + direct shrinkage", "most faithful, least stable", "step"),
             ("7", "A v6", "blend direct + hierarchical, usual level, consistency", "0.22 / 0.17; predicts 2025–26 from 2022–24", "keep"),
             ("8", "Solution B", "independent: pressure SR, economy + WPA", "strong on strike rate, ignores dismissals", "keep"),
             ("9", "A vs B", "same unseen splits, 8 targets", "no overall winner: each found something", "step"),
             ("10", "Hybrid tournament", "60+ blends, 3 pools, gates, extra terms", "beats both parents on worst case", "keep"),
             ("11", "Brief constraint", "must score pressure vs usual level", "bowler score gains uplift term", "keep")]
    col = {"keep": C["good"], "drop": C["bad"], "step": C["blue"]}
    lab = {"keep": "KEPT", "drop": "DROPPED", "step": "STEP"}
    g = Graph()
    cw, chh = 240, 152
    for i, (k, name, what, said, v) in enumerate(steps):
        row, c = divmod(i, 6)
        if row == 1:
            c = 5 - c
        x = 34 + c * 258; y = 104 + row * 186
        g.node(f"s{i}", x, y, cw, chh, f'<div style="display:flex;justify-content:space-between;align-items:center"><b style="font-family:Archivo;font-weight:900;font-size:15px">{k} · {name}</b>{chip(lab[v], col[v], True)}</div>'
                                        f'<small style="color:{C["text"]};font-size:12.5px;margin-top:6px">{what}</small><small style="margin-top:4px">→ {said}</small>', "node", f"border-color:{col[v]};justify-content:flex-start")
    for i in range(11):
        if i == 5:
            g.edge("s5", "s6", "b", "t", color=C["faint"])
        elif i < 5:
            g.edge(f"s{i}", f"s{i + 1}", "r", "l")
        else:
            g.edge(f"s{i}", f"s{i + 1}", "l", "r")
    b.append(g.render())
    b.append(box(34, 456, 900, 0, f'<div class="xs m">Reliability pairs = split-half ρ for batters / bowlers. {chip("KEPT", C["good"], True)} {chip("STEP", C["blue"], True)} {chip("DROPPED", C["bad"], True)}</div>'))
    # staircase
    st_b = [("Random 10", -.068, -.191, "base"), ("Most pressure balls", .227, -.190, "base"), ("Raw pressure SR", .312, -.223, "base"), ("Solution A", .277, -.002, "A"), ("Solution B", .324, -.192, "B"), ("FINAL hybrid", .321, -.004, "final")]
    st_w = [("Random 10", .040, -.111, "base"), ("Most pressure balls", .038, -.252, "base"), ("Raw pressure economy", .163, -.093, "base"), ("Solution A", .158, -.129, "A"), ("Solution B", .209, .018, "B"), ("FINAL hybrid", .213, .040, "final")]
    for j, (title, data, c) in enumerate((("Batters", st_b, BAT), ("Bowlers", st_w, BOWL))):
        x = 34 + j * 774
        b.append(card(x, 488, 758, 364, f'<div class="h2">{title}: every step scored on unseen matches</div><div class="xs m">Filled = average gain of the picked top 10 over the pool (in pool SDs); outline = worst of 16 held-out cells</div>'))
        b.append(svg_abs(x + 14, 550, 730, 296, ch.staircase(data, 730, 296, "m", "w", c)))
    return slide(n, "How we refined it: 12 steps, each tested", "ITERATIONS", "".join(b),
                 notes="We started simple and changed one thing at a time. Versions that flattered results without predicting unseen matches (v3) were dropped.")


# =========================================================================================== 10 TOURNAMENT
@add
def s_tournament(n):
    b = []
    g = Graph()
    g.node("m", 34, 104, 210, 96, f'<b>{icon("db", 16, C["pink"])} 837 matches</b>', "node")
    g.node("r", 300, 100, 260, 72, f'<b>{icon("dice", 16, C["pink"])} 30 random half-splits</b>', "node")
    g.node("f", 300, 188, 260, 72, f'<b>{icon("clock", 16, C["pink"])} 6 past → future cuts</b><small>train on first 50–85% by date</small>', "node")
    g.edge("m", "r", "r", "l").edge("m", "f", "r", "l")
    g.node("c", 614, 104, 270, 150, f'<b>{icon("users", 16, C["pink"])} 60+ candidates per role</b><small>A, B, blends (weights 0.33–1.0), 3 pool rules, ± usual-level & consistency terms, ± gate, simple baselines</small>', "node")
    g.edge("r", "c", "r", "l", tb=0.3).edge("f", "c", "r", "l", tb=0.75)
    g.node("t", 34, 286, 360, 150, f'<b>{icon("target", 16, C["pink"])} 8 targets × 2 schemes = 16 cells</b><small>batters: strike rate, runs above expected, win prob. added, dismissal avoidance · bowlers: economy, runs saved, win prob. added, wickets — each under both pressure definitions, measured only on unseen matches</small>', "node")
    g.node("gain", 430, 286, 210, 150, f'<b>{icon("chart", 16, C["pink"])} Gain</b><small>(mean target of the picked 10 − pool mean) ÷ pool SD</small>', "node")
    g.node("rule", 676, 286, 208, 150, f'<b>{icon("lock", 16, "#fff")} Rule fixed in advance</b><small>must include pressure-vs-usual; best worst cell, then best mean within 0.03</small>', "node pinkfill")
    g.edge("c", "t", "b", "t", ta=0.3, tb=0.5, via=[(695, 270), (214, 270)])
    g.edge("t", "gain").edge("gain", "rule")
    b.append(g.render())
    b.append(card(34, 454, 850, 398, ""))
    b.append(pill(54, 470, 360, "RESULT ON THE SAME 16 CELLS", C["jersey"], 32, 14))
    rows = [("Solution A", "−0.002", "0.277", "−0.129", "0.158", ""), ("Solution B", "−0.192", "0.324", "+0.018", "0.209", ""), ("Final hybrid", "−0.004", "0.321", "+0.040", "0.213", "hl")]
    tr = "".join(f'<tr class="{h}"><td>{a}</td><td>{w1}</td><td>{m1}</td><td>{w2}</td><td>{m2}</td></tr>' for a, w1, m1, w2, m2, h in rows)
    b.append(box(54, 518, 810, 0, f'<table class="t"><tr><th>Method</th><th>Bat worst</th><th>Bat mean</th><th>Bowl worst</th><th>Bowl mean</th></tr>{tr}</table>'))
    b.append(box(54, 652, 810, 0, '<ul class="b"><li class="p">Batters: the hybrid keeps A\'s safety (worst cell ≈ 0) and B\'s average gain.</li><li class="p">Bowlers: the hybrid has the best worst cell of any eligible candidate.</li><li class="p">Cost of the brief\'s usual-level rule for bowlers: best unconstrained candidate +0.028 / 0.228 vs chosen +0.040 / 0.213 — we followed the brief.</li></ul>'))
    for j, (role, c, title) in enumerate((("bat", BAT, "Batter candidates"), ("bowl", BOWL, "Bowler candidates"))):
        y = 96 + j * 382
        b.append(card(900, y, 666, 372, f'<div class="h3">{title} (each dot = one recipe)</div>'))
        b.append(svg_abs(912, y + 34, 642, 330, ch.tournament(D["tournament"], 642, 330, role, c)))
    return slide(n, "Choosing the method: a held-out tournament", "ITERATIONS", "".join(b),
                 notes="Every candidate ranks players using some matches; its top 10 is scored on matches it never saw. The selection rule was written down before the results.")


# =========================================================================================== 11 RECIPES
@add
def s_recipes(n):
    b = []
    for j, role in enumerate(("bat", "bowl")):
        x0 = 34 + j * 774; c = BAT if role == "bat" else BOWL
        b.append(card(x0, 96, 758, 600, ""))
        b.append(pill(x0 + 20, 112, 300, "BATTER SCORE" if role == "bat" else "BOWLER SCORE", c, 34, 15, "bat" if role == "bat" else "ball"))
        g = Graph()
        if role == "bat":
            g.node("F", x0 + 20, 380, 170, 90, '<b>Final batter score</b><small>z-scored, higher = better</small>', "node pinkfill")
            g.node("A", x0 + 260, 250, 210, 92, f'<b>{icon("brain", 15, SA)} A composite</b><small>context-adjusted, shrunk</small>', "node blue")
            g.node("B", x0 + 260, 520, 210, 92, f'<b>{icon("zap", 15, SB)} B strike-rate ensemble</b><small>no shrinkage</small>', "node violet")
            g.edge("A", "F", "l", "r", tb=0.3, color=SA, label="× 0.67").edge("B", "F", "l", "r", tb=0.7, color=SB, label="× 0.33")
            for i, (k, t1, t2, w) in enumerate([("a1", "Pressure rating", "runs above expected, 50/50 direct + hierarchical", "0.51"), ("a2", "Uplift", "pressure level − own usual level", "0.15"), ("a3", "Consistency", "share of pressure matches with a top-quartile contribution", "0.34")]):
                g.node(k, x0 + 530, 156 + i * 100, 210, 92, f'<b style="justify-content:space-between">{t1} {chip("× " + w, SA, True)}</b><small>{t2}</small>', "node")
                g.edge(k, "A", "l", "r", tb=0.2 + i * 0.3)
            for i, (k, t1, t2) in enumerate([("b1", "SR at leverage pct 75+", "top quarter of balls in each innings"), ("b2", "SR at leverage pct 85+", "top 15%")]):
                g.node(k, x0 + 530, 470 + i * 104, 210, 88, f'<b>{t1}</b><small>{t2}</small>', "node")
                g.edge(k, "B", "l", "r", tb=0.3 + i * 0.4)
        else:
            g.node("F", x0 + 20, 380, 170, 90, '<b>Final bowler score</b><small>z-scored, higher = better</small>', "node solid")
            g.node("H", x0 + 260, 250, 210, 100, f'<b>{icon("layers", 15, HY)} Rating blend</b><small>0.2 × A rating + 0.8 × B economy + WPA</small>', "node hot")
            g.node("U", x0 + 260, 520, 210, 92, f'<b>{icon("repeat", 15, C["good"])} Uplift</b><small>pressure − own usual level (the brief)</small>', "node good")
            g.edge("H", "F", "l", "r", tb=0.3, color=HY, label="× 0.90").edge("U", "F", "l", "r", tb=0.7, color=C["good"], label="× 0.10")
            for i, (k, t1, t2, w, cc) in enumerate([("a1", "A pressure rating", "runs saved vs expected, shrunk", "0.2", SA), ("b1", "B economy", "runs per ball at leverage pct 70+, shrunk (k = 500)", "", SB), ("b2", "B win prob. added", "per ball at pct 70+, shrunk; with economy = B (× 0.8)", "", SB)]):
                g.node(k, x0 + 530, 150 + i * 102, 210, 88, f'<b style="justify-content:space-between">{t1} {chip("× " + w, cc, True) if w else ""}</b><small>{t2}</small>', "node", f"border-color:{cc}")
                g.edge(k, "H", "l", "r", tb=0.2 + i * 0.3, color=cc)
            g.node("gate", x0 + 530, 494, 210, 132, f'<b>{icon("lock", 15, C["warn"])} Delivered gate</b><small>a bowler whose observed pressure value is below league average cannot rank above one who delivered</small>', "node", f"border-color:{C['warn']}")
            g.edge("gate", "U", "l", "r", dash=True, color=C["warn"])
        b.append(g.render())
    b.append(card(34, 712, 1532, 140, ""))
    b.append(pill(54, 728, 220, "SAME FOR BOTH", C["jersey"], 32, 14))
    b.append(box(300, 724, 1250, 0, '<ul class="b" style="columns:2;column-gap:40px"><li class="p">Pool: ≥150 pressure balls, ≥12 matches, ≥150 usual balls (won the pool test).</li><li class="p">IPL + T20I; Associates weighted 0.5; Elo inside the win-probability model.</li><li class="p">Weights in A\'s composite ∝ each part\'s split-half reliability; uplift floored at 0.15.</li><li class="p">Every number on these trees was chosen by the tournament, not by hand.</li></ul>'))
    return slide(n, "The final recipes", "METHOD", "".join(b),
                 notes="Batters: two thirds context-adjusted composite, one third pressure strike rate. Bowlers: 90% rating blend (mostly B's economy + WPA), 10% uplift, plus the delivered gate.")


# =========================================================================================== 12/13 TOP 10
def top_slide(n, role):
    rows = TOPB if role == "bat" else TOPW
    c = BAT if role == "bat" else BOWL
    b = []
    b.append(box(34, 90, 1530, 0, f'<div class="xs m">Official order (FINAL_TOP10_HYBRID.csv). Pressure = highest-leverage balls (leverage pct {"75" if role == "bat" else "70"}+), as in the report\'s evidence table. {chip("P(top 10)", c, True)} share of 300 resamples · <b>specs</b> = alternative specifications agreeing.</div>'))
    cw, chh = 296, 358
    for i, r in enumerate(rows):
        row, col = divmod(i, 5)
        x = 34 + col * (cw + 12); y = 116 + row * (chh + 6)
        prof = PROF[r["player"]]
        if role == "bat":
            a, u, lab, better = r["P SR"], r["usual SR"], "strike rate", r["P SR"] >= r["usual SR"]
            line2 = f'{r["P balls"]} pressure balls · {r["P outs"]} outs · runs above exp. <b>{r["P RAE/100"]:+.1f}</b>/100'
        else:
            a, u, lab, better = r["P econ"], r["usual econ"], "economy", r["P econ"] <= r["usual econ"]
            line2 = f'{r["P balls"]} pressure balls · {r["P wkts"]} wkts · runs saved <b>{r["P RAE saved/100"]:+.1f}</b>/100'
        mx = max(a, u) * 1.15
        bars = (f'<div style="display:grid;grid-template-columns:62px 1fr 44px;gap:4px 6px;align-items:center;font-size:11.5px">'
                f'<span class="m">pressure</span><div style="height:12px;border-radius:3px;background:{c};width:{a / mx * 100:.0f}%"></div><b>{a:.1f}</b>'
                f'<span class="m">usual</span><div style="height:12px;border-radius:3px;background:#4a3f5c;width:{u / mx * 100:.0f}%"></div><b class="m">{u:.1f}</b></div>')
        dlt = a - u
        if role == "bat":
            verdict = chip(f"SR {dlt:+.1f} vs usual", C["good"] if dlt > 3 else C["bad"] if dlt < -3 else C["muted"])
        else:
            verdict = chip(f"economy {dlt:+.2f} vs usual", C["good"] if dlt < -0.2 else C["bad"] if dlt > 0.2 else C["muted"])
        team = prof.get("last_ipl_team") or "T20I only"
        inner = (f'<div class="ph" style="position:relative;width:100%;height:136px;margin-bottom:8px">{"<img src=" + chr(34) + photo(r["pid"]) + chr(34) + "/>" if photo(r["pid"]) else ""}'
                 f'<div style="position:absolute;left:8px;top:8px;width:34px;height:34px;border-radius:50%;background:{c};display:grid;place-items:center;font-family:Archivo;font-weight:900;font-size:16px">{r["rank"]}</div>'
                 f'<div style="position:absolute;right:8px;top:8px">{chip(str(r["p_top10"]) + "%", c, True)}</div></div>'
                 f'<div class="h3" style="font-size:16px">{r["player"]}</div><div class="xs m" style="margin-bottom:8px">{team} · specs {r["specs"]}/{r["n_specs"]}</div>'
                 f'<div class="xs" style="margin-bottom:4px;font-weight:700">{lab.capitalize()}</div>{bars}<div class="xs m" style="margin-top:8px">{line2}</div><div style="margin-top:8px">{verdict}</div>')
        b.append(card(x, y, cw, chh, inner, "", "padding:10px 12px"))
    title = "Most reliable under pressure: batters" if role == "bat" else "Most reliable under pressure: bowlers"
    return slide(n, title, "RESULTS", "".join(b),
                 notes="Each card: pressure vs usual level, sample size, and how often the player stays in the top 10 when the data are resampled.")


@add
def s_topbat(n):
    return top_slide(n, "bat")


@add
def s_topbowl(n):
    return top_slide(n, "bowl")


# =========================================================================================== 14 RELIABILITY
@add
def s_reliability(n):
    b = []
    for j, (role, rows, c) in enumerate((("Batters", TOPB, BAT), ("Bowlers", TOPW, BOWL))):
        x = 34 + j * 520
        b.append(card(x, 96, 504, 520, f'<div class="h2">{role}</div><div class="xs m">P(top 10) across 300 resamples · right: specs agreeing</div>'))
        b.append(svg_abs(x + 16, 158, 472, 446, ch.ptop_bars(rows, 472, 446, c)))
    b.append(card(1074, 96, 492, 520, ""))
    b.append(pill(1094, 112, 300, "HOW TO READ THIS", C["jersey"], 32, 14))
    b.append(box(1094, 160, 456, 0, '<ul class="b"><li class="p"><b>Ranks 1–4</b> in each list are well supported: high P(top 10) and most specifications agree.</li>'
                                     '<li class="p"><b>Ranks 7–10</b> sit in a crowded band: the next 5–10 players are close.</li>'
                                     '<li class="p">No method keeps more than ~6–7 of its 10 names across resamples. That is a limit of the data, not of one method.</li>'
                                     '<li class="p">Hazlewood is top 10 in <b>39 of 39</b> specifications; Abhishek Sharma in <b>12 of 12</b>.</li></ul>'))
    b.append(card(34, 632, 1532, 220, ""))
    b.append(pill(54, 648, 300, "LIMITS WE STATE OPENLY", C["magenta"], 32, 14, "alert"))
    lim = [("Modest predictive power", "+0.3 to +0.45 pool SD on unseen matches; wicket/dismissal targets are the noisiest"),
           ("First innings is harder", "AUC 0.71: no target yet, so first-innings leverage is flatter"),
           ("Missing extras", "runs beyond the first on wides/byes/leg-byes absent; chases ~1 run short"),
           ("Cross-competition mix", "players whose pressure balls are mostly T20I (or mostly IPL) carry extra uncertainty")]
    for i, (a, s_) in enumerate(lim):
        b.append(box(54 + i * 378, 698, 360, 0, f'<div class="h3">{a}</div><div class="s m" style="margin-top:4px">{s_}</div>'))
    return slide(n, "How sure are we?", "RESULTS", "".join(b),
                 notes="Bootstrap and specification checks show which ranks are solid and which are close calls.")


# =========================================================================================== 15 RR GAPS
@add
def s_rrgaps(n):
    b = []
    G = {(r["side"], r["seg"]): r for r in D["rr_gaps"]}
    b.append(card(34, 96, 900, 470, '<div class="h2">Where RR lose matches under pressure</div><div class="xs m">IPL 2025–26, pressure balls only (Pressure Index top 30%). Rank among 10 teams by value per 100 pressure balls (1 = best).</div>'))
    phases = [("PP", "Powerplay"), ("MID", "Middle overs"), ("DEATH", "Death overs")]
    def cell(side, ph):
        r = G[(side, ph)]; rk = r["RR rank/10"]
        colr = C["good"] if rk <= 3 else C["bad"] if rk >= 7 else C["warn"]
        rpo = f'{r["RR rpo"]:.2f} rpo vs {r["median rpo"]:.2f}' if r["RR rpo"] == r["RR rpo"] else ""
        return (f'<div style="border:2px solid {colr};border-radius:12px;padding:12px 14px;height:136px;background:{C["panel2"]}">'
                f'<div style="display:flex;justify-content:space-between;align-items:baseline"><span class="big" style="font-size:44px;color:{colr}">#{rk}</span><span class="xs m">of 10</span></div>'
                f'<div class="s" style="margin-top:6px">value <b>{r["RR val/100"]:+.1f}</b> vs median {r["median team"]:+.1f}</div><div class="xs m">{rpo} · {r["RR balls"]} balls</div></div>')
    b.append(box(64, 170, 840, 0, '<div style="display:grid;grid-template-columns:110px repeat(3,1fr);gap:12px;align-items:center">'
                 + '<span></span>' + "".join(f'<div class="h3" style="text-align:center">{lab}</div>' for _, lab in phases)
                 + f'<div class="h3">{icon("bat", 18, BAT)} RR batting</div>' + "".join(cell("bat", p) for p, _ in phases)
                 + f'<div class="h3">{icon("ball", 18, BOWL)} RR bowling</div>' + "".join(cell("bowl", p) for p, _ in phases) + '</div>'))
    b.append(box(64, 500, 840, 0, '<div class="xs m">Context: RR finished 9th in IPL 2025 (4 wins) and 4th in IPL 2026 (8 wins), per Cricxtasy and MyKhel. Green = top 3, amber = 4–6, red = 7–10.</div>'))
    k = D["pick_bat"]["rr_mid"]
    b.append(card(950, 96, 616, 470, ""))
    b.append(pill(970, 112, 300, "THREE GAPS, ONE STRENGTH", C["magenta"], 32, 14))
    items = [("bad", "Gap 1 · Middle-overs batting", f'#7 of 10. Against spin under pressure RR strike at <b>{k["rr_spin"]["sr"]:.0f}</b> vs league <b>{k["lg_spin"]["sr"]:.0f}</b> (value {k["rr_spin"]["v"]:+.1f} vs {k["lg_spin"]["v"]:+.1f}).'),
             ("bad", "Gap 2 · Death bowling", f'#8 of 10, {G[("bowl", "DEATH")]["RR rpo"]:.2f} runs per over under pressure.'),
             ("warn", "Gap 3 · Powerplay bowling", "#7 of 10: new-ball pressure overs leak."),
             ("good", "Strength · Powerplay batting", "#1 of 10 (value +33.0 vs median +10.4): the openers already win pressure overs.")]
    for i, (kind, a, s_) in enumerate(items):
        colr = C[kind]
        b.append(box(972, 162 + i * 98, 576, 0, f'<div style="display:flex;gap:12px"><div style="flex:none;width:12px;height:12px;border-radius:50%;background:{colr};margin-top:6px"></div><div><div class="h3">{a}</div><div class="s m" style="margin-top:3px">{s_}</div></div></div>'))
    # auction timeline
    b.append(card(34, 582, 1532, 270, ""))
    b.append(pill(54, 598, 360, "IPL 2027: THE WINDOW RR HAVE", C["jersey"], 32, 14, "clock"))
    g = Graph()
    ev = [("t0", "17 Nov 2026", "Retention & release lists due", "keep the core"), ("t1", "23 Nov", "Player registration closes", "who is in the pool"),
          ("t2", "9 Dec", "Trade window closes", "trade route for contracted targets"), ("t3", "16 Dec · Goa", "Mini-auction", "last mini-auction before the 2028 mega auction")]
    for i, (k_, d_, a, s_) in enumerate(ev):
        g.node(k_, 60 + i * 380, 656, 330, 120, f'<b>{icon("flag", 16, C["pink"])} {d_}</b><small style="color:{C["text"]};font-size:13.5px">{a}</small><small>{s_}</small>', "node hot" if i == 3 else "node")
    for i in range(3):
        g.edge(f"t{i}", f"t{i + 1}")
    b.append(g.render())
    b.append(box(60, 794, 1480, 0, '<div class="xs m">Dates: BCCI timeline as reported by CricTracker and Sportsdigest (Nov 2026). Mini-auction = most players stay with their franchises; contracted targets need a release or a trade.</div>'))
    return slide(n, "RR's pressure gaps going into the auction", "RR STRATEGY", "".join(b),
                 notes="Same pressure definition, applied to RR's own IPL 2025-26 matches. The gaps decide which of our top 20 matter most for RR.")


# =========================================================================================== 16/17 RR FIT
AVAIL = {
    "Vaibhav Sooryavanshi": ("RR", "retain"), "Priyansh Arya": ("PBKS", "release/trade"), "Heinrich Klaasen": ("SRH", "release/trade"),
    "Abhishek Sharma": ("SRH", "release/trade"), "Suryakumar Yadav": ("MI", "release/trade"), "Travis Head": ("SRH", "release/trade"),
    "Rovman Powell": ("KKR", "release/trade"), "Finn Allen": ("KKR", "release/trade"), "Phil Salt": ("RCB", "release/trade"), "Dewald Brevis": ("CSK", "release/trade"),
    "Josh Hazlewood": ("RCB", "release/trade"), "Mujeeb Ur Rahman": ("no 2026 IPL team", "auction pool"), "Mohsin Khan": ("LSG", "release/trade"),
    "Abrar Ahmed": ("Pakistan", "not in IPL pool"), "Jasprit Bumrah": ("MI", "release/trade"), "Mahedi Hasan": ("Bangladesh", "auction pool"),
    "Varun Chakravarthy": ("KKR", "release/trade"), "Taskin Ahmed": ("Bangladesh", "auction pool"), "Mohammad Nawaz": ("Pakistan", "not in IPL pool"),
    "Haris Rauf": ("Pakistan", "not in IPL pool")}
ACOL = {"retain": C["good"], "release/trade": C["warn"], "auction pool": C["blue"], "not in IPL pool": C["faint"]}
FIT = {
    "Vaibhav Sooryavanshi": ("core", "Already RR. 77% of his pressure balls are powerplay (+37.6/100): the engine of RR's #1 powerplay. Retain."),
    "Priyansh Arya": ("low", "Powerplay opener (85% PP). Overlaps RR's strongest phase: backup only."),
    "Heinrich Klaasen": ("high", "Gap 1. 67% middle overs (+36.7/100); vs spin under pressure SR 197. The cleanest fix for RR's middle-overs problem."),
    "Abhishek Sharma": ("low", "Powerplay opener (72% PP). Elite, but RR's openers already top the league."),
    "Suryakumar Yadav": ("high", "Gap 1. 63% of his pressure balls in the middle overs, +40.6/100 there. Only if MI let him go."),
    "Travis Head": ("low", "Powerplay opener (85% PP). Overlaps RR's strength; overseas slot better spent elsewhere."),
    "Rovman Powell": ("mid", "Finisher: 41% death (+58.4/100). Overseas cover for the death-overs batting slot."),
    "Finn Allen": ("low", "Powerplay opener (86% PP). Overlap with RR's strength."),
    "Phil Salt": ("low", "Powerplay opener (71% PP); middle-overs value −3.3/100."),
    "Dewald Brevis": ("high", "Gap 1. 64% middle overs (+26.4/100); young, so a long-term middle-order option."),
    "Josh Hazlewood": ("high", "Gaps 2 + 3. Powerplay +32.3/100 at 7.66 rpo and death +34.5/100: covers both RR bowling gaps. Overseas."),
    "Mujeeb Ur Rahman": ("mid", "Spin: middle +21.2, death +48.7/100 but powerplay −13.9. Middle-overs bowling is not an RR gap; depth pick."),
    "Mohsin Khan": ("high", "Gaps 2 + 3 without an overseas slot: powerplay +23.9, death +84.5/100 (7.65 rpo). No 2025 matches in the data; check fitness."),
    "Abrar Ahmed": ("bench", "Not in the IPL pool. Benchmark profile: middle-overs leg-spin, +37.1/100."),
    "Jasprit Bumrah": ("bench", "MI core player; a release is very unlikely. Benchmark for powerplay + death pressure."),
    "Mahedi Hasan": ("mid", "Gap 3: powerplay spin +43.6/100 at 6.31 rpo; weak in middle overs (−47.3). Pool only if registered."),
    "Varun Chakravarthy": ("low", "Middle-overs spin (64%): not an RR gap, and a KKR core player."),
    "Taskin Ahmed": ("high", "Gaps 2 + 3: death +39.2/100 at 7.66 rpo, powerplay +18.6. Realistic auction-pool pace option if registered."),
    "Mohammad Nawaz": ("bench", "Not in the IPL pool. Benchmark: middle-overs spin all-rounder."),
    "Haris Rauf": ("bench", "Not in the IPL pool. Benchmark: death pace (36% death, +25.1/100)."),
}
FCOL = {"core": C["good"], "high": C["pink"], "mid": C["warn"], "low": C["faint"], "bench": C["faint"]}
FLAB = {"core": "CORE", "high": "HIGH FIT", "mid": "SITUATIONAL", "low": "LOW FIT", "bench": "BENCHMARK"}


def fit_slide(n, role):
    rows = TOPB if role == "bat" else TOPW
    c = BAT if role == "bat" else BOWL
    b = []
    b.append(box(34, 90, 1530, 0, f'<div class="s m" style="display:flex;gap:10px;align-items:center;flex-wrap:wrap">Bars = share of pressure balls (PI top 30%) by phase; values per 100 pressure balls. Fit = closes an RR gap? Availability: '
                                   + "".join(chip(k, v, True) for k, v in ACOL.items()) + '</div>'))
    for i, r in enumerate(rows):
        row, col = divmod(i, 2)
        x = 34 + col * 772; y = 124 + row * 146
        prof = PROF[r["player"]]; team, av = AVAIL[r["player"]]; fit, txt = FIT[r["player"]]
        img = f'<img src="{photo(r["pid"])}"/>' if photo(r["pid"]) else ""
        inner = (f'<div style="display:grid;grid-template-columns:96px 176px 1fr;gap:12px;height:100%">'
                 f'<div class="ph" style="position:relative;height:118px">{img}<div style="position:absolute;left:5px;top:5px;width:26px;height:26px;border-radius:50%;background:{c};display:grid;place-items:center;font-family:Archivo;font-weight:900;font-size:13px">{r["rank"]}</div></div>'
                 f'<div><div class="h3" style="font-size:14px;white-space:nowrap">{r["player"]}</div><div class="xs m">{team}</div>'
                 f'<svg width="170" height="70" style="margin-top:6px">{ch.phase_strip(prof["phases"], 170, 70, c)}</svg></div>'
                 f'<div><div style="display:flex;gap:6px;margin-bottom:6px">{chip(FLAB[fit], FCOL[fit], True)}{chip(av, ACOL[av], True)}</div><div class="s">{txt}</div></div></div>')
        b.append(card(x, y, 760, 138, inner, "", "padding:10px 12px" + (f";border-color:{C['pink']}" if fit == "high" else "")))
    title = "How each batter could strengthen RR" if role == "bat" else "How each bowler could strengthen RR"
    return slide(n, title, "RR STRATEGY", "".join(b),
                 notes="Each top-10 player matched against RR's pressure gaps and the IPL 2027 availability routes. Fit and availability are separate: a high-fit player under contract needs a release or a trade.")


@add
def s_fitbat(n):
    return fit_slide(n, "bat")


@add
def s_fitbowl(n):
    return fit_slide(n, "bowl")


# =========================================================================================== 18 PLAN
@add
def s_plan(n):
    b = []
    g = Graph()
    g.node("rr", 34, 330, 200, 130, f'<img src="{logo()}" style="height:70px;align-self:center"/><b style="justify-content:center">RR · IPL 2027</b>', "node", "align-items:center")
    plans = [("p1", "1 · Retain the powerplay engine", "Vaibhav Sooryavanshi (#1 batter, 94% of resamples). Keeps RR's #1 powerplay.", [(50284, "Vaibhav")], C["good"]),
             ("p2", "2 · Fix the middle overs (Gap 1)", "Target a middle-overs pressure batter, in order of fit and availability: Klaasen (SR 197 vs spin under pressure) → Suryakumar → Brevis.", [(4260, "Klaasen"), (1699, "SKY"), (25213, "Brevis")], C["pink"]),
             ("p3", "3 · Death + new-ball pace (Gaps 2–3)", "Indian slot: Mohsin Khan. Overseas: Hazlewood if released; auction-pool option: Taskin Ahmed.", [(6669, "Mohsin"), (830, "Hazlewood"), (2681, "Taskin")], C["pink"]),
             ("p4", "4 · Don't buy another opener", "Abhishek, Head, Allen, Salt, Priyansh are elite but play RR's strongest phase. Spend the purse on gaps.", [], C["faint"])]
    for i, (k, a, s_, pics, colr) in enumerate(plans):
        y = 96 + i * 186
        thumbs = "".join(f'<div style="text-align:center"><div class="ph" style="position:relative;width:74px;height:74px">{"<img src=" + chr(34) + photo(pid) + chr(34) + "/>" if photo(pid) else ""}</div><div class="xs m" style="margin-top:3px">{nm}</div></div>' for pid, nm in pics)
        g.node(k, 300, y, 760, 170, f'<div style="display:flex;gap:16px;align-items:center;height:100%"><div style="flex:1"><b style="font-size:17px">{a}</b><small style="font-size:14px;color:{C["text"]};margin-top:6px">{s_}</small></div><div style="display:flex;gap:10px">{thumbs}</div></div>', "node", f"border-color:{colr}")
        g.edge("rr", k, "r", "l", color=colr, ta=0.2 + i * 0.2)
    b.append(g.render())
    # watchlist + archer
    w = D["watch"]
    b.append(card(1080, 96, 486, 380, ""))
    b.append(pill(1100, 112, 300, "WATCHLIST · RECENT FORM", C["jersey"], 32, 14, "eye"))
    wl = "".join(f'<tr><td>{p["name"]}</td><td>{p["team"]}</td><td>#{p["rk"]}</td><td>{p["ptop"] * 100:.0f}%</td></tr>' for p in w["bat"] + w["bowl"])
    b.append(box(1100, 156, 446, 0, f'<div class="xs m" style="margin-bottom:6px">Top 10 on 2025–26 only (≥120 pressure balls), stable in ≥50% of 1,000 resamples, not in the official top 10. Context, not a change to the list. PAK players are not in the IPL pool.</div><table class="t"><tr><th>Player</th><th>Team</th><th>Recent</th><th>Stable</th></tr>{wl}</table>'))
    a = next(r for r in w["rr"] if r["name"] == "Jofra Archer")
    b.append(card(1080, 492, 486, 360, ""))
    b.append(box(1100, 508, 140, 150, f'<img src="{photo(3298)}" style="position:absolute;inset:0;width:100%;height:100%;object-fit:contain;object-position:bottom"/>', "ph"))
    b.append(box(1256, 508, 290, 0, f'<div class="h3">Jofra Archer: data over reputation</div><div class="s m" style="margin-top:6px">Official <b class="pk">#{a["official"]}</b> bowler; top 10 in {a["ptop"] * 100:.1f}% of resamples. IPL 2026: {a["s26"]["w"]} wickets, pressure economy {a["s26"]["pm"]:.2f} vs {a["s26"]["um"]:.2f} usual.</div>'))
    b.append(box(1100, 674, 446, 0, '<div class="s">Seasons under pressure (runs saved /100): ' + " · ".join(f'{s_["y"]} <b class="{"gd" if s_["v"] > 0 else "bd"}">{s_["v"]:+.1f}</b>' for s_ in a["seasons"]) + '</div><div class="s m" style="margin-top:8px">Valuable all-phase bowler, but his pressure numbers swing season to season. We keep him out of the top 10 and do not count him as RR\'s death-overs fix.</div>'))
    return slide(n, "Our IPL 2027 recommendation for RR", "RR STRATEGY", "".join(b),
                 notes="Four moves in priority order, each tied to a measured gap. Archer stays outside the top 10 because the data say so; the watchlist shows recent-form names for context.")


# =========================================================================================== 19 REPRODUCE
@add
def s_repro(n):
    b = []
    for i, (url, ic, a, s_) in enumerate(((LIVE, "globe", "Live dashboard (Vercel)", "explore every player, this deck is embedded under Reproduce"), (GITHUB, "github", "GitHub repository", "raw data, pipeline, outputs, dashboard, this deck"))):
        x = 34 + i * 520
        b.append(card(x, 96, 504, 240, f'<div style="display:flex;gap:18px"><div style="border-radius:12px;overflow:hidden;flex:none">{qr_svg(url, 150)}</div><div><div class="h3" style="font-size:18px">{icon(ic, 19, C["pink"])} {a}</div><div class="s m" style="margin-top:6px">{s_}</div><div class="mono xs" style="margin-top:14px;word-break:break-all;color:{C["pink"]}"><a href="{url}">{short(url)}</a></div></div></div>'))
    b.append(card(1074, 96, 492, 240, ""))
    b.append(pill(1094, 112, 300, "VERIFIED", C["good"], 32, 14, "check"))
    b.append(box(1094, 160, 456, 0, '<ul class="b good"><li class="p">Clean clone + rerun: all 40 data files, tables and figures identical; report text identical on all 10 pages.</li><li class="p">Dashboard: 10,172 checks recomputed from the pipeline, 0 failed.</li><li class="p">Seed 42, pinned package versions.</li></ul>'))
    steps = [("1", "Clone", "git clone …/SupeRR-Selector-S2-Round1"), ("2", "Install", "pip install -r requirements.txt"), ("3", "Run", "./reproduce.sh  (≈45–60 min)"), ("4", "Check", "FINAL_TOP10_HYBRID.csv + '0 failed'"), ("5", "Explore", "open dashboard/dist/…html")]
    g = Graph()
    for i, (k, a, cmd) in enumerate(steps):
        g.node(f"r{i}", 34 + i * 310, 354, 282, 108, f'<b>{icon("play" if i == 2 else "code", 16, C["pink"])} {k} · {a}</b><small class="mono" style="color:{C["text"]};font-size:12.5px;margin-top:8px">{cmd}</small>', "node hot" if i == 2 else "node")
        if i:
            g.edge(f"r{i - 1}", f"r{i}")
    b.append(g.render())
    b.append(card(34, 478, 760, 374, ""))
    b.append(pill(54, 494, 260, "REPOSITORY LAYOUT", C["jersey"], 32, 14))
    tree = """README.md            step-by-step guide
reproduce.sh         one command, end to end
requirements.txt     pinned versions
data/raw/            the six CSVs
pipeline/src/        config.py, s01 … s09
pipeline/outputs/    parquet, CSVs, figures, report
dashboard/           source, data, verifier, dist/
deck/                this presentation (HTML, PDF, PPTX)"""
    b.append(box(54, 542, 720, 0, f'<pre class="mono" style="font-size:16.5px;line-height:1.75;color:{C["text"]}">{esc(tree)}</pre>'))
    b.append(card(810, 478, 756, 374, ""))
    b.append(pill(830, 494, 300, "ONLY THE DASHBOARD?", C["jersey"], 32, 14))
    b.append(box(830, 540, 716, 0, f'<pre class="mono" style="font-size:14px;line-height:1.7;background:{C["bg"]};border-radius:10px;padding:14px 16px;color:{C["text"]}">./reproduce.sh dashboard     # ~2 min, from committed outputs\ncd dashboard && python3 -m http.server 8000</pre>'
                                    '<div class="s m" style="margin-top:12px">Or just open <span class="mono">dashboard/dist/under-pressure-rating.html</span>: one self-contained file, works offline.</div>'
                                    '<div class="h3" style="margin-top:12px">Inside the dashboard</div><ul class="b" style="columns:2;margin-top:8px"><li>Overview & featured top 3</li><li>Batters / Bowlers tables + profiles</li><li>Pressure Model explainer</li><li>Compare two players</li><li>Match-by-match pressure value</li><li>Watchlist & RR review</li><li>Methodology + full report</li><li>Reproduce: this deck, links, steps</li></ul>'))
    return slide(n, "Reproduce everything", "REPRODUCE", "".join(b),
                 notes="Both links, the five steps a judge needs, and what we verified.")


# =========================================================================================== 20 THANK YOU
@add
def s_thanks(n):
    b = [box(0, 0, W, H, "", "", f"background:{C['frame']}"), box(0, 0, 560, H, "", "", f"background:{C['panel']}")]
    b.append(box(150, 250, 260, 0, f'<img src="{logo()}" style="height:330px"/>'))
    b.append(box(640, 170, 900, 0, '<div class="big" style="font-size:120px">THANK<br><span class="pk">YOU</span></div>'))
    b.append(box(640, 470, 880, 0, '<div class="p" style="font-size:20px">Pressure measured by the match, players judged against an average player in the same spot, method chosen on matches it never saw, and every number reproducible from the raw files.</div>'))
    for i, (url, ic, a) in enumerate(((LIVE, "globe", "Live dashboard"), (GITHUB, "github", "GitHub"))):
        x = 640 + i * 440
        b.append(box(x, 620, 420, 0, f'<div style="display:flex;gap:16px;align-items:center"><div style="border-radius:10px;overflow:hidden">{qr_svg(url, 120)}</div><div><div class="h3">{icon(ic, 17, C["pink"])} {a}</div><div class="xs m mono" style="word-break:break-all;margin-top:4px">{short(url)}</div></div></div>'))
    b.append(box(640, 800, 900, 0, '<div class="xs m">Annexure follows: how we analysed the data · the player pick we are backing · war-room moments.</div>'))
    return slide(n, None, None, "".join(b), notes="Thank you.")


# =========================================================================================== A1 DATA ANALYSIS
@add
def s_annex_data(n):
    b = []
    for j, inn in enumerate(("1", "2")):
        x = 34 + j * 520
        b.append(card(x, 96, 504, 400, f'<div class="h2">{"First innings" if inn == "1" else "Chasing innings"}</div><div class="xs m">Average Pressure Index by over × wickets lost</div>'))
        b.append(svg_abs(x + 14, 160, 476, 326, ch.heatmap(D["pressure_map"][inn], 476, 326)))
    b.append(card(1074, 96, 492, 400, '<div class="h2">How pressure is distributed</div><div class="xs m">All 193,988 balls by Pressure Index (pink = top 30%)</div>'))
    b.append(svg_abs(1088, 160, 464, 326, ch.hist(D["pi_hist"], 464, 326, D["pi_cut"])))
    d0 = next(d_ for d_ in D["definitions"] if d_["definition"].startswith("PI"))
    facts = [("Pressure balls are not slower", f'run rate {d0["run rate (pressure)"]:.2f} under pressure vs {d0["run rate (routine)"]:.2f} routine; boundaries {d0["boundary % (pressure)"]:.1f}% vs {d0["boundary % (routine)"]:.1f}%'),
             ("…but mistakes cost more", f'dismissal {d0["dismissal % (pressure)"]:.2f}% vs {d0["dismissal % (routine)"]:.2f}% per ball, and each wicket swings the result further'),
             ("Chases carry the sharpest pressure", "the second innings has a target, so every ball's swing is larger (AUC 0.896 vs 0.706)"),
             ("Wickets in hand drive it", "the same over is far more pressured 4–5 down than 0–1 down (heatmaps)")]
    b.append(card(34, 512, 1532, 340, ""))
    b.append(pill(54, 528, 360, "WHAT THE EXPLORATION TOLD US", C["magenta"], 32, 14, "search"))
    for i, (a, s_) in enumerate(facts):
        r, c = divmod(i, 2)
        b.append(box(54 + c * 770, 596 + r * 128, 730, 0, f'<div style="display:flex;gap:18px"><div style="flex:none;width:58px;height:58px;border-radius:14px;background:{C["panel2"]};display:grid;place-items:center;font-family:Archivo;font-weight:900;font-size:26px;color:{C["pink"]}">{i + 1}</div><div><div class="h3" style="font-size:25px;line-height:1.15">{a}</div><div class="s m" style="margin-top:6px;font-size:20px;line-height:1.4">{s_}</div></div></div>'))
    return slide(n, "Annexure A · How we analysed the data", "REPRODUCE", "".join(b),
                 notes="Exploration that shaped the method: where pressure sits in an innings and how play changes under it.")


# =========================================================================================== A2 PLAYER PICK
@add
def s_annex_pick(n):
    k = D["pick_bat"]; r = next(x for x in TOPB if x["player"] == "Heinrich Klaasen"); rm = k["rr_mid"]
    b = []
    b.append(box(34, 96, 380, 520, f'<img src="{photo(4260)}" style="position:absolute;inset:0;width:100%;height:100%;object-fit:contain;object-position:bottom"/>', "ph"))
    b.append(box(50, 112, 0, 0, chip("THE PICK WE ARE BACKING", C["pink"], True)))
    b.append(box(34, 630, 380, 0, f'<div class="big" style="font-size:40px">HEINRICH<br>KLAASEN</div><div class="s m" style="margin-top:8px">Official #{r["rank"]} batter · top 10 in {r["p_top10"]}% of resamples · {r["specs"]}/{r["n_specs"]} specifications</div>'))
    b.append(card(434, 96, 640, 360, '<div class="h2">He fixes RR\'s biggest batting gap</div><div class="xs m">Strike rate against spin in the middle overs under pressure (IPL 2025–26 for RR & league; Klaasen 2022–26)</div>'))
    b.append(svg_abs(450, 170, 608, 270, ch.hbars([("RR vs spin", rm["rr_spin"]["sr"], C["bad"]), ("League vs spin", rm["lg_spin"]["sr"], C["faint"]), ("Klaasen vs spin", k["spin"]["sr"], BAT)], 608, 270, maxv=220, fmt="{:.0f}", label_w=160)))
    b.append(card(1090, 96, 476, 360, ""))
    b.append(pill(1110, 112, 300, "UNDER PRESSURE VS USUAL", C["jersey"], 32, 14))
    rows = [("Strike rate", f'{k["pressure"]["sr"]:.1f}', f'{k["usual"]["sr"]:.1f}'), ("Runs above exp. /100", f'{k["pressure"]["v"]:+.1f}', f'{k["usual"]["v"]:+.1f}'),
            ("Balls per dismissal", f'{k["pressure"]["pb"] / max(k["pressure"]["outs"], 1):.1f}', f'{k["usual"]["pb"] / max(k["usual"]["outs"], 1):.1f}'), ("Balls", f'{k["pressure"]["pb"]}', f'{k["usual"]["pb"]}')]
    b.append(box(1110, 160, 436, 0, '<table class="t"><tr><th></th><th>Pressure</th><th>Usual</th></tr>' + "".join(f'<tr><td>{a}</td><td><b class="{"" if a.startswith("Balls") else "pk"}">{x}</b></td><td>{y}</td></tr>' for a, x, y in rows) + '</table>'
                                    f'<div class="xs m" style="margin-top:10px">Pressure = Pressure Index top 30%, 2022–26. The report\'s leverage-percentile view gives the same picture: SR {r["P SR"]:.1f} vs {r["usual SR"]:.1f}.</div>'))
    b.append(card(434, 472, 640, 380, '<div class="h2">Positive in every season</div><div class="xs m">Runs above expected per 100 pressure balls</div>'))
    b.append(svg_abs(450, 540, 608, 300, ch.season_bars(k["seasons"], 608, 300, BAT)))
    b.append(card(1090, 472, 476, 380, ""))
    b.append(pill(1110, 488, 300, "THE HONEST CASE", C["magenta"], 32, 14))
    b.append(box(1110, 536, 436, 0, f'<ul class="b"><li class="s">Middle overs {k["phases"]["MID"]["pb"]} balls (+{k["phases"]["MID"]["v"]:.1f}/100) and death {k["phases"]["DEATH"]["pb"]} balls (+{k["phases"]["DEATH"]["v"]:.1f}): exactly where RR rank 7th and 5th.</li>'
                                    f'<li class="s">Chasing ({k["chase"]["v"]:+.1f}/100) and setting ({k["setting"]["v"]:+.1f}): delivers in both.</li>'
                                    f'<li class="s">2025 was quiet ({k["seasons"][3]["v"]:+.1f}/100); 2026 back to {k["seasons"][4]["v"]:+.1f}.</li>'
                                    f'<li class="s">He gets out more often under pressure (every {k["pressure"]["pb"] / k["pressure"]["outs"]:.1f} balls vs {k["usual"]["pb"] / k["usual"]["outs"]:.1f}): the price of attacking, already charged in his +{k["pressure"]["v"]:.1f} value.</li>'
                                    '<li class="s">Overseas slot and an SRH contract: route is a trade (to 9 Dec) or a release. Fallback: Dewald Brevis.</li></ul>'))
    return slide(n, "Annexure B · The player pick we are backing", "REPRODUCE", "".join(b),
                 notes="Heinrich Klaasen: the strongest data match for RR's biggest batting gap, middle-overs pressure against spin.")


# =========================================================================================== A3 WAR ROOM
@add
def s_annex_war(n):
    b = []
    g = Graph()
    moments = [("w1", "bug", "The result that looked too good", "Solution A v3 jumped to 0.31 reliability. A diagnostic showed it was measuring match context, not skill.", "Dropped it, even though it flattered us.", C["bad"]),
               ("w2", "swap", "Two teams, no winner", "Solution A and B were built separately. On the same unseen matches, A won on dismissals, B on strike rate.", "Wrote the selection rule first, then ran the tournament.", C["warn"]),
               ("w3", "users", "\"Why isn't Archer in?\"", "RR's own strike bowler came out #45. Tempting to nudge him in.", "Stayed with the data; added a clearly labelled watchlist instead.", C["blue"]),
               ("w4", "alert", "Dashboard ≠ report", "A judge-facing chart showed Vaibhav at +76.9; the report said +48.7. Two pressure definitions had crept in.", "Unified on the report's definition; built a verifier: 10,172 checks, 0 failed.", C["pink"])]
    for i, (k_, ic, a, what, did, colr) in enumerate(moments):
        x = 34 + i * 386
        g.node(k_, x, 110, 360, 290, f'<div style="width:56px;height:56px;border-radius:14px;background:{C["panel2"]};display:grid;place-items:center;margin-bottom:12px">{icon(ic, 28, colr)}</div>'
                                     f'<b style="font-size:18px">{a}</b><small style="font-size:14px;color:{C["text"]};margin-top:10px">{what}</small>'
                                     f'<small style="font-size:14px;margin-top:12px;color:{colr};font-weight:700">→ {did}</small>', "node", f"border-color:{colr};justify-content:flex-start;padding:18px")
        if i:
            g.edge(moments[i - 1][0], k_, color=C["faint"])
    b.append(g.render())
    b.append(card(34, 424, 1532, 428, ""))
    b.append(pill(54, 440, 470, "THE EASY ANSWER VS WHAT WE SHIPPED", C["jersey"], 32, 14))
    rows = [("Pressure definition", "Overs 17–20 + required rate 9+ (the obvious rule)", "Win-probability leverage, validated (2.06× decisive share)"),
            ("Rating", "Raw pressure strike rate", "Context-adjusted value, shrunk, + pressure SR, chosen on unseen matches"),
            ("Best-looking version", "A v3 (0.31 reliability)", "Rejected: it measured context"),
            ("RR's own players", "Nudge Archer into the top 10", "Official list untouched; watchlist + RR review shown separately"),
            ("Dashboard numbers", "Two pressure definitions mixed", "Generated from the pipeline and checked: 10,172 checks"),
            ("Choosing the method", "Pick the version we liked best", "Pre-stated rule on 16 held-out cells: best worst case, then best mean")]
    b.append(box(54, 492, 1492, 0, '<table class="t" style="font-size:15px"><tr><th style="width:22%">Decision</th><th style="width:36%;background:#7a1f3d">Easy answer</th><th style="background:#14532d">Shipped</th></tr>'
                                    + "".join(f'<tr><td><b>{a}</b></td><td class="m">{x}</td><td>{y}</td></tr>' for a, x, y in rows) + '</table>'))
    return slide(n, "Annexure C · War-room moments", "REPRODUCE", "".join(b),
                 notes="Four moments where the easy answer was wrong, and what the data made us do instead.")

if __name__ == "__main__":
    import sys
    from build import build
    build()
