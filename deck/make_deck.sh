#!/usr/bin/env bash
# Rebuild the presentation from the pipeline outputs:
#   build/data.json -> build/deck.html -> PNG slides + PDF -> PPTX -> dashboard/deck/ (web viewer + downloads)
# Needs: Python packages from ../requirements.txt + playwright (python -m playwright install chromium),
#        Node 18+ with `npm install` run in this folder (pptxgenjs, fonts), and `pip install qrcode`.
set -euo pipefail
cd "$(dirname "$0")"
OUT=../dashboard/deck
PDF=Under_Pressure_Rating_SupeRR_S2.pdf
PPTX=Under_Pressure_Rating_SupeRR_S2.pptx
python3 prep.py && python3 prep2.py          # numbers for every chart, from ../pipeline/outputs
python3 build.py                              # build/deck.html (23 slides)
python3 render.py all                         # build/png/slide-NN.png (3200x1800) + build/deck.pdf
python3 manifest.py                           # titles, speaker notes, link hotspots
node pptx.js "build/$PPTX"
zip -dq "build/$PPTX" '*/' 2>/dev/null || true
mkdir -p "$OUT"
cp build/deck.pdf "$OUT/$PDF"
cp "build/$PPTX" "$OUT/$PPTX"
python3 build.py viewer "$OUT" "$PDF" "$PPTX"
echo "Deck ready: $OUT/index.html, $OUT/$PDF, $OUT/$PPTX"
