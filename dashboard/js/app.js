/* Under Pressure Rating dashboard core: state, overview cards, leaderboard, player drawer, routing.
 * Single source of truth: window.CLUTCH_DATA (built by scripts/build_data.py from the hybrid pipeline).
 * Official rank = p.rank. Every list, card and export reads that field; nothing re-ranks. */
(function () {
  "use strict";
  const D = window.CLUTCH_DATA;
  const Ch = window.ClutchCharts, esc = Ch.esc;
  const icon = window.ClutchIcons.svg;
  const $ = (s, r = document) => r.querySelector(s);
  const reduceMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;

  const DONUT_COLORS = ["#ff3ea5", "#c4007a", "#7a4bd6", "#4b3a8f"];
  const KIND_LABEL = { bat: "Batter", bowl: "Bowler" };
  const TITLES = {
    overview: ["Pressure Dashboard", "Measure. Compare. Rank."],
    batters: ["Batters", "Every ranked batter, with usual-level comparison"],
    bowlers: ["Bowlers", "Every ranked bowler, with usual-level comparison"],
    model: ["Pressure Model", "Define pressure yourself and watch what changes"],
    compare: ["Compare", "Two or three players, side by side"],
    matches: ["Matches", "Ball-by-ball pressure, match by match"],
    watchlist: ["Watchlist", "Recent form (2025–26) and a Rajasthan Royals review"],
    reproduce: ["Reproduce", "The presentation, the code and every step to rebuild our results"],
    methodology: ["Methodology", "How the Clutch Rating is built, and how far to trust it"],
    settings: ["Settings", "Display and motion preferences"],
  };

  const state = {
    view: "overview", tab: "bat", comp: "combined", query: "", sort: { key: "rank", dir: 1 },
    selectedId: null, slide: 0, trendRange: "all", matchWindow: 10, drawer: null, paused: false,
    prefs: { autoplay: true, confidence: true },
  };
  window.ClutchState = state;

  /* ---------- selectors (all read the same arrays) ---------- */
  const pool = (tab) => D[tab];
  const ranked = (tab) => pool(tab);                       // already in official order
  const top10 = (tab) => pool(tab).slice(0, 10);
  const top3 = () => pool(state.tab).slice(0, 3);
  const find = (id, tab) => pool(tab || state.tab).find((p) => p.id === id);
  const statsOf = (p, comp = state.comp) => p.s[comp] || null;
  function selected() { return find(state.selectedId) || top10(state.tab)[0]; }
  const compLabel = () => ({ ipl: "IPL", t20i: "T20I", combined: "IPL + T20I" }[state.comp]);

  /* ---------- formatting ---------- */
  const sgn = (v, d = 1, suf = "") => `${v >= 0 ? "+" : "−"}${Math.abs(v).toFixed(d)}${suf}`;
  const deltaChip = (v, d = 1, suf = "") => `<span class="delta ${v >= 0 ? "up" : "down"}">${icon(v >= 0 ? "zap" : "activity").replace(/width="18" height="18"/, 'width="12" height="12"')}${sgn(v, d, suf)}</span>`;
  const initials = (n) => n.split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0]).join("").toUpperCase();
  const avatar = (p, size = "") => p.photo ? `<span class="avatar ${size}"><img src="${esc(p.photo)}" alt="" loading="lazy"/></span>` : `<span class="avatar ${size}"><span>${esc(initials(p.name))}</span></span>`;
  const conf = (p) => { const s = p.s.combined; const c = Math.min(1, s.pb / 500) * 0.7 + Math.min(1, p.nmatches / 60) * 0.3; return c; };
  const confBadge = (p) => { const c = conf(p); const t = c >= 0.7 ? ["High confidence", "#22c55e", "rgba(34,197,94,.12)"] : c >= 0.45 ? ["Medium confidence", "#fbbf24", "rgba(251,191,36,.12)"] : ["Low sample", "#f43f5e", "rgba(244,63,94,.12)"]; return `<span class="badge-conf" style="color:${t[1]};background:${t[2]}" title="Based on ${p.s.combined.pb} pressure balls over ${p.nmatches} matches">${t[0]}</span>`; };
  // "better" delta: batters want higher SR, bowlers want lower economy
  const gapOf = (p, s) => (s && s.um != null) ? (p.role === "bat" ? s.pm - s.um : s.um - s.pm) : null;
  const unitBalls = (p, s) => p.role === "bat" ? s.pb : +(s.pb / 6).toFixed(1);
  const metricFmt = (p, v) => v == null ? "—" : p.role === "bat" ? v.toFixed(1) : v.toFixed(2);
  const insightOf = (p) => {
    const s = p.s.combined;
    return p.role === "bat"
      ? `Strikes at ${s.pm.toFixed(1)} under pressure against ${s.um.toFixed(1)} in routine play, over ${s.pb} pressure balls. In the top 10 in ${Math.round(p.ptop10 * 100)}% of 300 resamples.`
      : `Concedes ${s.pm.toFixed(2)} an over under pressure against ${s.um.toFixed(2)} in routine play, over ${(s.pb / 6).toFixed(0)} pressure overs. In the top 10 in ${Math.round(p.ptop10 * 100)}% of 300 resamples.`;
  };
  const periodLabel = (p) => { const [y, h] = [p.slice(0, 4), p.slice(4)]; return `${h === "H1" ? "Jan–Jun" : "Jul–Dec"} ${y.slice(2)}`; };

  const api = { D, state, find, statsOf, gapOf, avatar, deltaChip, sgn, initials, confBadge, conf, metricFmt, unitBalls, KIND_LABEL, top10, ranked, pool, compLabel, openPlayer, toast, periodLabel, insightOf };
  window.ClutchApp = { api };

  /* ---------- cards ---------- */
  function renderFeatured() {
    const list = top3(); const p = list[state.slide % list.length]; const s = p.s.combined;
    $("#featured").innerHTML = `
      <div class="feat-copy">
        <span class="eyebrow">FEATURED PLAYER · #${p.rank} ${state.tab === "bat" ? "BATTER" : "BOWLER"}</span>
        <h2 class="feat-name">${esc(p.name)}</h2>
        <p class="feat-role">${KIND_LABEL[p.role]} · ${esc(p.team)} · Clutch Rating ${p.clutch.toFixed(0)}</p>
        <p class="feat-insight">${esc(insightOf(p))}</p>
        <div><button class="btn" data-open="${p.id}">View Profile</button></div>
      </div>
      <div class="feat-stage">
        ${p.photo ? `<img src="${esc(p.photo)}" alt="${esc(p.name)}" class="${/Sooryavanshi/.test(p.name) ? "" : "framed"}"/>` : `<div class="initials-fallback" aria-label="${esc(p.name)}">${esc(initials(p.name))}</div>`}
        <span class="delta up ci">${p.s.combined.pb} pressure ${state.tab === "bat" ? "balls" : "balls bowled"}</span>
        <div class="carousel-ctrl">
          <button data-prev aria-label="Previous player">${icon("left")}</button>
          <div class="dots">${list.map((_, i) => `<i class="${i === state.slide % list.length ? "on" : ""}"></i>`).join("")}</div>
          <button data-next aria-label="Next player">${icon("right")}</button>
        </div>
      </div>`;
  }

  function trendPoints(p) {
    let t = p.trend; if (state.trendRange === "recent") t = t.filter((x) => x.p >= "2025H1");
    return t.map((x) => ({ x: periodLabel(x.p), v: x.v, tip: `<b>${esc(p.name)}</b><br>to ${periodLabel(x.p)}: ${sgn(x.v, 1)} runs above expected per 100 pressure balls<br>${x.n} pressure balls so far` }));
  }
  function renderTrend() {
    const p = selected(); const pts = trendPoints(p);
    const last = pts.length ? pts[pts.length - 1].v : 0, prev = pts.length > 1 ? pts[pts.length - 2].v : last;
    $("#trend").innerHTML = `
      <div class="card-head"><h3 class="card-title">Pressure value trend</h3>
        <select class="select" id="trend-range" aria-label="Trend range"><option value="all" ${state.trendRange === "all" ? "selected" : ""}>All time</option><option value="recent" ${state.trendRange === "recent" ? "selected" : ""}>Since 2025</option></select></div>
      <p class="trend-cap">${esc(p.name)} · runs ${p.role === "bat" ? "above expected" : "saved vs expected"} per 100 pressure balls, cumulative (pressure = top 30% Pressure Index, as in the report)</p>
      <div class="trend-num"><span class="big">${pts.length ? sgn(last, 1) : "—"}</span>${pts.length > 1 ? deltaChip(last - prev) + `<span class="chip-note">change since ${pts[pts.length - 2].x}</span>` : ""}</div>
      <div class="chart-box" id="trend-box"></div>`;
    const box = $("#trend-box"); box.innerHTML = Ch.areaChart(pts, { width: box.clientWidth, height: box.clientHeight, label: `Cumulative pressure value for ${p.name}`, zero: true, id: "tr" });
  }

  function renderKpis() {
    const p = selected(); const s = statsOf(p) || p.s.combined; const bat = p.role === "bat";
    const gap = gapOf(p, s); const dis = (bat ? (s.urate != null ? s.urate - s.prate : 0) : s.prate - (s.urate || 0));
    const kp = bat ? [
      { ico: "activity", label: "Pressure balls faced", val: s.pb, sub: `of ${s.pb + s.ub} faced (${compLabel()})`, d: null },
      { ico: "zap", label: "Pressure strike rate", val: s.pm.toFixed(1), sub: `Usual SR ${s.um != null ? s.um.toFixed(1) : "—"}`, d: gap, suf: " SR" },
      { ico: "shield", label: "Pressure dismissal rate", val: s.prate.toFixed(2) + "%", sub: `Usual ${s.urate != null ? s.urate.toFixed(2) + "%" : "—"} per ball`, d: dis, suf: " pts" },
      { ico: "trophy", label: "Clutch rating", val: p.clutch.toFixed(0), sub: `Rank #${p.rank} · top-10 in ${Math.round(p.ptop10 * 100)}%`, d: null },
    ] : [
      { ico: "activity", label: "Pressure overs bowled", val: (s.pb / 6).toFixed(0), sub: `of ${((s.pb + s.ub) / 6).toFixed(0)} bowled (${compLabel()})`, d: null },
      { ico: "zap", label: "Pressure economy", val: s.pm.toFixed(2), sub: `Usual ${s.um != null ? s.um.toFixed(2) : "—"}`, d: gap, suf: "" },
      { ico: "target", label: "Pressure wicket rate", val: s.prate.toFixed(2) + "%", sub: `Usual ${s.urate != null ? s.urate.toFixed(2) + "%" : "—"} per ball`, d: dis, suf: " pts" },
      { ico: "trophy", label: "Clutch rating", val: p.clutch.toFixed(0), sub: `Rank #${p.rank} · top-10 in ${Math.round(p.ptop10 * 100)}%`, d: null },
    ];
    const scale = Math.max(s.um || 0, s.pm) * 1.15;
    $("#kpis").innerHTML = `
      <div class="card-head"><h3 class="card-title">${esc(p.name)} <span class="muted" style="font-weight:400">· ${esc(compLabel())}</span></h3>
        <span class="muted" style="font-size:12px">Pressure = top 25–30% leverage balls</span></div>
      <div class="kpi-grid">${kp.map((k) => `<div class="kpi"><div class="lab">${icon(k.ico)} ${esc(k.label)}</div><div class="val">${k.val}</div>${k.d != null ? deltaChip(k.d, 1, k.suf) : "<span class='delta flat'>reference</span>"}<div class="sub">${esc(k.sub)}</div></div>`).join("")}
        <div class="kpi-compare">${compareRow("Usual level", s.um, "#6f84f0", bat ? 1 : 2, scale)}${compareRow("Under pressure", s.pm, "#e0409a", bat ? 1 : 2, scale)}</div></div>`;
  }
  function compareRow(label, v, color, digits, max) {
    return `<div class="compare-row"><div class="top"><span class="muted">${label}</span><span class="tnum">${v == null ? "—" : v.toFixed(digits)}</span></div><div class="track"><i style="width:${v == null ? 0 : (v / max) * 100}%;background:${color}"></i></div></div>`;
  }

  function renderDonut() {
    const phases = D.phases[state.comp]; const top = phases.reduce((a, b) => (b.value > a.value ? b : a));
    $("#donut").innerHTML = `
      <div class="card-head"><h3 class="card-title">Pressure situations</h3><span class="muted" style="font-size:12px">${esc(compLabel())} · share of high-pressure balls</span></div>
      <div class="donut-wrap"><div class="donut-box">${Ch.donut(phases, DONUT_COLORS)}<div class="donut-center"><span class="big" id="dc-val">${top.value.toFixed(0)}%</span><small id="dc-lab">${esc(top.label)}</small></div></div>
      <ul class="legend" id="donut-legend">${phases.map((ph, i) => `<li data-idx="${i}"><span class="sw" style="background:${DONUT_COLORS[i]}"></span>${esc(ph.label)}<span class="pct">${ph.value.toFixed(0)}%</span></li>`).join("")}</ul></div>`;
  }

  /* ---- leaderboard ---- */
  const sortVal = (p, key) => {
    const s = statsOf(p); if (!s) return -Infinity;
    if (key === "rank") return p.rank;
    if (key === "balls") return s.pb; if (key === "metric") return s.pm;
    if (key === "delta") return gapOf(p, s) ?? -Infinity; if (key === "clutch") return p.clutch; return p.rank;
  };
  function renderLeaderboard() {
    const bat = state.tab === "bat";
    $("#leaderboard").innerHTML = `
      <div class="card-head"><h3 class="card-title">Top 10 ${bat ? "batters" : "bowlers"}</h3><span class="muted" style="font-size:12px">Official order · stats for ${esc(compLabel())}</span></div>
      <div class="lb-tools">
        <div class="tabs" role="tablist" aria-label="Role"><span class="slider" style="width:calc(50% - 4px);transform:translateX(${bat ? 0 : 100}%)"></span>
          <button role="tab" aria-selected="${bat}" data-tab="bat" class="${bat ? "on" : ""}">Batters</button><button role="tab" aria-selected="${!bat}" data-tab="bowl" class="${!bat ? "on" : ""}">Bowlers</button></div>
        <label class="search">${icon("search")}<input id="lb-search" type="search" placeholder="Search top 10" value="${esc(state.query)}" aria-label="Search top 10"/></label>
        <span class="spacer"></span><button class="export-btn" id="export-btn">${icon("download")} Export top 10 (CSV)</button></div>
      <div class="table-wrap"><table aria-label="Top 10 ${bat ? "batters" : "bowlers"}"><thead><tr>
        <th><button data-sort="rank">Rank</button></th><th>Player</th><th><button data-sort="balls">${bat ? "Pressure balls" : "Pressure overs"}</button></th>
        <th><button data-sort="metric">${bat ? "Pressure SR" : "Pressure econ"}</button></th><th><button data-sort="delta">vs usual</button></th><th><button data-sort="clutch">Clutch rating</button></th></tr></thead>
        <tbody id="lb-body"></tbody></table></div>`;
    renderTable();
  }
  function renderTable() {
    const body = $("#lb-body"); if (!body) return;
    const bat = state.tab === "bat", q = state.query.trim().toLowerCase(), sel = selected();
    let rows = top10(state.tab).slice().sort((a, b) => (sortVal(a, state.sort.key) - sortVal(b, state.sort.key)) * state.sort.dir || a.rank - b.rank);
    if (q) rows = rows.filter((p) => p.name.toLowerCase().includes(q));
    body.innerHTML = rows.length ? rows.map((p) => {
      const s = statsOf(p), g = gapOf(p, s);
      return `<tr data-row="${p.id}" class="${sel && sel.id === p.id ? "sel" : ""}" tabindex="0" aria-label="Open ${esc(p.name)}">
        <td class="rank ${p.rank <= 3 ? "top" : ""}">${String(p.rank).padStart(2, "0")}</td>
        <td><div class="pcell">${avatar(p)}<div><div class="pname">${esc(p.name)}</div><div class="pteam">${esc(p.team)} · ${KIND_LABEL[p.role]}</div></div></div></td>
        <td>${s ? unitBalls(p, s) : "—"}</td><td>${s ? metricFmt(p, s.pm) : "—"}</td><td>${g == null ? "—" : deltaChip(g, 1)}</td>
        <td><div class="rating-cell"><span class="big" style="font-size:18px">${p.clutch.toFixed(0)}</span><span class="rating-bar"><i style="width:${p.clutch}%"></i></span></div></td></tr>`;
    }).join("") : `<tr><td colspan="6" class="empty">No players match “${esc(state.query)}” in the top 10.</td></tr>`;
    document.querySelectorAll("[data-sort]").forEach((b) => { const on = b.dataset.sort === state.sort.key; b.classList.toggle("sorted", on); b.setAttribute("aria-sort", on ? (state.sort.dir > 0 ? "ascending" : "descending") : "none"); });
  }

  function renderMatches() {
    const p = selected(); const n = state.matchWindow; const ms = p.ms.slice(-n);
    const bat = p.role === "bat";
    const MON = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]; const items = ms.map((m) => ({ x: `${+m.dt.slice(8)} ${MON[+m.dt.slice(5, 7) - 1]} '${m.dt.slice(2, 4)}`, v: m.v, tip: `<b>${esc(p.name)}</b> v ${esc(m.opp)}<br>${m.dt} · ${m.comp}${m.st && m.st !== "League" && m.st !== "Others" ? " · " + m.st : ""}<br>${m.n} pressure balls · ${m.r} ${bat ? "runs" : "conceded"} · ${m.o} ${bat ? "out" : "wkts"}<br>Value: ${sgn(m.v, 1)} runs vs expected` }));
    const avg = items.length ? items.reduce((a, b) => a + b.v, 0) / items.length : 0, half = Math.floor(items.length / 2);
    const mean = (a) => a.length ? a.reduce((x, y) => x + y.v, 0) / a.length : 0;
    $("#matches").innerHTML = `
      <div class="card-head"><h3 class="card-title">Pressure by match</h3><select class="select" id="match-window" aria-label="Matches window"><option value="10" ${n === 10 ? "selected" : ""}>Last 10 matches</option><option value="5" ${n === 5 ? "selected" : ""}>Last 5 matches</option></select></div>
      <div class="match-head"><div><div class="big">${sgn(avg, 1)}</div><div class="match-meta">${esc(p.name)} · avg runs vs expected per match, pressure balls only</div></div>${items.length > 3 ? `<div class="chip-wrap">${deltaChip(mean(items.slice(half)) - mean(items.slice(0, half)))}<span class="chip-note">latest ${items.length - half} vs earlier ${half} matches</span></div>` : ""}</div>
      <div class="chart-box" id="match-box"></div>`;
    const box = $("#match-box"); box.innerHTML = Ch.barChart(items, { width: box.clientWidth, height: box.clientHeight, label: `Pressure value per match for ${p.name}` });
  }

  let rt; addEventListener("resize", () => { clearTimeout(rt); rt = setTimeout(() => { if (state.view === "overview") { renderTrend(); renderMatches(); } else if (window.ClutchPages && ClutchPages.resize) ClutchPages.resize(); }, 140); });

  function renderAll() { renderFeatured(); renderTrend(); renderKpis(); renderDonut(); renderLeaderboard(); renderMatches(); }
  function sync() { renderFeatured(); renderTrend(); renderKpis(); renderMatches(); renderTable(); }

  /* ---------- drawer ---------- */
  function openPlayer(id, tab) {
    if (tab && tab !== state.tab) { state.tab = tab; state.slide = 0; if (state.view === "overview") renderAll(); }
    state.selectedId = id; if (state.view === "overview") sync(); openDrawer(id);
  }
  function openDrawer(id) {
    const p = find(id) || find(id, state.tab === "bat" ? "bowl" : "bat"); if (!p) return;
    state.drawer = p.id; const bat = p.role === "bat";
    const s = statsOf(p) || p.s.combined, c = p.s.combined;
    const max = Math.max(s.um || 0, s.pm) * 1.15;
    const bar = (l, v, col, d) => `<div class="compare-row"><div class="top"><span>${l}</span><span class="tnum">${v == null ? "—" : v.toFixed(d)}</span></div><div class="track"><i style="width:${v == null ? 0 : (v / max) * 100}%;background:${col}"></i></div></div>`;
    const seasons = p.seasons.map((x) => ({ x: String(x.y), v: x.v, tip: `<b>${x.y}</b>: ${sgn(x.v, 1)} runs vs expected per 100 pressure balls<br>${x.n} pressure balls (top 30% Pressure Index)` }));
    const best = p.best.map((m) => `<li><span>${m.dt} v ${esc(m.opp)}</span><span>${m.r} ${bat ? "runs" : "conc."}, ${m.o} ${bat ? "out" : "wkt"}${m.o === 1 ? "" : "s"}</span><b>${sgn(m.v, 1)}</b></li>`).join("");
    const d = $("#drawer");
    d.innerHTML = `
      <button class="x" data-close aria-label="Close">${icon("close")}</button>
      <div class="dr-head">${avatar(p, "lg")}<div><h2>${esc(p.name)}</h2><div class="muted" style="font-size:13px">${KIND_LABEL[p.role]} · ${esc(p.team)} · Rank #${p.rank}</div><div style="margin-top:8px">${confBadge(p)}</div></div></div>
      <div class="dr-section"><h3>Clutch rating</h3><div style="display:flex;align-items:center;gap:12px"><span class="big">${p.clutch.toFixed(0)}</span><span class="muted" style="font-size:12.5px">Top-10 in ${Math.round(p.ptop10 * 100)}% of 300 resamples · rank ${p.rlo.toFixed(0)}–${p.rhi.toFixed(0)} (90% range)<br>Top-10 in ${p.specs} of ${p.nspecs} alternative specifications</span></div></div>
      <div class="dr-section"><h3>${bat ? "Strike rate" : "Economy (lower is better)"}: usual vs pressure · ${esc(compLabel())}</h3>${bar("Usual level", s.um, "#6f84f0", bat ? 1 : 2)}${bar("Under pressure", s.pm, "#e0409a", bat ? 1 : 2)}
        <div class="split-grid"><div><small>${bat ? "Boundary %" : "Boundary conceded %"}</small><b>${s.pbnd.toFixed(1)}%</b><i>usual ${s.ubnd == null ? "—" : s.ubnd.toFixed(1) + "%"}</i></div><div><small>Dot-ball %</small><b>${s.pdot.toFixed(1)}%</b><i>usual ${s.udot == null ? "—" : s.udot.toFixed(1) + "%"}</i></div><div><small>${bat ? "Dismissal % per ball" : "Wicket % per ball"}</small><b>${s.prate.toFixed(2)}</b><i>usual ${s.urate == null ? "—" : s.urate.toFixed(2)}</i></div></div></div>
      <div class="dr-section"><h3>Sample size</h3><div class="note">${s.pb} pressure ${bat ? "balls" : "balls bowled"} (${p.nmatches} matches) and ${s.ub} usual ${bat ? "balls" : "balls"} in ${esc(compLabel())}. Ratings shrink toward the league mean when samples are small.</div></div>
      <div class="dr-section"><h3>Season-by-season consistency</h3>${Ch.barChart(seasons, { height: 150, label: "Pressure value by season" })}</div>
      <div class="dr-section"><h3>Best pressure innings and spells</h3><ul class="best">${best || "<li>Not enough data</li>"}</ul></div>
      <div class="dr-section"><h3>Last 12 pressure matches</h3>${Ch.barChart(p.ms.map((m) => ({ x: m.dt.slice(2, 7).replace("-", "/"), v: m.v, tip: `${m.dt} v ${esc(m.opp)}: ${sgn(m.v, 1)} (${m.n} balls)` })), { height: 150, label: "Recent matches" })}</div>
      <div class="dr-section"><div class="note"><strong style="color:var(--text)">Limitations.</strong> Pressure samples are small: a few boundaries or wickets can move a rating, so ranks 8–10 are close calls. Roles differ (openers face more powerplay balls than finishers face death balls); the model adjusts for context but cannot remove all role bias. Associate-team opposition is down-weighted.</div></div>`;
    d.classList.add("open"); d.setAttribute("aria-hidden", "false"); $("#overlay").hidden = false; d.querySelector("[data-close]").focus();
  }
  function closeDrawer() { $("#drawer").classList.remove("open"); $("#drawer").setAttribute("aria-hidden", "true"); $("#overlay").hidden = true; state.drawer = null; }

  /* ---------- toast + navigation ---------- */
  let tt; function toast(msg) { const t = $("#toast"); t.textContent = msg; t.classList.add("show"); clearTimeout(tt); tt = setTimeout(() => t.classList.remove("show"), 2400); }

  function setView(view) {
    if (!TITLES[view]) view = "overview";
    state.view = view;
    document.querySelectorAll(".nav-item").forEach((b) => { b.classList.toggle("active", b.dataset.view === view); b.toggleAttribute("aria-current", b.dataset.view === view); });
    $("#page-title").textContent = TITLES[view][0]; $("#page-sub").textContent = TITLES[view][1];
    const page = $("#page"), grid = $("#grid");
    if (view === "overview") { page.hidden = true; grid.hidden = false; renderAll(); }
    else {
      grid.hidden = true; page.hidden = false; page.className = "page page-" + view; page.innerHTML = "";
      if (view === "batters" || view === "bowlers") { const t = view === "batters" ? "bat" : "bowl"; if (state.tab !== t) { state.tab = t; state.selectedId = top10(t)[0].id; } }
      window.ClutchPages[view](page, api);
      page.classList.remove("in"); void page.offsetWidth; page.classList.add("in");
    }
    window.scrollTo({ top: 0, behavior: reduceMotion ? "auto" : "smooth" });
    if (location.hash.startsWith("#/dashboard")) history.replaceState(null, "", "#/dashboard/" + view);
  }
  function setTab(tab) { state.tab = tab; state.slide = 0; state.selectedId = top10(tab)[0].id; renderAll(); }
  function setComp(comp) {
    state.comp = comp; document.querySelectorAll("#comp-seg button").forEach((b) => b.classList.toggle("on", b.dataset.comp === comp));
    if (state.view === "overview") renderAll(); else setView(state.view);
    toast(`Showing ${compLabel()} statistics. Ranks stay official (IPL + T20I combined).`);
  }

  /* carousel */
  function step(dir) { const n = top3().length; state.slide = (state.slide + dir + n) % n; state.selectedId = top3()[state.slide].id; sync(); }
  let auto = null;
  function startAuto() { stopAuto(); if (reduceMotion || !state.prefs.autoplay) return; auto = setInterval(() => { if (!state.paused && state.view === "overview" && !document.hidden && !$("#app").hidden) step(1); }, 8000); }
  function stopAuto() { clearInterval(auto); auto = null; }
  api.startAuto = startAuto; api.stopAuto = stopAuto;

  function exportCsv() {
    const bat = state.tab === "bat";
    const header = ["rank", "player", "team", "clutch_rating", bat ? "pressure_balls" : "pressure_overs", bat ? "pressure_sr" : "pressure_economy", bat ? "usual_sr" : "usual_economy", "p_top10_bootstrap", "specs_in_top10", "n_specs", "competition_filter"];
    const rows = top10(state.tab).map((p) => { const s = statsOf(p) || {}; return [p.rank, p.name, p.team, p.clutch.toFixed(1), s.pb != null ? unitBalls(p, s) : "", s.pm ?? "", s.um ?? "", p.ptop10, p.specs, p.nspecs, state.comp]; });
    download(`under-pressure-rating-top10-${bat ? "batters" : "bowlers"}.csv`, [header, ...rows].map((r) => r.map((v) => `"${String(v).replace(/"/g, '""')}"`).join(",")).join("\n"), "text/csv;charset=utf-8");
    toast("Top 10 exported as CSV");
  }
  function download(name, text, type) {
    try { const url = URL.createObjectURL(new Blob([text], { type })); const a = document.createElement("a"); a.href = url; a.download = name; document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 1500); }
    catch (e) { toast("Export is unavailable in this preview"); }
  }
  api.download = download;

  /* ---------- events ---------- */
  document.addEventListener("click", (e) => {
    if ($("#app").hidden) return;
    const t = e.target, hit = (s) => t.closest(s); let el;
    if ((el = hit("[data-comp]"))) return setComp(el.dataset.comp);
    if ((el = hit("[data-view]"))) return setView(el.dataset.view);
    if ((el = hit(".tabs [data-tab]")) && !el.closest("#page")) return setTab(el.dataset.tab);
    if ((el = hit("[data-sort]")) && el.closest("#leaderboard")) { const k = el.dataset.sort; state.sort = { key: k, dir: state.sort.key === k ? -state.sort.dir : (k === "rank" ? 1 : -1) }; return renderTable(); }
    if (hit("#export-btn")) return exportCsv();
    if (hit("[data-prev]")) { stopAuto(); step(-1); return startAuto(); }
    if (hit("[data-next]")) { stopAuto(); step(1); return startAuto(); }
    if ((el = hit("[data-open]"))) { const kind = el.dataset.kind; return openPlayer(Number(el.dataset.open), kind); }
    if ((el = hit("[data-row]"))) return openPlayer(Number(el.dataset.row));
    if (hit("[data-close]") || t.id === "overlay") return closeDrawer();
  });
  document.addEventListener("change", (e) => {
    if (e.target.id === "trend-range") { state.trendRange = e.target.value; renderTrend(); }
    if (e.target.id === "match-window") { state.matchWindow = Number(e.target.value); renderMatches(); }
  });
  document.addEventListener("input", (e) => { if (e.target.id === "lb-search") { state.query = e.target.value; renderTable(); } });
  document.addEventListener("keydown", (e) => {
    if ($("#app").hidden) return;
    if (e.key === "Escape" && state.drawer !== null) closeDrawer();
    if (e.key === "Enter" && e.target.matches && e.target.matches("[data-row],[data-open].sc")) { const id = Number(e.target.dataset.row || e.target.dataset.open); openPlayer(id, e.target.dataset.kind); }
  });
  document.addEventListener("mouseover", (e) => {
    const seg = e.target.closest && e.target.closest(".donut .seg"), li = e.target.closest && e.target.closest("#donut-legend li");
    const idx = seg ? seg.dataset.idx : li ? li.dataset.idx : null; if (idx == null) return;
    const ph = D.phases[state.comp][+idx]; $("#dc-val").textContent = `${ph.value.toFixed(0)}%`; $("#dc-lab").textContent = ph.label;
    document.querySelectorAll("#donut-legend li").forEach((x) => x.classList.toggle("on", x.dataset.idx === idx));
  });
  document.addEventListener("mouseout", (e) => {
    if (e.target.closest && (e.target.closest(".donut") || e.target.closest("#donut-legend"))) {
      const top = D.phases[state.comp].reduce((a, b) => (b.value > a.value ? b : a));
      const v = $("#dc-val"); if (!v) return; v.textContent = `${top.value.toFixed(0)}%`; $("#dc-lab").textContent = top.label;
      document.querySelectorAll("#donut-legend li").forEach((x) => x.classList.remove("on"));
    }
  });
  document.addEventListener("mouseenter", (e) => { if (e.target.id === "featured") state.paused = true; }, true);
  document.addEventListener("mouseleave", (e) => { if (e.target.id === "featured") state.paused = false; }, true);

  /* ---------- boot (called once, when the dashboard is first shown) ---------- */
  api.init = function () {
    window.ClutchIcons.fill(); Ch.wireTips($("#tip"));
    state.selectedId = top10(state.tab)[0].id;
    $("#date-label").textContent = `${D.summary.years[0]} – ${D.summary.years[1]} · ${D.summary.matches} matches`;
    renderAll(); startAuto();
  };
  window.ClutchApp.init = api.init; window.ClutchApp.setView = setView; window.ClutchApp.openPlayer = openPlayer;
})();
