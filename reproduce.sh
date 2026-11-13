#!/usr/bin/env bash
# One command, end to end: raw CSVs -> pressure model -> ratings -> final top 10 -> report -> dashboard.
#   ./reproduce.sh              full run (pipeline ~45-60 min on 2 CPUs, then dashboard ~2 min)
#   ./reproduce.sh dashboard    skip the pipeline; rebuild + verify the dashboard from the committed outputs
# Raw data is read from data/raw (override with SUPERR_DATA=/path/to/csvs).
set -euo pipefail
cd "$(dirname "$0")"
export PYTHONWARNINGS=ignore

if [[ "${1:-all}" != "dashboard" ]]; then
  echo "== [1/2] pipeline (seed 42)"
  bash pipeline/run_all.sh
  echo
  echo "Final lists (pipeline/outputs/FINAL_TOP10_HYBRID.csv):"
  cat pipeline/outputs/FINAL_TOP10_HYBRID.csv
fi

echo
echo "== [2/2] dashboard"
cd dashboard
python3 -I scripts/build_data.py      ../pipeline/outputs "${SUPERR_DATA:-../data/raw}" .
python3 -I scripts/build_watchlist.py ../pipeline/outputs .
python3 -I scripts/verify_dashboard.py ../pipeline/outputs .
python3 scripts/build_single_file.py
echo
echo "Done. Open dashboard/dist/under-pressure-rating.html in a browser."
