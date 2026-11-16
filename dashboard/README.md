# Under Pressure Rating: dashboard

An interactive view of the pipeline's results. Every number on screen is read from `../pipeline/outputs`;
`scripts/verify_dashboard.py` recomputes them independently and fails if any differ.

## Open it (no install)

- **Easiest:** double-click `dist/under-pressure-rating.html`. It is one self-contained file (data, photos and
  the report are inlined) and works offline; only the web fonts need internet.
- **From source:** serve this folder and open the page:
  ```bash
  cd dashboard
  python3 -m http.server 8000
  # open http://localhost:8000
  ```

Views (also reachable by URL hash `#/dashboard/<view>`):

| View | What it shows |
|---|---|
| `overview` | Featured top-3, pressure value trend, KPIs, pressure situations, per-match values |
| `batters`, `bowlers` | Full ranked tables (official order from `FINAL_TOP10_HYBRID.csv`), profile drawer |
| `model` | How the Pressure Index is built; the sliders use a labelled simplified surrogate and never change ranks |
| `compare` | Two players side by side |
| `matches` | Match-by-match pressure value |
| `watchlist` | 2025–26 recent-form players to consider (not the official list) and a Rajasthan Royals review |
| `reproduce` | The presentation (embedded, plus PDF/PPTX), GitHub and live links, step-by-step reproduction, annexure |
| `methodology` | Methodology summary and the full PDF report |
| `settings` | Display preferences |

## Rebuild from the pipeline outputs

Run from this folder (`dashboard/`). Needs the Python packages in `../requirements.txt`.

```bash
python3 -I scripts/build_data.py       ../pipeline/outputs ../data/raw .   # -> data/clutch_data.js
python3 -I scripts/build_watchlist.py  ../pipeline/outputs .               # -> data/watchlist.js
python3 -I scripts/verify_dashboard.py ../pipeline/outputs .               # ~10,000 checks, must print "0 failed"
python3 scripts/build_single_file.py                                       # -> dist/under-pressure-rating.html
```

Or from the repo root: `./reproduce.sh dashboard`.

## Files

```
index.html            entry page (loads css/, js/, data/)
css/                  styles.css (layout, theme), pages.css (per-view styles)
js/                   app.js (state, overview), pages.js (other views), charts.js (SVG charts), icons.js, main.js (router)
data/                 generated: clutch_data.js, watchlist.js, FINAL_TOP10_HYBRID.csv; links.js (GitHub/live URLs)
deck/                 presentation built by ../deck/make_deck.sh (viewer index.html, PDF, PPTX)
assets/               player photos (webp), RR logo, report PDF and figures copied from the pipeline
scripts/              build_data.py, build_watchlist.py, verify_dashboard.py, build_single_file.py
dist/                 the single-file build
```

## Notes

- **Clutch Rating** is a 0–100 min-max of the official score within the top 120. It is a display scale only;
  the official order is never re-sorted.
- **Pressure** everywhere means the report's definition: the top 30% of deliveries by Pressure Index.
- **Watchlist** = players ranked in the top 10 on 2025–26 data alone (≥120 pressure balls) who stay there in
  at least half of 1,000 bootstrap resamples and are not already in the official top 10. It is a recent-form
  view and does not change the official list.
- Players without a photo are shown with a monogram.
