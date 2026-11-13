# SupeRR Selector S2 - Round 1: HYBRID pressure-performance ratings

Combines solution A (context-adjusted, shrunk pressure rating with usual-level and consistency
components) with solution B (multi-cut-off pressure strike rate, shrunk pressure economy + WPA,
held-out maximin method selection, IPL+T20I scope). A held-out tournament on unseen matches
chose the blend for each role.

## Final lists (submit in this order) - outputs/FINAL_TOP10_HYBRID.csv
Batters: Vaibhav Sooryavanshi, Priyansh Arya, Heinrich Klaasen, Abhishek Sharma, Suryakumar Yadav, Travis Head, Rovman Powell, Finn Allen, Phil Salt, Dewald Brevis
Bowlers: Josh Hazlewood, Mujeeb Ur Rahman, Mohsin Khan, Abrar Ahmed, Jasprit Bumrah, Mahedi Hasan, Varun Chakravarthy, Taskin Ahmed, Mohammad Nawaz, Haris Rauf

## Recipes (both roles include the pressure-vs-usual-level comparison)
- Batters: 0.67 x z(A composite: rating + usual-level uplift + consistency) + 0.33 x z(B strike rate at leverage pct 75 & 85)
- Bowlers: 0.9 x z[0.2 z(A rating) + 0.8 z(B shrunk economy + WPA at pct 70)] + 0.1 x z(uplift: pressure minus own usual level), delivered-under-pressure gate
- Pool: >=150 pressure balls, >=12 matches, >=150 usual balls

## Run
From the repo root (see the top-level README for the full walkthrough):
```bash
pip install -r ../requirements.txt
./run_all.sh            # reads ../data/raw by default; ~45-60 min on 2 CPUs, seed 42
```
Set `SUPERR_DATA=/path/to/csvs` to read the raw CSVs from somewhere else.
Report: outputs/SupeRR_Selector_Round1_HYBRID_Methodology_Report.pdf
Tournament: outputs/hyb_selection.csv, hyb_cells_*.csv; final tables: hyb_ratings_*.csv, hyb_specs_*.csv, hyb_evidence_*.csv

docs/: recorded development logs used in the report's iteration section (solution A version history, A-vs-B head-to-head).
