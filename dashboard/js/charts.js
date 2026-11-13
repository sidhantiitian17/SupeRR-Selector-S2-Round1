/* Dependency-free SVG charts with hover tooltips. Each chart returns an SVG string; elements carrying
 * data-tip="html" get the shared tooltip (wired once by ClutchCharts.wireTips). Crosshairs are CSS-only.
 * Categorical colours (validated for dark mode, ΔE ≥ 14 in normal vision, 3:1 contrast): pink, violet-blue, teal. */
(function (global) {
  "use strict";
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const SERIES = ["#e0409a", "#6f84f0", "#1fa88f"];
  const POS = "#e0409a", NEG = "#6b5b86";
  const tip = (html) => ` data-tip="${esc(html)}"`;
  const nice = (min, max, n = 4) => {
    const span = max - min || 1, raw = span / n, mag = Math.pow(10, Math.floor(Math.log10(raw)));
    const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((s) => s >= raw) || raw;
    const lo = Math.floor(min / step) * step, hi = Math.ceil(max / step) * step;
    const ticks = []; for (let v = lo; v <= hi + step * 0.001; v += step) ticks.push(+v.toFixed(6));
    return { lo, hi, ticks };
  };
  const fmt = (v, d = 0) => (Math.abs(v) >= 1000 ? v.toLocaleString("en", { maximumFractionDigits: d }) : v.toFixed(d));

  /** Smooth area chart with per-point crosshair and tooltip. pts: [{x label, v, tip}] */
  function areaChart(pts, o = {}) {
    if (!pts.length) return `<div class="empty">Not enough pressure balls for a trend yet.</div>`;
    const W = o.width || 600, H = o.height || 180, P = { t: 14, r: 16, b: 26, l: 42 };
    const iw = W - P.l - P.r, ih = H - P.t - P.b;
    const vals = pts.map((p) => p.v);
    let { lo, hi, ticks } = nice(Math.min(...vals, o.zero ? 0 : Infinity), Math.max(...vals, o.zero ? 0 : -Infinity), 4);
    const x = (i) => P.l + (pts.length === 1 ? iw / 2 : (i / (pts.length - 1)) * iw), y = (v) => P.t + ih - ((v - lo) / (hi - lo)) * ih;
    const xy = pts.map((p, i) => [x(i), y(p.v)]);
    let d = `M${xy[0][0]},${xy[0][1]}`;
    for (let i = 1; i < xy.length; i++) { const [x0, y0] = xy[i - 1], [x1, y1] = xy[i], cx = (x0 + x1) / 2; d += ` C${cx},${y0} ${cx},${y1} ${x1},${y1}`; }
    const base = Math.min(Math.max(y(0), P.t), P.t + ih);
    const area = `${d} L${xy[xy.length - 1][0]},${base} L${xy[0][0]},${base} Z`;
    const grid = ticks.map((t) => `<line x1="${P.l}" x2="${W - P.r}" y1="${y(t)}" y2="${y(t)}" class="grid${t === 0 ? " zero" : ""}"/><text x="${P.l - 8}" y="${y(t) + 4}" class="axis" text-anchor="end">${fmt(t, Math.abs(hi - lo) < 6 ? 1 : 0)}</text>`).join("");
    const step = Math.max(1, Math.ceil(pts.length / Math.max(2, Math.floor((W - P.l - P.r) / 74))));   // ~74px per label, counted back from the last point
    const labels = pts.map((p, i) => ((pts.length - 1 - i) % step === 0) ? `<text x="${x(i)}" y="${H - 6}" class="axis" text-anchor="middle">${esc(p.x)}</text>` : "").join("");
    const cw = iw / Math.max(pts.length - 1, 1);
    const hits = pts.map((p, i) => `<g class="xh"><line class="cross" x1="${x(i)}" x2="${x(i)}" y1="${P.t}" y2="${P.t + ih}"/><circle class="cdot" cx="${x(i)}" cy="${y(p.v)}" r="5"/>
      <rect class="hit" x="${x(i) - cw / 2}" y="${P.t}" width="${cw}" height="${ih}"${tip(p.tip || `${p.x}: ${fmt(p.v, 1)}`)}/></g>`).join("");
    const last = xy[xy.length - 1];
    return `<svg viewBox="0 0 ${W} ${H}" class="chart" role="img" aria-label="${esc(o.label || "Trend chart")}">
      <defs><linearGradient id="ag${o.id || 0}" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="${POS}" stop-opacity=".38"/><stop offset="1" stop-color="${POS}" stop-opacity="0"/></linearGradient></defs>
      ${grid}<path d="${area}" fill="url(#ag${o.id || 0})"/><path d="${d}" class="line"/>
      <circle cx="${last[0]}" cy="${last[1]}" r="11" class="glow"/><circle cx="${last[0]}" cy="${last[1]}" r="4.5" class="dot"/>${labels}${hits}</svg>`;
  }

  /** Donut with hoverable segments; data-idx drives the centre label. */
  function donut(segments, colors) {
    const R = 70, Cc = 2 * Math.PI * R, size = 180; let offset = 0;
    const total = segments.reduce((a, s) => a + s.value, 0) || 1;
    const arcs = segments.map((s, i) => {
      const len = (s.value / total) * Cc;
      const a = `<circle class="seg" data-idx="${i}" cx="90" cy="90" r="${R}" fill="none" stroke="${colors[i]}" stroke-width="22" stroke-dasharray="${Math.max(len - 3, 0)} ${Cc}" stroke-dashoffset="${-offset}" transform="rotate(-90 90 90)"${tip(`${s.label}: ${s.value.toFixed(1)}% of high-pressure deliveries`)}/>`;
      offset += len; return a;
    }).join("");
    return `<svg viewBox="0 0 ${size} ${size}" class="donut" role="img" aria-label="High-pressure deliveries by phase">${arcs}</svg>`;
  }

  /** Signed vertical bars (value above expected). items: [{x, v, tip}] */
  function barChart(items, o = {}) {
    if (!items.length) return `<div class="empty">No qualifying matches yet.</div>`;
    const W = o.width || 600, H = o.height || 190, P = { t: 12, r: 10, b: 26, l: 40 };
    const iw = W - P.l - P.r, ih = H - P.t - P.b;
    const vals = items.map((i) => i.v);
    const { lo, hi, ticks } = nice(Math.min(0, ...vals), Math.max(0, ...vals), 4);
    const y = (v) => P.t + ih - ((v - lo) / (hi - lo)) * ih, slot = iw / items.length, bw = Math.min(slot * 0.58, 42);
    const grid = ticks.map((t) => `<line x1="${P.l}" x2="${W - P.r}" y1="${y(t)}" y2="${y(t)}" class="grid${t === 0 ? " zero" : ""}"/><text x="${P.l - 8}" y="${y(t) + 4}" class="axis" text-anchor="end">${fmt(t, hi - lo < 6 ? 1 : 0)}</text>`).join("");
    const lstep = Math.max(1, Math.ceil((Math.max(...items.map((it) => String(it.x).length)) * 6.2 + 12) / slot));   // skip x labels when bars are narrower than a label
    const bars = items.map((it, i) => {
      const cx = P.l + (i + 0.5) * slot, y0 = y(0), y1 = y(it.v), top = Math.min(y0, y1), h = Math.max(Math.abs(y1 - y0), 1.5);
      const neg = it.v < 0;
      return `<g class="bar-g"><rect class="hit" x="${P.l + i * slot}" y="${P.t}" width="${slot}" height="${ih}"${tip(it.tip || `${it.x}: ${fmt(it.v, 1)}`)}/>
        <rect x="${cx - bw / 2}" y="${top}" width="${bw}" height="${h}" rx="4" class="bar" fill="${neg ? NEG : POS}" pointer-events="none"/>
        ${(items.length - 1 - i) % lstep === 0 ? `<text x="${cx}" y="${H - 8}" class="axis" text-anchor="middle">${esc(it.x)}</text>` : ""}</g>`;
    }).join("");
    return `<svg viewBox="0 0 ${W} ${H}" class="chart" role="img" aria-label="${esc(o.label || "Bar chart")}">${grid}${bars}</svg>`;
  }

  /** Scatter: normal vs pressure with a parity diagonal. pts: [{x, y, id, kind, label, hot, tip}] */
  function scatter(pts, o = {}) {
    const W = o.width || 640, H = o.height || 420, P = { t: 16, r: 18, b: 44, l: 54 };
    const iw = W - P.l - P.r, ih = H - P.t - P.b;
    const all = pts.flatMap((p) => [p.x, p.y]);
    const mn = o.min ?? Math.min(...all) * 0.97, mx = o.max ?? Math.max(...all) * 1.03;
    const { lo, hi, ticks } = nice(mn, mx, 5);
    const sx = (v) => P.l + ((v - lo) / (hi - lo)) * iw, sy = (v) => P.t + ih - ((v - lo) / (hi - lo)) * ih;
    const grid = ticks.map((t) => `<line x1="${P.l}" x2="${W - P.r}" y1="${sy(t)}" y2="${sy(t)}" class="grid"/><line y1="${P.t}" y2="${P.t + ih}" x1="${sx(t)}" x2="${sx(t)}" class="grid"/>
      <text x="${P.l - 8}" y="${sy(t) + 4}" class="axis" text-anchor="end">${fmt(t, hi - lo < 12 ? 1 : 0)}</text><text x="${sx(t)}" y="${H - P.b + 16}" class="axis" text-anchor="middle">${fmt(t, hi - lo < 12 ? 1 : 0)}</text>`).join("");
    const dots = pts.map((p) => `<circle class="sc${p.hot ? " hot" : ""}" data-open="${p.id}" data-kind="${p.kind}" cx="${sx(p.x)}" cy="${sy(p.y)}" r="${p.hot ? 6 : 4}" tabindex="0" aria-label="${esc(p.label)}"${tip(p.tip)}/>`).join("");
    const names = pts.filter((p) => p.hot).map((p) => `<text class="sc-name" x="${sx(p.x) + 9}" y="${sy(p.y) + 4}">${esc(p.label.split(" ").slice(-1)[0])}</text>`).join("");
    return `<svg viewBox="0 0 ${W} ${H}" class="chart scatter" role="img" aria-label="${esc(o.label || "Normal versus pressure performance")}">${grid}
      <line x1="${sx(lo)}" y1="${sy(lo)}" x2="${sx(hi)}" y2="${sy(hi)}" class="parity"/>
      <text x="${P.l + iw - 6}" y="${P.t + 14}" class="axis" text-anchor="end">${esc(o.topLabel || "above the line = better under pressure")}</text>
      <text x="${P.l + iw / 2}" y="${H - 6}" class="axis ttl" text-anchor="middle">${esc(o.xLabel || "")}</text>
      <text transform="translate(14 ${P.t + ih / 2}) rotate(-90)" class="axis ttl" text-anchor="middle">${esc(o.yLabel || "")}</text>${dots}${names}</svg>`;
  }

  /** Histogram of numbers with an optional threshold line. */
  function histogram(vals, o = {}) {
    const W = o.width || 520, H = o.height || 170, P = { t: 12, r: 10, b: 26, l: 36 };
    const nb = o.bins || 36, lo = o.lo ?? 0, hi = o.hi ?? Math.max(...vals);
    const bins = new Array(nb).fill(0); vals.forEach((v) => { const k = Math.min(nb - 1, Math.max(0, Math.floor(((v - lo) / (hi - lo)) * nb))); bins[k]++; });
    const mx = Math.max(...bins), iw = W - P.l - P.r, ih = H - P.t - P.b, bw = iw / nb;
    const thr = o.threshold, tx = thr == null ? null : P.l + ((thr - lo) / (hi - lo)) * iw;
    const bars = bins.map((c, i) => { const h = (c / mx) * ih, x0 = P.l + i * bw, mid = lo + ((i + 0.5) / nb) * (hi - lo), hot = thr != null && mid >= thr;
      return `<rect x="${x0 + 0.5}" y="${P.t + ih - h}" width="${Math.max(bw - 1.5, 1)}" height="${h}" rx="2" fill="${hot ? POS : "#4a3d66"}"${tip(`PI ${(lo + (i / nb) * (hi - lo)).toFixed(1)}–${(lo + ((i + 1) / nb) * (hi - lo)).toFixed(1)}: ${(100 * c / vals.length).toFixed(1)}% of deliveries`)}/>`; }).join("");
    const axis = [0, 0.25, 0.5, 0.75, 1].map((t) => `<text x="${P.l + t * iw}" y="${H - 8}" class="axis" text-anchor="middle">${(lo + t * (hi - lo)).toFixed(0)}</text>`).join("");
    return `<svg viewBox="0 0 ${W} ${H}" class="chart" role="img" aria-label="${esc(o.label || "Distribution")}"><line x1="${P.l}" x2="${W - P.r}" y1="${P.t + ih}" y2="${P.t + ih}" class="grid"/>${bars}
      ${tx != null ? `<line x1="${tx}" x2="${tx}" y1="${P.t}" y2="${P.t + ih}" class="thr"/><text x="${tx + 5}" y="${P.t + 11}" class="axis">${esc(o.thrLabel || "high pressure")}</text>` : ""}${axis}</svg>`;
  }

  /** Over x wickets heat-map. grid[over-1][wkts] = mean PI or null. */
  function heatmap(grid, counts, o = {}) {
    const W = o.width || 560, H = o.height || 300, P = { t: 10, r: 10, b: 30, l: 40 };
    const iw = W - P.l - P.r, ih = H - P.t - P.b, cw = iw / 10, ch = ih / 20;
    const flat = grid.flat().filter((v) => v != null), mx = Math.max(...flat), mn = Math.min(...flat);
    const col = (v) => { const t = (v - mn) / (mx - mn); const r = Math.round(30 + 225 * t), g = Math.round(18 + 44 * t * t), b = Math.round(54 + 111 * t); return `rgb(${r},${g},${b})`; };
    let cells = "";
    grid.forEach((row, ov) => row.forEach((v, w) => {
      if (v == null || counts[ov][w] < 20) { cells += `<rect x="${P.l + w * cw}" y="${P.t + ov * ch}" width="${cw - 1}" height="${ch - 1}" rx="2" fill="#1d1629"${tip(`Over ${ov + 1}, ${w} down: too few deliveries`)}/>`; return; }
      cells += `<rect x="${P.l + w * cw}" y="${P.t + ov * ch}" width="${cw - 1}" height="${ch - 1}" rx="2" fill="${col(v)}"${tip(`Over ${ov + 1}, ${w} wickets down: mean PI ${v.toFixed(2)} (${counts[ov][w].toLocaleString()} balls)`)}/>`;
    }));
    const yl = [1, 5, 10, 15, 20].map((v) => `<text x="${P.l - 6}" y="${P.t + (v - 0.5) * ch + 4}" class="axis" text-anchor="end">${v}</text>`).join("");
    const xl = [0, 2, 4, 6, 8].map((w) => `<text x="${P.l + (w + 0.5) * cw}" y="${H - 14}" class="axis" text-anchor="middle">${w}</text>`).join("");
    return `<svg viewBox="0 0 ${W} ${H}" class="chart" role="img" aria-label="Mean Pressure Index by over and wickets lost">${cells}${yl}${xl}
      <text x="${P.l + iw / 2}" y="${H - 1}" class="axis ttl" text-anchor="middle">wickets lost</text><text transform="translate(9 ${P.t + ih / 2}) rotate(-90)" class="axis ttl" text-anchor="middle">over</text></svg>`;
  }

  /** Radar chart. axes: [name], series: [{name, color, values 0-1}] */
  function radar(axes, series, o = {}) {
    const S = o.size || 320, c = S / 2, R = S / 2 - 54, n = axes.length;
    const pt = (i, r) => [c + Math.sin((i / n) * 2 * Math.PI) * R * r, c - Math.cos((i / n) * 2 * Math.PI) * R * r];
    const rings = [0.25, 0.5, 0.75, 1].map((r) => `<polygon points="${axes.map((_, i) => pt(i, r).join(",")).join(" ")}" class="rad-ring"/>`).join("");
    const spokes = axes.map((a, i) => { const [x, y] = pt(i, 1), [lx, ly] = pt(i, 1.2); return `<line x1="${c}" y1="${c}" x2="${x}" y2="${y}" class="grid"/><text x="${lx}" y="${ly + 4}" class="axis" text-anchor="${lx < c - 4 ? "end" : lx > c + 4 ? "start" : "middle"}">${esc(a)}</text>`; }).join("");
    const polys = series.map((s) => `<polygon points="${s.values.map((v, i) => pt(i, Math.max(0.03, v)).join(",")).join(" ")}" fill="${s.color}" fill-opacity=".16" stroke="${s.color}" stroke-width="2.2"/>` +
      s.values.map((v, i) => { const [x, y] = pt(i, Math.max(0.03, v)); return `<circle cx="${x}" cy="${y}" r="4" fill="${s.color}" stroke="#1a1424" stroke-width="2"${tip(`${s.name} · ${axes[i]}: ${s.tips ? s.tips[i] : Math.round(v * 100)}`)}/>`; }).join("")).join("");
    return `<svg viewBox="0 0 ${S} ${S}" class="chart radar" role="img" aria-label="${esc(o.label || "Radar comparison")}">${rings}${spokes}${polys}</svg>`;
  }

  /** Per-ball pressure timeline. balls: [inn, over, PI, WP, code, bat, bowl]. Wicket balls get a marker. */
  function timeline(balls, o = {}) {
    const W = o.width || 900, H = o.height || 240, P = { t: 14, r: 14, b: 28, l: 40 };
    const iw = W - P.l - P.r, ih = H - P.t - P.b, n = balls.length;
    const mx = Math.max(3, Math.ceil(Math.max(...balls.map((b) => b[2]))));
    const x = (i) => P.l + (i / (n - 1)) * iw, y = (v) => P.t + ih - (v / mx) * ih;
    let d = ""; balls.forEach((b, i) => { d += `${i ? "L" : "M"}${x(i).toFixed(1)},${y(b[2]).toFixed(1)}`; });
    const first = balls.findIndex((b) => b[0] === 2);
    const thr = o.threshold;
    const grid = [0, 1, 2, 3].filter((t) => t <= mx).map((t) => `<line x1="${P.l}" x2="${W - P.r}" y1="${y(t)}" y2="${y(t)}" class="grid"/><text x="${P.l - 8}" y="${y(t) + 4}" class="axis" text-anchor="end">${t}</text>`).join("");
    const marks = balls.map((b, i) => {
      const w = b[4] === 9, big = b[4] >= 4 && b[4] < 9, hot = thr != null && b[2] >= thr;
      const t = `${b[0] === 1 ? "1st" : "2nd"} inns · over ${b[1]} · ${b[5]} v ${b[6]}<br>${w ? "<b>Wicket</b>" : `${b[4]} run${b[4] === 1 ? "" : "s"}`} · PI ${b[2].toFixed(2)} · win prob ${(b[3] * 100).toFixed(0)}%`;
      return `<rect class="hit" x="${x(i) - iw / n / 2}" y="${P.t}" width="${Math.max(iw / n, 2)}" height="${ih}"${tip(t)}/>${w ? `<circle cx="${x(i)}" cy="${y(b[2])}" r="5.5" class="wk"/>` : big ? `<circle cx="${x(i)}" cy="${y(b[2])}" r="3.2" class="bd"/>` : ""}${hot && !w && !big ? `<circle cx="${x(i)}" cy="${y(b[2])}" r="1.4" class="hotdot"/>` : ""}`;
    }).join("");
    const lbl = [[0, "1st over"], [Math.floor(first / 2), "over 10"], [first - 1, "over 20"], [first + Math.floor((n - first) / 2), "over 10"], [n - 1, "end"]].map(([i, t]) => `<text x="${x(Math.max(0, i))}" y="${H - 8}" class="axis" text-anchor="middle">${t}</text>`).join("");
    return `<svg viewBox="0 0 ${W} ${H}" class="chart" role="img" aria-label="${esc(o.label || "Pressure timeline")}">
      ${thr != null ? `<rect x="${P.l}" y="${P.t}" width="${iw}" height="${y(thr) - P.t}" fill="#e0409a" fill-opacity=".07"/><line class="thr" x1="${P.l}" x2="${W - P.r}" y1="${y(thr)}" y2="${y(thr)}"/>` : ""}
      ${grid}${first > 0 ? `<line x1="${x(first)}" x2="${x(first)}" y1="${P.t}" y2="${P.t + ih}" class="split"/>` : ""}
      <path d="${d}" class="line thin"/>${marks}${lbl}</svg>`;
  }

  /* shared tooltip, wired once */
  function wireTips(tipEl) {
    let cur = null;
    const place = (e) => {
      const r = tipEl.getBoundingClientRect(); let x = e.clientX + 14, y = e.clientY + 16;
      if (x + r.width > innerWidth - 8) x = e.clientX - r.width - 14; if (y + r.height > innerHeight - 8) y = e.clientY - r.height - 12;
      tipEl.style.transform = `translate(${Math.max(8, x)}px, ${Math.max(8, y)}px)`;
    };
    document.addEventListener("pointermove", (e) => {
      const t = e.target.closest && e.target.closest("[data-tip]");
      if (!t) { if (cur) { tipEl.hidden = true; cur = null; } return; }
      if (t !== cur) { cur = t; tipEl.innerHTML = t.getAttribute("data-tip"); tipEl.hidden = false; }
      place(e);
    }, { passive: true });
    document.addEventListener("pointerleave", () => { tipEl.hidden = true; cur = null; }, true);
    document.addEventListener("focusin", (e) => { const t = e.target.closest && e.target.closest("[data-tip]"); if (t) { const r = t.getBoundingClientRect(); tipEl.innerHTML = t.getAttribute("data-tip"); tipEl.hidden = false; tipEl.style.transform = `translate(${r.right + 8}px, ${r.top}px)`; } });
    document.addEventListener("focusout", () => { tipEl.hidden = true; });
  }

  global.ClutchCharts = { areaChart, donut, barChart, scatter, histogram, heatmap, radar, timeline, wireTips, esc, SERIES, POS, NEG, nice, fmt };
})(window);
