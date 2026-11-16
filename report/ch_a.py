"""Cover, contents and chapters 1-7: the question, the data, cleaning, the plan, defining and checking pressure."""
from rlib import *
WPM = D["wp_metrics"]


def cover():
    v, h = D["top"]["bat"][0], D["top"]["bowl"][0]
    imgs = "".join(f'<div style="width:62mm;height:70mm;border-radius:14px;background:#221b30;overflow:hidden;position:relative">'
                   f'<img src="{photo(p["pid"])}" style="position:absolute;bottom:0;left:0;width:100%;height:100%;object-fit:contain;object-position:bottom"/>'
                   f'<div style="position:absolute;left:10px;top:10px">{chip(lab, col)}</div></div>' for p, lab, col in ((v, "#1 BATTER", PINK), (h, "#1 BOWLER", BLUE)))
    return f"""<div class="cover">
<div style="position:absolute;left:0;top:0;width:74mm;height:297mm;background:#1a1424"></div>
<img src="{LOGO}" style="position:absolute;left:18mm;top:20mm;height:52mm"/>
<div style="position:absolute;left:18mm;top:84mm;width:50mm;font-family:Archivo;font-weight:800;font-size:8pt;letter-spacing:.16em;color:#a39bb3;line-height:1.7">SUPERR SELECTOR<br>SEASON 2 · ROUND 1</div>
<div style="position:absolute;left:18mm;top:226mm;width:50mm">
  <div style="font-family:Archivo;font-weight:800;font-size:8pt;letter-spacing:.16em;color:#ff8ccc">WRITTEN BY</div>
  <div style="font-family:Archivo;font-weight:850;font-size:17pt;line-height:1.1;margin-top:4px">Prashast Sidhant</div>
  <div style="font-size:10pt;color:#d9d2e3;margin-top:4px">National Institute of Technology Raipur</div>
</div>
<div style="position:absolute;left:84mm;top:20mm;width:112mm">
  <div style="font-family:Archivo;font-weight:800;font-size:9pt;letter-spacing:.16em;color:#a39bb3">THE COMPLETE GUIDE</div>
  <div style="font-family:Archivo;font-weight:900;font-stretch:118%;font-size:40pt;line-height:.95;margin-top:8px">UNDER<br>PRESSURE<br><span style="color:{PINK}">RATING</span></div>
  <div style="font-size:12pt;line-height:1.5;color:#e9e4f0;margin-top:14px">From six raw CSV files to the most reliable T20 players under pressure, and what they mean for <b>Rajasthan Royals</b> at the <b>IPL 2027 auction</b>. Every step, every formula, every mistake, in plain English.</div>
  <div style="display:flex;gap:6mm;margin-top:12mm">{imgs}</div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:5mm;margin-top:10mm">
    {"".join(f'<div style="border:1px solid #3a3048;border-radius:12px;padding:10px 12px"><div style="font-family:Archivo;font-weight:900;font-size:20pt;color:{PINK}">{a}</div><div style="font-size:9pt;color:#a39bb3">{b}</div></div>' for a, b in [(str(D["n_matches"]), "matches, IPL + T20I, 2022–26"), (f'{D["n_balls"]:,}', "deliveries rebuilt and modelled"), ("10 + 10", "most reliable batters and bowlers"), (CHECKS, "dashboard numbers checked, 0 failed")])}
  </div>
  <div style="font-size:9pt;color:#a39bb3;margin-top:10mm;line-height:1.7">Live dashboard · superr-under-pressure-rating.vercel.app<br>Code, data, results · github.com/sidhantiitian17/SupeRR-Selector-S2-Round1</div>
</div></div>"""


TOC = [("1", "The question, in plain words"), ("2", "Opening the data for the first time"), ("3", "Cleaning: rebuilding every ball"),
       ("4", "The plan before any modelling"), ("5", "What is pressure? Three attempts"), ("6", "Leverage and the Pressure Index"),
       ("7", "Checking the definition"), ("8", "Valuing every ball fairly"), ("9", "Small samples: shrinkage"),
       ("10", "Usual level, consistency and the composite"), ("11", "The refinement journey: 12 steps"), ("12", "A second, independent solution"),
       ("13", "The held-out tournament (how the final method was chosen)"), ("14", "The final recipe, step by step"), ("15", "How sure are we?"),
       ("16", "Results: the top 10 batters and bowlers"), ("17", "From a ranking to a plan for Rajasthan Royals"), ("18", "The player pick we are backing"),
       ("19", "War-room moments"), ("20", "Why this approach, and what we gave up"), ("21", "Limitations, and how accuracy could improve"),
       ("22", "Architecture and reproducing everything yourself"), ("A–D", "Appendices: glossary, formula sheet, settings, number reference")]


PAGES = {}


def contents():
    rows = "".join(f'<div><span class="tn">{n}</span><span>{t}</span><span class="tp">{PAGES.get(n, "")}</span></div>' for n, t in TOC)
    road = Flow(680, 150)
    steps = [("Raw CSVs", "6 files", "n"), ("Clean state", "s01", "b"), ("Pressure", "s02", "p"), ("Ball value", "s03", "b"),
             ("Ratings", "s04–s05", "v"), ("Tournament", "s07", "p"), ("Final lists", "s08", "g"), ("RR plan", "dashboard", "s")]
    for i, (a, b_, k) in enumerate(steps):
        road.node(f"n{i}", 4 + i * 85, 40, 78, 62, a, b_, k, fs=9, align="center")
        if i:
            road.edge(f"n{i - 1}", f"n{i}")
    road.text(4, 24, "THE WHOLE JOURNEY ON ONE LINE", 10, PINK, weight=800)
    road.text(4, 128, "Each box is one chapter group below. s01–s09 are the program files that do the step.", 10)
    return f"""<section style="break-before:page"><h1>Contents</h1><div style="height:10px"></div><div class="toc">{rows}</div>
<h2>How to read this guide</h2>
<p>This guide explains the whole project from the first time we opened the files to the final list of players and the advice for Rajasthan Royals (RR). It is written for someone who has never built a sports model. If you are given the same six files and follow the chapters in order, you should reach the same answer, and you should understand <i>why</i> each choice was made.</p>
<p>Coloured boxes appear throughout:</p>
{box("kid", "<p>A simple picture or analogy for a hard idea. Read these first if the maths looks scary.</p>")}
{box("math", "<p>The exact formula, with a worked example using real numbers from the data.</p>")}
{box("why", "<p>Why we picked this option over the alternatives we tried.</p>")}
{box("mist", "<p>A mistake we made or nearly made, and how we found it. These are the most useful boxes for a beginner.</p>")}
{box("warn", "<p>A limit or a trap you should know about.</p>")}
<p><b>Numbers.</b> Every number in this guide comes from the pipeline outputs in the repository (seed 42). Where a number is rounded for teaching, the box says so.</p>
{road.svg()}</section>"""


# =============================================================================================== 1
def ch1():
    f = Flow(680, 280)
    f.node("brief", 10, 100, 150, 80, "The brief", "SupeRR Selector S2, Round 1", "d")
    for i, (k, a, b_, kind) in enumerate([("q1", "Who is most reliable under pressure?", "top 10 batters + top 10 bowlers", "p"),
                                          ("q2", "Compared with their usual level", "pressure vs normal, side by side", "b"),
                                          ("q3", "Explain the method", "so judges can check it", "v"),
                                          ("q4", "How would they help RR?", "for the IPL 2027 auction", "g")]):
        f.node(k, 230, 6 + i * 68, 250, 60, a, b_, kind)
        f.edge("brief", k, "r", "l", tb=0.5, ta=0.2 + i * 0.2)
    f.node("out", 540, 85, 134, 110, "What we ship", "ranked lists, method report, dashboard, deck, RR plan", "s")
    for k in ("q1", "q2", "q3", "q4"):
        f.edge(k, "out", "r", "l", color="#c9bfd6")
    words = table(["Word in the brief", "What it means in this project", "How we measure it"], [
        ["Pressure", "A moment when the next ball can change who wins.", "Leverage from a win-probability model (Chapter 6)."],
        ["Performance", "Did the player do better than an average player would have done in that exact situation?", "Runs above expected, with a fair price for wickets (Chapter 8)."],
        ["Reliable", "He does it again and again, not once. The number should repeat on different matches and predict future matches.", "Shrinkage, consistency, bootstrap, unseen-match tests (Chapters 9–15)."],
        ["Usual level", "The same player in ordinary, low-stakes moments.", "Bottom 50% of balls by pressure (Chapter 10)."],
        ["Strengthen RR", "Fill a real weakness in RR's squad that the auction can actually address.", "RR's phase-by-phase pressure record + availability (Chapter 17)."]])
    return chapter("1", "Start here", "The question, in plain words",
                   "Before touching any data we wrote down what the brief actually asks, and what each word should mean in numbers. Most bad sports analysis goes wrong here, not in the maths.") + f"""
{f.svg()}
<h2>What the brief asks</h2>
<p>The SupeRR Selector Season 2, Round 1 brief gives ball-by-ball data for IPL and T20 International matches and asks four things: find the <b>most reliable players under pressure</b> (ten batters and ten bowlers), <b>compare</b> how they perform under pressure with how they perform normally, <b>explain the method</b>, and show how these players could <b>strengthen Rajasthan Royals</b> for the IPL 2027 auction.</p>
<p>The trap is that every one of those words sounds obvious and is not. "Pressure" has no agreed definition. "Reliable" could mean "high average" or "rarely fails" or "does it every season". So the first job was to turn each word into something we can count.</p>
{words}
{box("kid", "<p>Imagine two students. One scores 95 in a practice test nobody cares about. The other scores 80 in the final exam, when the whole year depends on it, and does the same in every final for five years. The brief is asking us to find the second student. We need a way to tell which tests were \"finals\", a fair way to mark each answer, and proof that the good marks were not luck.</p>")}
<h2>The three hard problems hiding in the question</h2>
<ol><li><b>Which balls are pressure balls?</b> The last over of a close chase clearly is. The 10th over when one team is 80 runs ahead clearly is not. Everything in between needs a rule, and the rule has to work for thousands of balls.</li>
<li><b>How do we judge a player fairly?</b> An opener in the powerplay and a finisher at the death face completely different balls. A strike rate of 150 is excellent in the middle overs and poor in the last two overs. We must compare each player with what an average player would do in the same spot.</li>
<li><b>How do we avoid rewarding luck?</b> Most players have only a few hundred pressure balls. One hot week can put an unknown player at the top of a raw table. We need to shrink noisy numbers and prove the ranking holds on matches it never saw.</li></ol>
{box("why", "<p>We fixed these definitions <b>before</b> looking at any ranking. If you look at the ranking first, it is very easy to keep tweaking the method until your favourite players come out on top. Writing the rules first protects you from fooling yourself.</p>")}
</section>"""


# =============================================================================================== 2
def ch2():
    files = table(["File", "Rows", "One row is…", "Key columns we used"], [
        ["<code>ball_by_ball.csv</code>", "200,999", "one delivery", "match_id, innings, striker, bowler, runs, is_wicket, dismissal_type, extras_type, pace_or_spin"],
        ["<code>matches.csv</code>", "883", "one match", "date, stage, knock_out, winner, result text, revised overs and target (rain rules)"],
        ["<code>competitions.csv</code>", "141", "one tournament or series", "comp_name, match_format (T20I or T20), season"],
        ["<code>teams.csv</code>", "353", "one team in one competition", "team names"],
        ["<code>playing_eleven.csv</code>", "28,381", "one player in one match", "who played, batting order, captain, keeper, impact sub"],
        ["<code>competition_team_player_mapping.csv</code>", "6,413", "one player in one squad", "player names and squads"]], num=(1,))
    er = Flow(680, 230)
    er.node("c", 10, 20, 150, 60, "competitions", "comp_id · format · season", "v")
    er.node("t", 10, 140, 150, 60, "teams", "comp_id · team_id", "n")
    er.node("m", 250, 80, 170, 70, "matches", "match_id · comp_id · winner · knock-out · revised target", "b")
    er.node("b", 510, 10, 160, 90, "ball_by_ball", "match_id · innings · ball no. · striker · bowler · runs · wicket · extras", "p")
    er.node("x", 510, 130, 160, 50, "playing_eleven", "match_id · player_id", "n")
    er.node("s", 510, 190, 160, 34, "squad mapping", "", "n")
    er.edge("c", "m", "r", "l", label="comp_id").edge("t", "m", "r", "l", label="comp_id").edge("m", "b", "r", "l", label="match_id").edge("m", "x", "r", "l", label="match_id")
    vol = D["volume"]
    bars = [(y, [(vol[y].get("IPL", 0), PINK), (vol[y].get("T20I", 0), BLUE)]) for y in sorted(vol)]
    return chapter("2", "First contact", "Opening the data for the first time",
                   "Six CSV files arrived. Before planning anything we opened each one, counted rows, read the column names and looked for anything strange. This chapter is that first look.") + f"""
<h2>The six files</h2>
{files}
<p>The files connect through two keys. <code>match_id</code> links a ball to its match, and <code>comp_id</code> links a match to its competition. Everything else (team names, squads) is for labels.</p>
{fig(er.svg(), "<b>Figure 2.1</b> How the files join. The ball-by-ball file is the heart of the data; the others add context to each ball.")}
<h2>What we checked first, and what we found</h2>
<p>We used <code>pandas</code> (a Python library for tables) to load each file and ran simple counts. These are the facts that shaped the plan:</p>
{table(["Check", "What we found", "What it meant for us"], [
        ["Competitions by type", "134 T20I series, 5 IPL seasons, and 2 tournaments marked plain \"T20\": the Emerging Teams Asia Cup 2024 and Asia Cup Rising Stars 2025.", "The two \"T20\" events are A-team (under-23) cricket, not what the brief asks about. We later removed them."],
        ["Matches", "883 matches in <code>matches.csv</code>, but only 867 have balls.", "16 matches have no ball-by-ball rows, so there is nothing to analyse for them."],
        ["Innings numbers", "Innings 1 and 2 hold 200,961 balls; innings 3 and 4 hold 38 balls.", "Innings 3/4 are Super Overs. They follow different rules, so we dropped them."],
        ["Extras", "wide 7,714 · leg-byes 2,748 · no-ball (\"Overstep\") 576 · byes 529 · other no-balls 264 · penalty 1", "Wides and no-balls are not legal balls; we must count them separately."],
        ["Extra runs", "<code>extras1_runs</code> holds the extra runs on the ball (a wide that runs away for four byes shows 5); <code>extras_2_runs</code> holds byes taken off a no-ball.", "Team score = bat runs + both extras columns. We check this against the results in Chapter 3."],
        ["Dismissals", "Caught 7,557 · Bowled 1,775 · LBW 709 · Run out 600 · Stumped 214 · Hit wicket 17 · Retired out 6 · Obstructing 3", "Run outs and retirements are not the bowler's wicket. We separate bowler wickets from team wickets."],
        ["Pace or spin", "Pace 123,886 balls, spin 77,113.", "Useful context: we can compare players against pace and spin separately."],
        ["Ball speed", "<code>bowl_speed</code> is 0 in 38.7% of rows.", "Too patchy to use. We ignored it."],
        ["Results", "40 matches abandoned or no result; 74 results mention a tie or Super Over; 23 matches had a rain-revised target; 31 were knock-outs.", "No-result and tie matches cannot teach a win model who won. Rain rules change the target and the number of balls."]])}
{box("kid", "<p>Opening data is like unpacking a box of LEGO before building. You count the pieces, check the instructions are the right ones, and notice that a few pieces are missing. If you start building straight away, you find out halfway through that the wheel is not there.</p>")}
{box("warn", "<p>War-room lesson: an earlier copy of this file stored a <i>code</i> for the extras type in <code>extras1_runs</code> (every normal ball showed 6), so extra runs had to be approximated. The organisers' updated file holds real runs, and the whole analysis in this guide is re-run on it. Lesson: never trust a column name; look at the values next to each other, and test the rebuilt scores against the official results.</p>")}
<h2>The shape of the data after scoping</h2>
<p>After removing Super Overs and the two A-team events, we kept <b>837 matches</b> and <b>193,988 deliveries</b>: 87,673 IPL balls and 106,315 T20I balls, played by 824 different batters and 596 different bowlers from 2022 to 2026.</p>
{fig(panel("Matches per year", "IPL vs T20I after scoping", ch.stacked_bars(bars, 600, 260, legend=[("IPL", PINK), ("T20I", BLUE)]), 600, 260),
         "<b>Figure 2.2</b> Every IPL season has 71–74 matches. T20I volume changes with the international calendar.")}
{box("why", "<p><b>Why keep IPL and T20I together?</b> The brief covers both. Pooling roughly doubles the pressure sample for many players, which matters because samples are small. To keep it fair, the competition is a feature in every model, so a T20I ball is compared with T20I balls and an IPL ball with IPL balls. We also re-ran the final lists on IPL only and T20I only as a robustness check (Chapter 15).</p>")}
</section>"""


# =============================================================================================== 3
def ch3():
    ex = D["example"]["balls"][-6:]
    rows = [[b["ov"], b["s"], b["b"], b["need"], b["left"], b["w"], b["runs"], f'{b["wp"]:.0%}', f'{b["pi"]:.2f}'] for b in ex]
    st = Flow(680, 200)
    st.node("raw", 6, 70, 130, 70, "Raw ball row", "runs, extras type, wicket, striker, bowler", "n")
    st.node("leg", 166, 4, 170, 60, "Legal ball?", "not a wide or no-ball", "b")
    st.node("run", 166, 70, 170, 60, "Runs for team, batter, bowler", "three different counts", "b")
    st.node("wk", 166, 136, 170, 60, "Whose wicket?", "team / batter / bowler", "b")
    st.node("cum", 366, 70, 140, 70, "Running totals", "score, wickets, legal balls before this ball", "v")
    st.node("state", 546, 50, 128, 110, "Match state", "balls left · wickets left · runs needed · required rate · phase · target", "p")
    for k in ("leg", "run", "wk"):
        st.edge("raw", k).edge(k, "cum")
    st.edge("cum", "state")
    return chapter("3", "Cleaning", "Cleaning: rebuilding every ball",
                   "The raw file says what happened on each ball. A pressure model needs to know the situation <i>before</i> each ball: the score, wickets, balls left and, in a chase, the runs still needed. None of that is stored. We rebuilt it (program <code>s01_prepare.py</code>).") + f"""
{fig(st.svg(), "<b>Figure 3.1</b> From a raw row to the match state before the ball.")}
<h2>Step 1: which balls count</h2>
<p>A <b>legal ball</b> is any delivery that is not a wide or a no-ball. Only legal balls use up one of the 120 balls in an innings. A no-ball still counts as a ball <i>faced</i> by the batter (he can hit it), but a wide does not.</p>
{eq("is_legal = not (wide or no-ball)\\nfaced    = not wide")}
<h2>Step 2: three different run counts</h2>
<p>The same delivery means different things to the team, the batter and the bowler, so we count runs three ways:</p>
{table(["Count", "Formula", "Why"], [
        ["Team runs", "bat runs + <code>extras1_runs</code> (wides, no-ball penalty, byes, leg-byes, penalty runs) + <code>extras_2_runs</code> (byes off a no-ball)", "Needed to rebuild the score."],
        ["Batter runs", "runs off the bat only", "A batter is not credited with wides or byes."],
        ["Bowler runs", "bat runs + all runs from a wide + the no-ball penalty", "Byes and leg-byes are the keeper's or nobody's fault, so the bowler is not charged."]])}
<h2>Step 3: three different wickets</h2>
<ul><li><b>Team wicket</b>: any dismissal except \"retired out\" (it reduces wickets in hand).</li>
<li><b>Batter out</b>: the striker himself was dismissed (in a run out, sometimes the non-striker is out instead).</li>
<li><b>Bowler wicket</b>: every dismissal except run outs, retirements and obstructing the field.</li></ul>
<h2>Step 4: the state before every ball</h2>
<p>We sorted balls by match, innings and ball number, then used running totals. The trick is to subtract the current ball, so that each row shows the situation <i>before</i> the ball was bowled:</p>
{eq("score_before = (running total of team runs) - team runs on this ball\\nwkts_before  = (running total of team wickets) - wicket on this ball\\nballs_left   = scheduled balls - legal balls already bowled\\nruns_needed  = target - score_before            (chases only)\\nrequired rate = 6 x runs_needed / balls_left\\nphase        = Powerplay (overs 1-6) / Middle (7-15) / Death (16-20)")}
<p><b>Rain-reduced matches.</b> When overs are cut, <code>matches.csv</code> stores the revised overs and target. We use those instead of 120 balls and \"first-innings total + 1\", so a chase of 60 off 5 overs is treated as exactly that.</p>
<p><b>Elo strength.</b> We also give every team a strength rating before each match (Elo, explained in Chapter 5), so a mismatch can be recognised.</p>
<h2>A real example: the last six balls of a chase</h2>
<p>Kolkata Knight Riders chasing 156 against Rajasthan Royals on 19 April 2026. After cleaning, each ball carries its full state. The last two columns come from the models in Chapters 5–6.</p>
{table(["Over", "Striker", "Bowler", "Need", "Balls left", "Wkts down", "Runs", "Win prob. before", "Pressure Index"], rows, num=(3, 4, 5, 6, 7, 8))}
<p>Rinku Singh needed 1 run off 3 balls after a dot ball, and hit a six. The rebuilt state makes it possible to say exactly how much that moment mattered.</p>
<h2>Step 5: a quality check we could not skip</h2>
<p>If the rebuilding is right, every chase the batting team won should reach the target. We tested this on all winning chases.</p>
{stats([("99.5%", "of winning chases reach the target when rebuilt (404 of 406)"), ("2", "exceptions, both rain-reduced DLS games"), ("Why", "the feed does not store those two revised targets"), ("Effect", "negligible; every other chase state is exact")])}
{box("why", "<p>We also checked the other direction: when the team batting first won \"by X runs\", the rebuilt totals give exactly X in 99.5% of matches. So the extras are now counted correctly.</p>")}
<h2>Step 6: who won? (the label)</h2>
<p>For every ball we store whether the batting team went on to win. Ties and no-results get no label: a model learning \"who wins from here\" should not learn from matches nobody won.</p>
{box("kid", "<p>Cleaning is like writing the score on a whiteboard after every single ball. The raw file only tells you what happened on each ball. We replay the match in order and keep the whiteboard up to date, so for any ball we can read off \"KKR need 1 off 3, 6 down\".</p>")}
</section>"""


# =============================================================================================== 4
def ch4():
    plan = table(["Problem", "Our idea", "Where"], [
        ["\"Pressure\" has no agreed definition; death overs are not always pressure", "Let a win-probability model measure how much each ball can change the result", "Ch 5–7"],
        ["Openers and finishers face different balls; a run is worth more in a tight chase", "Compare each ball with an average player in the same spot; charge wickets by their real cost", "Ch 8"],
        ["Good players look good everywhere", "Score pressure level minus the player's own usual level", "Ch 10"],
        ["Most players have fewer than 300 pressure balls; one hot week tops a raw table", "Shrink noisy numbers toward the average; minimum sample rules", "Ch 9"],
        ["Any formula can be tuned to look right; there is no answer key for \"clutch\"", "Test on matches the method never saw; fix the choosing rule before seeing results", "Ch 11–13"],
        ["A ranking is not a squad plan; most stars are under contract", "Find RR's pressure gaps; match players to gaps and to availability", "Ch 17"]])
    pipe = Flow(680, 300)
    S = [("s01", "s01 Prepare", "clean, join, match state", "b", 10, 10), ("s02", "s02 Pressure", "Elo, win prob., leverage, PI", "p", 180, 10),
         ("s03", "s03 Value", "expected outcomes, wicket cost, value per ball", "b", 350, 10), ("s05", "s05 Validate", "definitions, thresholds, reliability → weights", "v", 520, 10),
         ("s04", "s04 Solution A", "context-adjusted shrunk ratings", "b", 520, 120), ("B", "Solution B", "pressure SR, economy + WPA", "v", 350, 120),
         ("s07", "s07 Tournament", "79 candidates × 36 splits, unseen matches", "p", 180, 120), ("s08", "s08 Final lists", "bootstrap + specification checks", "g", 10, 120),
         ("s09", "s09 Report", "methodology PDF", "n", 10, 225), ("dash", "Dashboard + verifier", f"{CHECKS} checks", "j", 180, 225), ("deck", "Deck + this guide", "", "n", 350, 225)]
    for k, a, b_, kind, x, y in S:
        pipe.node(k, x, y, 150, 74, a, b_, kind)
    pipe.edge("s01", "s02").edge("s02", "s03").edge("s03", "s05").edge("s05", "s04", "b", "t").edge("s04", "s07", "l", "r", ta=0.3, tb=0.3)
    pipe.edge("B", "s07", "l", "r", tb=0.7, ta=0.5).edge("s07", "s08", "l", "r").edge("s08", "s09", "b", "t").edge("s08", "dash", "b", "t", tb=0.3).edge("s08", "deck", "b", "t", tb=0.2, color="#c9bfd6")
    pipe.edge("s03", "B", "b", "t", color=VIO, dash=True, ta=0.5)
    return chapter("4", "Thinking before coding", "The plan before any modelling",
                   "With the data cleaned we wrote a plan: the problems we expected, the idea for each, and the rules for deciding between ideas. This page is that plan, almost word for word.") + f"""
{plan}
<h2>Four rules we promised ourselves</h2>
<ol><li><b>Decide by evidence on unseen matches.</b> A method is better only if it picks players who do well in matches it was not built from.</li>
<li><b>Write the choosing rule before seeing results.</b> Otherwise you keep tuning until the list looks \"right\".</li>
<li><b>Keep every step reproducible.</b> One command rebuilds everything; one settings file (<code>config.py</code>) holds every tunable number; the random seed is fixed at 42.</li>
<li><b>Show the uncertainty.</b> Every ranked player gets a probability of being top 10, not just a rank.</li></ol>
{fig(pipe.svg(), "<b>Figure 4.1</b> The pipeline. Each box is a Python program in <code>pipeline/src</code>. Solution B (dashed) was built separately and joined at the tournament.")}
{box("kid", "<p>Building a model without a plan is like cooking without a recipe and tasting only at the end. We wrote down the recipe and, more importantly, how we would taste: \"the dish is good if people who never saw it being made like it\". In our case, the people who never saw it are matches the model never used.</p>")}
<h2>Tools we used and why</h2>
{table(["Tool", "Used for", "Why this one"], [
        ["Python 3, pandas, NumPy", "loading, cleaning, all tables", "standard, readable, free"],
        ["LightGBM", "win probability, outcome and expected-runs models", "fast on 200k rows, handles curved relationships, supports monotone constraints"],
        ["scikit-learn", "grouped cross-validation, AUC, Brier score", "standard evaluation tools"],
        ["SciPy", "Spearman rank correlation (reliability)", "standard statistics"],
        ["Parquet files", "saving each step's table", "fast and keeps column types"],
        ["Vanilla JavaScript + SVG", "the dashboard", "one file, works offline, nothing to install"]])}
</section>"""


# =============================================================================================== 5
def ch5():
    att = Flow(680, 210)
    att.node("a1", 10, 20, 200, 120, "Attempt 1 · Rules", "Pressure if: chase and required rate ≥ 9, or overs 17–20, or 4+ down inside 10 overs.", "r")
    att.node("a2", 240, 20, 200, 120, "Attempt 2 · Stress score", "Hand-weighted mix: required-rate gap, wickets lost, recent wickets, death overs, closeness.", "y")
    att.node("a3", 470, 20, 200, 120, "Attempt 3 · Leverage", "How much can THIS ball change the chance of winning? Measured by a win-probability model.", "g")
    att.edge("a1", "a2", label="too blunt").edge("a2", "a3", label="weights are guesses")
    att.text(10, 170, "Flags 42% of balls; treats every death over the same.", 10, BAD)
    att.text(240, 170, "Better, but the weights are our opinion.", 10, WARN)
    att.text(470, 170, f"Chosen: {DEC}× its share of decisive swing.", 10, GOOD)
    cv = Flow(680, 170)
    for i in range(5):
        for j in range(5):
            kind = "p" if i == j else "n"
            cv.node(f"c{i}{j}", 110 + j * 112, 8 + i * 31, 104, 26, "test" if i == j else "train", "", kind, fs=9, align="center")
        cv.text(10, 26 + i * 31, f"Round {i + 1}", 10, INK, weight=700)
    cal = D["calibration"]
    return chapter("5", "Defining pressure", "What is pressure? Three attempts",
                   "We tried three definitions, from the most obvious to the most careful. The winner measures pressure with a model of who is going to win. This chapter builds that model from scratch.") + f"""
{att.svg()}
<h2>Attempts 1 and 2: rules and hand weights</h2>
<p>The obvious rule (death overs, a high required rate, an early collapse) is easy to explain, but it is blunt. Every ball in overs 17–20 counts as pressure, even when a team needs 4 off 18 balls with 8 wickets left. It flags 42% of all balls.</p>
<p>The stress score mixes the same ingredients with weights (0.35 for the required-rate gap, 0.25 for wickets lost and so on). It is smarter, but the weights are our guesses. Change them a little and the list of pressure balls changes.</p>
{box("kid", "<p>Asking \"is this a pressure ball?\" is really asking \"could this ball decide the match?\". So instead of guessing, we built a machine that answers a simpler question for every ball: <b>what is each team's chance of winning right now?</b> If one ball can swing that chance a lot, the ball is high pressure.</p>")}
<h2>Attempt 3: a win-probability model</h2>
<p>A win-probability (WP) model looks at the situation before a ball and outputs the chance that the batting team wins. We trained two, one per innings, because the questions are different:</p>
{table(["Model", "Inputs", "Must be true (monotone rule)"], [
        ["First innings", "balls left, wickets left, score so far, Elo difference", "more balls left, more wickets, more runs and a stronger team can only raise the chance"],
        ["Chase", "balls left, wickets left, runs needed, Elo difference", "more runs needed can only lower the chance; more balls and wickets can only raise it"]])}
<p>End states are set by rule, not by the model: a chase that has reached the target is 100%, a chase with no balls or wickets left is 0%, and a chase that finishes level is 50% (a Super Over is a coin flip).</p>
<h3>The learning method: gradient boosting (LightGBM)</h3>
{box("kid", "<p>Gradient boosting builds hundreds of tiny decision trees one after another. The first tree makes a rough guess (\"teams needing a lot with few balls left usually lose\"). The second tree looks only at the mistakes of the first and tries to fix them. The third fixes what is still wrong, and so on. After 300 small trees, the combined guess is very good. Each tree on its own is weak; together they are strong.</p>")}
<p>We used 300 trees, a learning rate of 0.05 (each tree's correction is scaled down to 5%, so no single tree can over-react), at least 200 balls in every leaf (so no rule is learned from a handful of balls), and <b>monotone constraints</b>. A monotone constraint forces a sensible direction: for example, needing more runs can never increase the chasing side's chance. Without it, a flexible model can learn silly bumps from noise.</p>
<h3>Team strength: Elo</h3>
<p>Two equal teams at 100 for 2 have very different chances from India at 100 for 2 against an Associate side. We add each team's Elo rating, calculated from results only, before each match.</p>
{box("math", eq("Every team starts at 1500.\\nExpected result for A:  E_A = 1 / (1 + 10^((R_B - R_A) / 400))\\nAfter the match:      R_A_new = R_A + 24 x (result - E_A)      result = 1 win, 0 loss") +
             "<p><b>Example.</b> A is rated 1600, B is 1500. E_A = 1 / (1 + 10<sup>-0.25</sup>) = 0.64. If A wins, A gains 24 × (1 − 0.64) = 8.6 points and B loses 8.6. If A loses, A drops 24 × 0.64 = 15.4. Upsets move ratings more.</p>")}
<h3>Never let a model mark its own homework: grouped cross-validation</h3>
<p>If a model is trained on a match and then asked about that same match, it already \"knows\" the ending. So we split the 837 matches into five groups. Each group's balls are scored by a model trained only on the other four groups. Every ball's win probability is therefore <b>out-of-fold</b>: produced by a model that never saw that match.</p>
{fig(cv.svg(), "<b>Figure 5.1</b> Five-fold cross-validation grouped by match. Each round, one fifth of the matches (pink) is scored by a model trained on the rest.")}
<h3>Is the model any good?</h3>
{stats([(f'{WPM[1]["auc"]:.3f}', f'AUC in chases: the model ranks winners above losers {WPM[1]["auc"]:.0%} of the time'), (f'{WPM[0]["auc"]:.3f}', "AUC in first innings: harder, no target yet"), (f'{WPM[1]["brier"]:.3f}', "Brier score in chases (0 = perfect, 0.25 = coin flip)"), (f'{WPM[0]["brier"]:.3f}', "Brier score in first innings")])}
{box("math", "<p><b>AUC</b> = pick a random ball from a team that went on to win and one from a team that lost. AUC is the chance the model gave the winner the higher probability. 0.5 is guessing, 1.0 is perfect.</p><p><b>Brier score</b> = average of (predicted probability − what happened)², where what happened is 1 or 0. Lower is better.</p><p><b>Calibration</b> = when the model says 70%, does the team win about 70% of the time? Figure 5.2 checks this.</p>")}
{fig('<div class="grid2">' + panel("Calibration", "predicted (x) vs actual win rate (y)", ch.calibration(cal, 320, 300), 320, 300) + box("why", "<p>Points close to the diagonal mean the probabilities can be taken at face value. The chase line hugs the diagonal. The first-innings line drifts below it at the top (when the model says 94% the team wins about 87% of the time), so first-innings pressure is flatter and less certain. We report this rather than hide it.</p><p>First innings is genuinely harder: without a target, nobody knows yet what a good score is.</p>") + '</div>',
         "<b>Figure 5.2</b> Calibration of the win-probability models (10 bins, out-of-fold). Pink = chase, blue = first innings.")}
</section>"""


# =============================================================================================== 6
def ch6():
    toy = table(["Possible next ball", "Chance (outcome model)", "Win prob. after", "Swing |after − now|", "Chance × swing"], [
        ["dot", "0.35", "38%", "7", "2.45"], ["1 run", "0.33", "47%", "2", "0.66"], ["2 runs", "0.07", "52%", "7", "0.49"],
        ["4", "0.10", "63%", "18", "1.80"], ["6", "0.05", "75%", "30", "1.50"], ["wicket", "0.07", "28%", "17", "1.19"],
        ["wide / no-ball", "0.03", "50%", "5", "0.15"], ["<b>Total = expected swing</b>", "1.00", "", "", "<b>8.24 points</b>"]], num=(1, 2, 3, 4))
    ex = D["example"]
    return chapter("6", "Defining pressure", "Leverage and the Pressure Index",
                   "With a win-probability for every ball, we can measure how much the <i>next</i> ball can change it. That is leverage. Leverage, with a small bonus for knock-out matches, is our Pressure Index.") + f"""
<h2>Leverage: the expected swing of one ball</h2>
<p>Before a ball is bowled we do not know what will happen. It could be a dot, a single, a four, a six or a wicket. A second model, the <b>outcome model</b>, gives the chance of each outcome in the current situation (8 classes: 0, 1, 2, 3, 4, 6 runs, wicket, or a wide/no-ball). For each outcome we ask the WP model what the chance of winning would become. Leverage is the average size of the swing.</p>
{box("math", eq("Leverage_raw(state) =  sum over outcomes o of  P(o | state) x | WP(state after o) - WP(state now) |\\nLeverage            =  Leverage_raw / average Leverage_raw over all 193,988 balls       (1.0 = an average ball)\\nPressure Index (PI) =  Leverage x 1.15 in knock-out matches,  x 1.00 otherwise") +
             "<p><b>Teaching example</b> (numbers made up and rounded so the arithmetic is easy to follow). A chase, win probability now 45%:</p>" + toy +
             "<p>The expected swing is 8.2 percentage points. Across all 193,988 real balls the average expected swing is 1.4 points (this number is real). So this ball's leverage is 8.24 / 1.4 ≈ 5.9: it carries almost six times the weight of a normal ball.</p>")}
{box("kid", "<p>Think of a see-saw with the two teams on it. Most balls barely move it. In a tight finish, one ball can slam it down on one side. Leverage measures how hard the next ball can push the see-saw, before we know which way it will go. That is why it measures <b>pressure</b> and not <b>performance</b>: it is the same for every player who could face that ball.</p>")}
<h3>Three small but important details</h3>
<ul><li><b>Knock-out bonus (×1.15).</b> A semi-final is worth more than a league game with the same scoreboard. The bonus is deliberately small so it nudges rather than dominates.</li>
<li><b>A cap on extreme values.</b> In rain-shortened finishes leverage can explode. We cap leverage at its 99.5th percentile (6.44 times an average ball). That is why every ball in the last over of the KKR chase shows a Pressure Index of exactly 6.44.</li>
<li><b>The first-innings end.</b> Our first version switched to the chase model on the last ball of the first innings. That created fake spikes of leverage on that one ball. We now score first-innings end states with the first-innings model (see the box below).</li></ul>
{box("mist", "<p><b>The last-ball spike.</b> In iteration 1 the top-pressure balls were full of \"last ball of the first innings\". A batter blocking the 120th ball showed huge leverage. The cause: we valued the state after that ball with a different model (the chase model), so even a dot \"changed\" the win probability. Fix: use the same model on both sides of the swing. Lesson: when something tops a list for a boring reason, look for a bug before celebrating.</p>")}
<h2>Seeing it on a real match</h2>
{fig(panel(f'{ex["bat"]} v {ex["bowl"]}, {ex["date"]}', f'Line = chasing side\'s win probability before each ball. Bars = Pressure Index; pink = top 30% of all balls.', ch.chase_chart(ex["balls"], 900, 400, D["pi_cut"]), 900, 400),
         "<b>Figure 6.1</b> Early balls barely move the result, so their Pressure Index is low. As the chase tightens every ball can swing it and the bars turn pink. The final over carries the most pressure.")}
<h2>Where is pressure in a T20 innings?</h2>
<div class="grid2">{panel("First innings", "average PI by over × wickets lost", ch.heatmap(D["pressure_map"]["1"], 330, 260), 330, 260)}{panel("Chase", "average PI by over × wickets lost", ch.heatmap(D["pressure_map"]["2"], 330, 260), 330, 260)}</div>
<p class="small m"><b>Figure 6.2</b> Darker pink = more pressure. In a chase, pressure climbs with both the over and the wickets lost: the same over is far more pressured at 4–5 down than at 0–1 down. The first innings is flatter.</p>
<h2>Drawing the line: the top 30%</h2>
<p>To compare \"pressure\" with \"usual\" we need two groups. A ball is <b>high pressure</b> if its Pressure Index is in the top 30% of all balls, which means PI ≥ <b>{D["pi_cut"]:.3f}</b>. That flags 58,197 balls. The <b>usual</b> group is the bottom 50% (96,994 balls). The middle 20% is left out, so the two groups are clearly different.</p>
{fig(panel("How pressure is distributed", "all 193,988 balls by Pressure Index (pink = top 30%)", ch.hist(D["pi_hist"], 640, 260, D["pi_cut"]), 640, 260),
         f"<b>Figure 6.3</b> Most balls sit below an average ball (median PI {D['pi_median']:.2f}). A long tail of high-pressure balls carries most of the match-deciding swing. The spike at the right is the capped group (PI ≥ 4).")}
{box("why", "<p><b>Why 30% and not 10% or 50%?</b> Chapter 7 shows the test. In short: the ratings became about as repeatable as they get from 25–30% upward, while a smaller cut-off left too few players with enough balls. 30% keeps about 150 players per role in the running. It was chosen by a measured plateau, not because it gave the \"best\" list.</p>")}
<h3>A second view of the same leverage (used by Solution B)</h3>
<p>Solution B (Chapter 12) ranks each ball's leverage <b>within its own innings</b> as a percentile from 0 to 100. A ball at the 85th percentile is in the top 15% of its innings. This stops a whole high-scoring chase from looking like pressure from the first ball. Both views come from the same leverage number.</p>
</section>"""


# =============================================================================================== 7
def ch7():
    defs = D["definitions"]
    lab = {"PI": "Our Pressure Index", "HEUR": "Hand-weighted stress score", "NAIVE": "Rule-based"}
    rows = [(lab[d_["definition"].split(" ")[0]], d_["share of total |WPA| in flagged balls"] * 100, d_["decisiveness ratio"], d_["share of balls flagged"] * 100) for d_ in defs]
    beh = [[lab[d_["definition"].split(" ")[0]], f'{d_["share of balls flagged"]:.0%}', f'{d_["share of total |WPA| in flagged balls"]:.0%}', f'<b>{d_["decisiveness ratio"]:.2f}×</b>',
            f'{d_["dismissal % (pressure)"]:.2f}% / {d_["dismissal % (routine)"]:.2f}%', f'{d_["run rate (pressure)"]:.2f} / {d_["run rate (routine)"]:.2f}',
            f'{d_["boundary % (pressure)"]:.1f}% / {d_["boundary % (routine)"]:.1f}%'] for d_ in defs]
    th = table(["Pressure = top…", "Batters ρ", "Bowlers ρ", "Batters eligible", "Bowlers eligible"],
               [[r["top_share"], f'{r["quality_rho"]:.2f}', f'{o["quality_rho"]:.2f}', r["n_players"], o["n_players"]] for r, o in zip(D["threshold"][0::2], D["threshold"][1::2])], num=(1, 2, 3, 4))
    return chapter("7", "Proof", "Checking the definition",
                   "A definition of pressure is only useful if the balls it flags really are the ones that decide matches. We tested all three definitions on the same yardstick.") + f"""
<h2>Test 1: does it find the decisive balls?</h2>
<p>For every ball we know how much the win probability actually moved (the <b>win probability added</b>, WPA). Add up the size of all those moves and you have the total \"match-deciding swing\" in the data. A good definition should catch much more than its fair share of that swing.</p>
{box("math", eq("decisiveness = (share of all |WPA| that falls on flagged balls) / (share of balls flagged)") + f"<p>If a definition flags 30% of balls and those balls hold 30% of the swing, its decisiveness is 1.0 (no better than picking at random). Ours flags 30% of balls holding {DEF0['share of total |WPA| in flagged balls'] * 100:.0f}% of the swing: {DEF0['share of total |WPA| in flagged balls']:.3f} / 0.30 = <b>{DEC}</b>.</p>")}
{fig(panel("Share of match-deciding swing caught", "and the ratio to the share of balls flagged", ch.def_bars(rows, 640, 260), 640, 260), "<b>Figure 7.1</b> Leverage catches about twice its share of decisive swing. The two hand-made definitions catch only 1.2–1.3 times their share.")}
<h2>Test 2: does play actually change on those balls?</h2>
{table(["Definition", "Balls flagged", "Swing caught", "Decisiveness", "Dismissal % pressure / usual", "Run rate pressure / usual", "Boundary % pressure / usual"], beh)}
<p>Two lessons hide in this table. Under our definition, <b>pressure balls are not slower</b>: the run rate is a little higher ({DEF0["run rate (pressure)"]:.2f} vs {DEF0["run rate (routine)"]:.2f}) and boundaries are slightly more common. But <b>mistakes cost more</b>: dismissals are a bit more frequent and each one swings the result further. The rule-based definition shows a bigger jump in dismissals only because it is mostly death overs, where everyone slogs. That is a phase effect, not pressure.</p>
{box("kid", "<p>A metal detector that beeps at everything is useless, and so is one that never beeps. The decisiveness test asks: when our detector beeps, how often is there really treasure? Ours finds about twice as much treasure per beep as the other two.</p>")}
<h2>Test 3: how big should the pressure group be?</h2>
<p>We computed every player's pressure rating twice, on two random halves of the matches, and measured how well the two halves agreed (split-half reliability, explained fully in Chapter 11). We repeated this for cut-offs from the top 40% to the top 15%. This test used a looser minimum (100 pressure balls, 8 matches), so it keeps more players than the final eligibility rule.</p>
{th}
{fig(panel("Reliability by cut-off", "split-half Spearman ρ of player pressure ratings", ch.threshold(D["threshold"], 640, 260), 640, 260), f"<b>Figure 7.2</b> Reliability sits on a plateau around ρ ≈ {min(t['quality_rho'] for t in D['threshold']):.2f}–{max(t['quality_rho'] for t in D['threshold']):.2f} for every cut-off. A smaller group does not make ratings more repeatable; it just leaves fewer eligible players.")}
{box("why", "<p>Because reliability is flat, the cut-off should keep as many qualified players as possible while still being clearly \"pressure\". The top 30% keeps about 150 players per role and is where both batters and bowlers are near the top of the plateau. The top 15% would leave only about 90 players, which removes many genuine regulars.</p>")}
<h2>Where the pressure balls are</h2>
{stats([(f'{D["hp_phase_share"]["PP"]:.0f}%', "of pressure balls are in the powerplay"), (f'{D["hp_phase_share"]["MID"]:.0f}%', "in the middle overs"), (f'{D["hp_phase_share"]["DEATH"]:.0f}%', "at the death"), ("58,197", "pressure balls in total")])}
<p>This surprises most people. Pressure is not only a death-overs thing: an early wicket in a big chase, or a tight middle-overs squeeze, can matter as much as the 19th over. This is the clearest evidence that the rule-based definition (\"death overs = pressure\") was wrong.</p>
</section>"""
