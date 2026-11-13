#!/usr/bin/env bash
# Reproduce the full HYBRID SupeRR Selector pressure analysis end-to-end (~45 min on 2 CPUs).
# Usage: ./run_all.sh   (reads <repo>/data/raw by default; override with SUPERR_DATA=/path/to/csvs)
set -euo pipefail
cd "$(dirname "$0")/src"
export PYTHONWARNINGS=ignore
python3 s01_prepare.py         # clean deliveries + match state (IPL + T20I scope)
python3 s02_pressure.py        # win-probability model -> leverage -> Pressure Index
python3 s03_value.py           # expected-outcome models -> per-ball context-adjusted value
python3 s05_validate.py        # validation of pressure definitions / lenses / models (solution A design)
python3 s04_rank.py            # solution A ratings (reference parent + components)
python3 s07_hybrid_select.py   # held-out tournament: A vs B vs 45 hybrid candidates per role
python3 s08_hybrid_final.py    # FINAL hybrid lists, bootstrap, specification support
python3 s09_hybrid_report.py   # hybrid methodology report (PDF)
