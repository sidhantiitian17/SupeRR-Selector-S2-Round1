"""Central configuration for the SupeRR Selector pressure-rating pipeline.

Every tunable used anywhere in the pipeline lives here so a reviewer can
reproduce (or perturb) the analysis by editing one file.
"""
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.environ.get("SUPERR_DATA", ROOT.parent / "data" / "raw"))  # default: <repo>/data/raw
OUT = ROOT / "outputs"
FIG = OUT / "figures"
OUT.mkdir(exist_ok=True)
FIG.mkdir(exist_ok=True)

FILES = {
    "balls": "ball_by_ball.csv",
    "matches": "matches.csv",
    "comps": "competitions.csv",
    "teams": "teams.csv",
    "xi": "playing_eleven.csv",
    "squads": "competition_team_player_mapping.csv",
}
# exact name first; otherwise accept an uploader prefix such as 4a8858f1-matches.csv
def path(key):
    p = DATA_DIR / FILES[key]
    if p.exists():
        return p
    cands = sorted(DATA_DIR.glob(f"*-{FILES[key]}"))
    if not cands:
        raise FileNotFoundError(f"{FILES[key]} not found in {DATA_DIR}")
    return cands[0]

SEED = 42

# Scope: the brief covers IPL and T20I. The two emerging-team (A-side) tournaments are excluded (adopted from solution B).
EXCLUDE_EMERGING = True

# ICC Full Members (team_id) - everything else in T20Is is an Associate
FULL_MEMBERS = {17, 18, 19, 20, 21, 22, 23, 25, 27, 28, 72, 78}
IPL_TEAMS = {1, 2, 3, 4, 5, 7, 8, 242, 3508, 3509}

# ---- pressure definition ----
HIGH_PRESSURE_QUANTILE = 0.70   # top 30% of deliveries by Pressure Index = "high pressure" (chosen by reliability, s05)
LOW_PRESSURE_QUANTILE = 0.50    # bottom 50% = "routine" baseline

# Currency of the pressure-performance rating: run value above expected (runs + wicket cost), chosen
# in s05 because it best predicts *future* pressure performance.  Match-level consistency uses the
# win-probability currency (WPA / LI) so both "how much" and "when it decided matches" are represented.
VALUE_LENS = "val"
CONSIST_LENS = "wpali"
MIN_UPLIFT_WEIGHT = 0.15   # floor so the brief's "vs usual level" comparison always counts (sensitivity-tested)
# rating model (chosen in s05 by split-half reliability + 2022-24 -> 2025-26 predictive validity):
#   "direct" = what the player actually did under pressure, EB-shrunk to the league mean
#   "hier"   = own overall level + shrunk pressure deviation (collapses to overall ability)
#   "blend"  = 50/50 of the two  <- chosen: most reliable & most predictive for batters, near-best for bowlers
MODEL = "blend"
BLEND_DIRECT = 0.5   # used when MODEL == "blend"

# ---- eligibility ----
MIN_PRESSURE_BALLS_BAT = 150    # legal balls faced in high-pressure states
MIN_PRESSURE_BALLS_BOWL = 150   # legal balls bowled in high-pressure states
MIN_PRESSURE_MATCHES = 12       # distinct matches with pressure involvement
MIN_BASELINE_BALLS = 150        # balls in routine states (needed for the 'vs usual' delta)

# ---- opposition strength weighting (balls vs Associates count for less) ----
OPP_WEIGHT = {"FULL": 1.0, "IPL": 1.0, "A": 0.8, "ASSOC": 0.5}

# ---- composite score weights (sensitivity-tested in 05_validate.py) ----
# fallback composite weights; the pipeline derives reliability-proportional weights in s05 (weights.json)
W_QUALITY = 0.55     # posterior pressure performance (per 100 balls)
W_UPLIFT = 0.20      # pressure performance minus own usual level (rise vs dip)
W_CONSIST = 0.25     # match-level reliability under pressure
BOOTSTRAP_ITERS = 300


def wicket_cost_by_phase():
    """Average state-dependent wicket cost (runs) by phase, read from the s03 output, rounded to 0.1."""
    import pandas as pd
    wc = pd.read_parquet(OUT / "deliveries_value.parquet", columns=["phase", "Wc"]).groupby("phase").Wc.mean()
    return {k: round(float(v), 1) for k, v in wc.items()}


def wicket_cost_text():
    w = wicket_cost_by_phase()
    return f"about {w['PP']:.1f} runs in the powerplay, {w['MID']:.1f} in the middle overs and {w['DEATH']:.1f} at the death"
