# SupeRR Selector Season 2 · Round 1: Under Pressure Rating

**Goal:** identify the most reliable players under pressure, using the ball-by-ball data provided for the round
(IPL + T20I, 2022–2026: 837 matches, 193,988 deliveries).

This repository holds everything needed to reproduce our submission from the raw CSVs:

1. **Pipeline** (`pipeline/`): win-probability model → Pressure Index → context-adjusted value per ball →
   shrunk pressure ratings → held-out tournament that picks the final method → final top 10 → methodology report.
2. **Dashboard** (`dashboard/`): an interactive view of the same results. Every number on it is checked against
   the pipeline outputs.

## Final top 10

| # | Batters | Bowlers |
|---|---|---|
| 1 | Vaibhav Sooryavanshi | Josh Hazlewood |
| 2 | Priyansh Arya | Mujeeb Ur Rahman |
| 3 | Heinrich Klaasen | Mohsin Khan |
| 4 | Abhishek Sharma | Abrar Ahmed |
| 5 | Suryakumar Yadav | Jasprit Bumrah |
| 6 | Travis Head | Mahedi Hasan |
| 7 | Rovman Powell | Varun Chakravarthy |
| 8 | Finn Allen | Taskin Ahmed |
| 9 | Phil Salt | Mohammad Nawaz |
| 10 | Dewald Brevis | Haris Rauf |

Source of truth: [`pipeline/outputs/FINAL_TOP10_HYBRID.csv`](pipeline/outputs/FINAL_TOP10_HYBRID.csv).
Full method and evidence: [`pipeline/outputs/SupeRR_Selector_Round1_HYBRID_Methodology_Report.pdf`](pipeline/outputs/SupeRR_Selector_Round1_HYBRID_Methodology_Report.pdf).

---

## Quick look (no setup)

- **Dashboard:** download [`dashboard/dist/under-pressure-rating.html`](dashboard/dist/under-pressure-rating.html)
  and open it in any modern browser. It is a single self-contained file.
- **Results:** every table the report uses is already committed in `pipeline/outputs/`.

---

## Reproduce everything, step by step

### 1. Requirements

- Python **3.11 or newer** (tested on 3.13) and `git`.
- About 2 GB of free RAM and ~45–60 minutes on a 2-core machine for the full pipeline.
- Linux or macOS shell. On Windows, use WSL or Git Bash (or run the `python` commands below one by one).

### 2. Get the code and data

```bash
git clone https://github.com/sidhantiitian17/SupeRR-Selector-S2-Round1.git
cd SupeRR-Selector-S2-Round1
```

The six raw CSVs provided for the round are already in `data/raw/`:

| File | Contents |
|---|---|
| `ball_by_ball.csv` | One row per delivery |
| `matches.csv` | Match metadata (date, venue, result, stage) |
| `competitions.csv` | Competition list (IPL seasons, T20I series) |
| `teams.csv` | Team names per competition |
| `playing_eleven.csv` | Playing XIs |
| `competition_team_player_mapping.csv` | Squads and player names |

To use your own copy of the data, point `SUPERR_DATA` at its folder (file names may carry an uploader prefix
such as `4a8858f1-matches.csv`; both forms are accepted).

### 3. Install the Python packages

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

`requirements.txt` pins the exact versions the published results were produced with.

### 4. Run the pipeline and rebuild the dashboard

One command does all of it:

```bash
./reproduce.sh
```

This runs the pipeline steps below in order (random seed fixed at 42), prints the final lists, then rebuilds
and verifies the dashboard. It overwrites the files in `pipeline/outputs/` and `dashboard/data/` and `dashboard/dist/`,
so `git status` / `git diff` afterwards shows whether anything changed. In our from-scratch run it reproduced
the committed outputs exactly.

To run the steps by hand instead:

```bash
cd pipeline/src
python3 s01_prepare.py         # clean deliveries, rebuild match state, IPL + T20I scope
python3 s02_pressure.py        # LightGBM win-probability model -> leverage -> Pressure Index
python3 s03_value.py           # expected-outcome models -> context-adjusted value of every ball
python3 s05_validate.py        # validate pressure definitions, value lenses and rating models
python3 s04_rank.py            # solution A ratings (one parent of the hybrid)
python3 s07_hybrid_select.py   # held-out tournament: A vs B vs 45 hybrid candidates per role
python3 s08_hybrid_final.py    # final hybrid lists, bootstrap stability, specification checks
python3 s09_hybrid_report.py   # methodology report (PDF)
```

| Step | Main outputs (in `pipeline/outputs/`) |
|---|---|
| s01 | `deliveries.parquet` |
| s02 | `deliveries_pressure.parquet`, `wp_model_metrics.csv`, `wp_calibration.csv` |
| s03 | `deliveries_value.parquet` |
| s05 | `val_*.csv`, `weights.json` |
| s04 | `ratings_bat.csv`, `ratings_bowl.csv` |
| s07 | `hyb_selection.csv`, `hyb_cells_*.csv`, `hyb_tournament_raw.csv`, `hyb_chosen.json` |
| s08 | **`FINAL_TOP10_HYBRID.csv`**, `hyb_ratings_*.csv`, `hyb_specs_*.csv`, `hyb_evidence_*.csv` |
| s09 | `SupeRR_Selector_Round1_HYBRID_Methodology_Report.pdf`, `figures/` |

### 5. Check the results

- `pipeline/outputs/FINAL_TOP10_HYBRID.csv` should match the table at the top of this page.
- `./reproduce.sh` ends with `10172 checks, 0 failed` from the dashboard verifier, which recomputes every
  dashboard number from `deliveries_value.parquet` and the rating tables, and checks the methodology claims
  against the PDF text.
- Win-probability model quality (`wp_model_metrics.csv`): AUC 0.706 (1st innings), 0.896 (2nd innings).

---

## Run only the dashboard

If you just want to explore, or rebuild the dashboard from the committed outputs (about 2 minutes):

```bash
pip install -r requirements.txt
./reproduce.sh dashboard
```

Then open `dashboard/dist/under-pressure-rating.html`, or serve the source version:

```bash
cd dashboard && python3 -m http.server 8000     # open http://localhost:8000
```

Details on each view are in [`dashboard/README.md`](dashboard/README.md).

---

## How the method works (short version)

1. **Pressure Index.** A win-probability model (LightGBM, grouped cross-validation by match) gives the win
   probability before every ball. A ball's *leverage* is how much the result of that ball can swing it; the
   Pressure Index combines leverage with match stakes (knockouts count 1.15×). "Under pressure" means the top
   30% of deliveries by Pressure Index; that cut-off was chosen for reliability in `s05`.
2. **Value of each ball.** Runs and wickets are compared with what an average player would produce in the same
   situation (expected-outcome models; wicket cost depends on innings phase), so a run in the death overs of a
   tight chase is not worth the same as one in a dead rubber.
3. **Ratings.** Each player's pressure value is shrunk towards the league average according to sample size
   (Empirical Bayes), and compared with the same player's routine level, so a high rating means good under
   pressure, not just good overall. Eligibility: at least 150 pressure balls, 12 matches and 150 routine balls.
4. **Choosing the method.** Two complete solutions (A and B) and 45 blends were scored on matches they had not
   seen. The blend that held up best for each role became the final method (`hyb_chosen.json`).
5. **Stability.** 300 bootstrap resamples report how often each player stays in the top 10.

All tunable settings live in [`pipeline/src/config.py`](pipeline/src/config.py).

---

## Repository layout

```
README.md               this guide
requirements.txt        pinned Python packages
reproduce.sh            one-command end-to-end run
data/raw/               the six raw CSVs provided for the round
pipeline/
  run_all.sh            pipeline steps in order
  src/                  config.py, s01..s09 steps, ratings.py, hybrid.py
  docs/                 development logs used in the report's iteration section
  outputs/              committed results (parquet, CSV, JSON, figures, PDF report)
dashboard/
  index.html, css/, js/ dashboard source (vanilla JS + SVG, no build tools)
  data/                 generated data files
  assets/               player photos, logo, report and figures
  scripts/              build, verify and single-file packaging scripts
  dist/                 single-file dashboard
```

## Notes and limits

- Pressure samples are small for some players (a few hundred balls at most), which is why ratings are shrunk
  and bootstrap stability is reported alongside the ranks.
- The dashboard's Watchlist (2025–26 recent form) and Rajasthan Royals review are context only; they do not
  change the official top 10.
- The Pressure Model sliders in the dashboard use a simplified surrogate of the Pressure Index (labelled as
  such in the UI) and do not affect any rank.
