/* Dashboard pages beyond Overview. Each page is render(host, api); all numbers come from window.CLUTCH_DATA. */
(function () {
  "use strict";
  const Ch = window.ClutchCharts, esc = Ch.esc, S = Ch.SERIES;
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const pct = (a, v) => { const s = a.slice().sort((x, y) => x - y); let k = 0; while (k < s.length && s[k] <= v) k++; return k / s.length; };
  let ctx = null;                      // api of the last-rendered page
  const pages = {};
  let resizers = [];
  pages.resize = () => resizers.forEach((f) => f());

  /* ================================================================ Batters / Bowlers */
  function ranking(kind) {
    return (host, api) => {
      const { D, state, statsOf, gapOf, avatar, deltaChip, metricFmt, unitBalls, KIND_LABEL } = api; ctx = api;
      const bat = kind === "bat"; const all = D[kind];
      const teams = [...new Set(all.map((p) => p.team))].sort();
      const f = { q: "", team: "", minBalls: bat ? 100 : 100, shown: 25, sort: "rank", dir: 1, season: "all" };
      host.innerHTML = `
        <div class="page-grid two">
          <article class="card wide"><div class="card-head"><h3 class="card-title">${bat ? "Batters" : "Bowlers"}: usual versus pressure</h3><span class="muted" style="font-size:12px">${esc(api.compLabel())} · each dot is one ranked player</span></div>
            <div class="chart-box tall" id="sc-box"></div>
            <p class="chart-note">${bat ? "Strike rate in routine play (x) against under pressure (y). Above the diagonal = scores faster under pressure." : "Economy in routine play (x) against under pressure (y). Below the diagonal = tighter under pressure."} Labelled dots are the official top 10.</p></article>
          <article class="card"><div class="card-head"><h3 class="card-title">${bat ? "Strike-rate" : "Economy"} change distribution</h3></div>
            <div class="chart-box" id="hist-box" style="min-height:190px"></div><p class="chart-note" id="hist-note"></p>
            <div class="card-head" style="margin-top:14px"><h3 class="card-title">Clutch rating distribution</h3></div><div class="chart-box" id="hist2-box" style="min-height:170px"></div></article>
        </div>
        <article class="card" style="margin-top:16px"><div class="card-head"><h3 class="card-title">Full ranking (${all.length} players)</h3>
          <div class="filters"><label class="search">${window.ClutchIcons.svg("search")}<input id="f-q" type="search" placeholder="Search player" aria-label="Search player"/></label>
            <label class="fld">Team <select class="select" id="f-team"><option value="">All</option>${teams.map((t) => `<option>${esc(t)}</option>`).join("")}</select></label>
            <label class="fld">Min pressure ${bat ? "balls" : "overs"} <input type="range" id="f-min" min="0" max="${bat ? 500 : 80}" step="${bat ? 25 : 5}" value="${bat ? 100 : 15}"/><b id="f-min-v">${bat ? 100 : 15}</b></label></div></div>
          <div class="table-wrap"><table class="full" aria-label="Full ranking"><thead><tr><th>Rank</th><th>Player</th><th>${bat ? "Press. balls" : "Press. overs"}</th><th>${bat ? "Press. SR" : "Press. econ"}</th><th>Usual</th><th>vs usual</th><th>Clutch</th><th title="Share of 300 bootstrap resamples with this player in the top 10">P(top 10)</th><th>Rank range</th></tr></thead><tbody id="full-body"></tbody></table></div>
          <div class="more"><button class="btn btn-ghost" id="more-btn">Show more</button><span class="muted" id="count"></span></div></article>`;
      if (bat) f.minBalls = 100; else f.minBalls = 15 * 6;
      const rows = () => all.filter((p) => { const s = statsOf(p); if (!s) return false; if (s.pb < f.minBalls) return false; if (f.team && p.team !== f.team) return false; if (f.q && !p.name.toLowerCase().includes(f.q)) return false; return true; });
      function table() {
        const r = rows(); const shown = r.slice(0, f.shown);
        $("#full-body").innerHTML = shown.map((p) => { const s = statsOf(p), g = gapOf(p, s);
          return `<tr data-row="${p.id}" tabindex="0" class="${p.rank <= 10 ? "is-top" : ""}"><td class="rank ${p.rank <= 3 ? "top" : ""}">${p.rank}</td><td><div class="pcell">${avatar(p)}<div><div class="pname">${esc(p.name)}</div><div class="pteam">${esc(p.team)}</div></div></div></td>
          <td>${unitBalls(p, s)}</td><td>${metricFmt(p, s.pm)}</td><td>${metricFmt(p, s.um)}</td><td>${g == null ? "—" : deltaChip(g, 1)}</td>
          <td><div class="rating-cell"><b>${p.clutch.toFixed(0)}</b><span class="rating-bar"><i style="width:${p.clutch}%"></i></span></div></td>
          <td data-tip="Top 10 in ${Math.round(p.ptop10 * 100)}% of 300 resamples"><span class="pbar"><i style="width:${p.ptop10 * 100}%"></i></span> ${Math.round(p.ptop10 * 100)}%</td><td class="muted">${p.rlo.toFixed(0)}–${p.rhi.toFixed(0)}</td></tr>`; }).join("") || `<tr><td colspan="9" class="empty">No players match these filters.</td></tr>`;
        $("#count").textContent = `Showing ${shown.length} of ${r.length}`; $("#more-btn").style.display = r.length > shown.length ? "" : "none";
      }
      function charts() {
        const r = all.filter((p) => statsOf(p) && statsOf(p).um != null && statsOf(p).pb >= 30);
        const pts = r.map((p) => { const s = statsOf(p); return { x: s.um, y: s.pm, id: p.id, kind, label: p.name, hot: p.rank <= 10, tip: `<b>${esc(p.name)}</b> · rank #${p.rank}<br>Usual ${metricFmt(p, s.um)} → pressure ${metricFmt(p, s.pm)}<br>${s.pb} pressure balls · Clutch ${p.clutch.toFixed(0)}` }; });
        const box = $("#sc-box"); box.innerHTML = Ch.scatter(pts, { width: box.clientWidth, height: box.clientHeight, xLabel: bat ? "usual strike rate" : "usual economy", yLabel: bat ? "pressure strike rate" : "pressure economy", topLabel: bat ? "above the line = faster under pressure" : "below the line = tighter under pressure" });
        const deltas = r.map((p) => { const s = statsOf(p); return bat ? s.pm - s.um : s.um - s.pm; });
        const lim = bat ? 70 : 3; const hb = $("#hist-box");
        hb.innerHTML = Ch.histogram(deltas.map((v) => Math.max(-lim, Math.min(lim, v))), { width: hb.clientWidth, height: 190, lo: -lim, hi: lim, bins: 26, threshold: 0, thrLabel: "no change", label: "Distribution of pressure minus usual" });
        const up = deltas.filter((v) => v > 0).length;
        $("#hist-note").textContent = `${up} of ${deltas.length} ranked players do better under pressure than in routine play (${Math.round(100 * up / deltas.length)}%). The league as a whole does not: pressure is hard.`;
        const h2 = $("#hist2-box"); h2.innerHTML = Ch.histogram(all.map((p) => p.clutch), { width: h2.clientWidth, height: 170, lo: 0, hi: 100, bins: 25, label: "Distribution of clutch rating" });
      }
      $("#f-q").addEventListener("input", (e) => { f.q = e.target.value.toLowerCase(); f.shown = 25; table(); });
      $("#f-team").addEventListener("change", (e) => { f.team = e.target.value; f.shown = 25; table(); });
      $("#f-min").addEventListener("input", (e) => { const v = +e.target.value; $("#f-min-v").textContent = v; f.minBalls = bat ? v : v * 6; f.shown = 25; table(); });
      $("#more-btn").addEventListener("click", () => { f.shown += 25; table(); });
      table(); requestAnimationFrame(charts); resizers = [charts];
    };
  }
  pages.batters = ranking("bat"); pages.bowlers = ranking("bowl");

  /* ================================================================ Pressure Model */
  function decode(b64) { const bin = atob(b64); const u = new Uint8Array(bin.length); for (let i = 0; i < bin.length; i++) u[i] = bin.charCodeAt(i); return u; }
  let surCache = null;
  function surr(D) {
    if (surCache) return surCache; const Sg = D.surrogate;
    surCache = { sample: decode(Sg.sample), bat: Sg.bat.map(decode), bowl: Sg.bowl.map(decode) }; return surCache;
  }
  pages.model = (host, api) => {
    const { D, find, openPlayer } = api; ctx = api; const Sg = D.surrogate; const dec = surr(D);
    const W0 = Sg.weights.slice(); const w = W0.slice(); let share = 30, kind = "bat";
    host.innerHTML = `
      <div class="page-grid two">
        <article class="card"><div class="card-head"><h3 class="card-title">Define pressure</h3><button class="btn btn-ghost sm" id="reset">Reset to fitted</button></div>
          <p class="chart-note" style="margin-top:0">Five transparent factors, each scaled 0–1 per delivery. Move the sliders to weight them. This is a simplified stand-in for the official model, which learns pressure directly from win probability (Spearman ρ with this surrogate at default weights: <b>${Sg.spearman.toFixed(2)}</b>).</p>
          <div id="sliders">${Sg.names.map((n, i) => `<label class="wslider"><span>${n}</span><input type="range" min="0" max="100" step="1" value="${Math.round(w[i] * 100)}" data-w="${i}" aria-label="${esc(n)} weight"/><b id="wv${i}">${Math.round(w[i] * 100)}</b></label>`).join("")}
            <label class="wslider share"><span>High-pressure share of deliveries</span><input type="range" min="10" max="50" step="5" value="30" id="share"/><b id="sh-v">30%</b></label></div>
        </article>
        <article class="card"><div class="card-head"><h3 class="card-title">Pressure Index distribution</h3><span class="muted" style="font-size:12px">${Sg.nsample.toLocaleString()} sampled deliveries</span></div>
          <div class="chart-box" id="mh-box" style="min-height:200px"></div><p class="chart-note" id="mh-note"></p></article>
      </div>
      <div class="page-grid two" style="margin-top:16px">
        <article class="card"><div class="card-head"><h3 class="card-title">What changes in the top 10?</h3>
          <div class="tabs sm" role="tablist"><span class="slider" id="mk-s" style="width:calc(50% - 4px)"></span><button data-mk="bat" class="on">Batters</button><button data-mk="bowl">Bowlers</button></div></div>
          <p class="chart-note" style="margin-top:0">The official top 30 are re-ranked by their raw pressure-versus-usual difference under <em>your</em> definition and compared with the same raw measure at the default weights. It shows how sensitive a ranking is to the definition of pressure; it does not replace the official, shrunk Clutch Rating.</p>
          <div id="diff"></div></article>
        <article class="card"><div class="card-head"><h3 class="card-title">Where pressure lives: over × wickets lost</h3><span class="muted" style="font-size:12px">mean official Pressure Index</span></div>
          <div class="chart-box" id="heat-box" style="min-height:300px"></div><p class="chart-note">Pressure climbs with overs and with wickets lost: a 6-down death over is the heaviest ball in T20. Cells with under 20 balls are blank.</p></article>
      </div>`;
    const norm = () => { const t = w.reduce((a, b) => a + b, 0) || 1; return w.map((v) => v / t); };
    function indexOf(u, n, wn) { const out = new Float32Array(n); for (let i = 0; i < n; i++) { const o = i * 5; out[i] = 100 * (wn[0] * u[o] + wn[1] * u[o + 1] + wn[2] * u[o + 2] + wn[3] * u[o + 3] + wn[4] * u[o + 4]) / 255; } return out; }
    function quant(arr, q) { const s = Float32Array.from(arr).sort(); return s[Math.min(s.length - 1, Math.floor(q * s.length))]; }
    function rankUnder(wn, thr, k) {
      const res = [];
      D[k].slice(0, 30).forEach((p, idx) => {
        const u = dec[k][idx], n = u.length / 6; let pn = 0, pr = 0, pw = 0, un = 0, ur = 0, uw = 0, pl = 0, ul = 0;
        for (let i = 0; i < n; i++) { const o = i * 6; const s = 100 * (wn[0] * u[o] + wn[1] * u[o + 1] + wn[2] * u[o + 2] + wn[3] * u[o + 3] + wn[4] * u[o + 4]) / 255; const fl = u[o + 5]; const runs = fl & 15, out = (fl >> 4) & 1, legal = (fl >> 5) & 1;
          if (s >= thr) { pn++; pr += runs; pw += out; pl += legal; } else { un++; ur += runs; uw += out; ul += legal; } }
        if (pn < 40 || un < 40) { res.push({ p, v: -99, pn }); return; }
        const v = k === "bat" ? 100 * pr / pn - 100 * ur / un : 6 * ur / ul - 6 * pr / pl;
        res.push({ p, v, pn });
      });
      return res.sort((a, b) => b.v - a.v);
    }
    function update() {
      const wn = norm(); const n = Sg.nsample; const idx = indexOf(dec.sample, n, wn.map((v) => v));
      const thr = quant(idx, 1 - share / 100);
      const mb = $("#mh-box"); mb.innerHTML = Ch.histogram(Array.from(idx), { width: mb.clientWidth, height: 200, lo: 0, hi: 100, bins: 40, threshold: thr, thrLabel: `top ${share}%`, label: "Pressure Index distribution" });
      $("#mh-note").textContent = `Threshold: surrogate index ≥ ${thr.toFixed(1)} marks the top ${share}% of deliveries as high pressure.`;
      const bnorm = W0.map((v) => v / W0.reduce((a, b) => a + b, 0)); const bidx = indexOf(dec.sample, n, bnorm); const bthr = quant(bidx, 0.7);
      const A = rankUnder(bnorm, bthr, kind), B = rankUnder(wn, thr, kind);
      const posA = new Map(A.map((r, i) => [r.p.id, i + 1]));
      const top = B.slice(0, 10), inB = new Set(top.map((r) => r.p.id)), inA = new Set(A.slice(0, 10).map((r) => r.p.id));
      const dropped = A.slice(0, 10).filter((r) => !inB.has(r.p.id)).map((r) => r.p.name);
      $("#diff").innerHTML = `<table class="diff"><thead><tr><th>#</th><th>Player</th><th>${kind === "bat" ? "SR gain" : "Econ gain"}</th><th>Move</th><th>Official</th></tr></thead><tbody>` + top.map((r, i) => {
        const mv = posA.get(r.p.id) - (i + 1); const isNew = !inA.has(r.p.id);
        return `<tr data-row="${r.p.id}" tabindex="0"><td>${i + 1}</td><td>${esc(r.p.name)}</td><td>${r.v > -90 ? (r.v >= 0 ? "+" : "−") + Math.abs(r.v).toFixed(kind === "bat" ? 0 : 2) : "—"}</td><td>${isNew ? `<span class="chip new">new</span>` : mv === 0 ? `<span class="muted">—</span>` : `<span class="chip ${mv > 0 ? "up" : "down"}">${mv > 0 ? "▲" : "▼"} ${Math.abs(mv)}</span>`}</td><td class="muted">#${r.p.rank}</td></tr>`; }).join("") + `</tbody></table>` +
        `<p class="chart-note">${dropped.length ? `Dropped out of the top 10: ${dropped.map(esc).join(", ")}.` : "No player leaves the top 10 at this setting."} ${top.filter((r) => !inA.has(r.p.id)).length} new name${top.filter((r) => !inA.has(r.p.id)).length === 1 ? "" : "s"}.</p>`;
    }
    $$("#sliders [data-w]").forEach((el) => el.addEventListener("input", () => { w[+el.dataset.w] = +el.value / 100; $(`#wv${el.dataset.w}`).textContent = el.value; update(); }));
    $("#share").addEventListener("input", (e) => { share = +e.target.value; $("#sh-v").textContent = share + "%"; update(); });
    $("#reset").addEventListener("click", () => { W0.forEach((v, i) => { w[i] = v; const el = $(`[data-w="${i}"]`); el.value = Math.round(v * 100); $(`#wv${i}`).textContent = Math.round(v * 100); }); share = 30; $("#share").value = 30; $("#sh-v").textContent = "30%"; update(); });
    $$("[data-mk]").forEach((b) => b.addEventListener("click", () => { kind = b.dataset.mk; $$("[data-mk]").forEach((x) => x.classList.toggle("on", x === b)); $("#mk-s").style.transform = `translateX(${kind === "bat" ? 0 : 100}%)`; update(); }));
    const hb = $("#heat-box"); const drawHeat = () => { hb.innerHTML = Ch.heatmap(D.heat, D.heatN, { width: hb.clientWidth, height: Math.max(hb.clientHeight, 300) }); };
    requestAnimationFrame(() => { drawHeat(); update(); }); resizers = [drawHeat, update];
  };

  /* ================================================================ Compare */
  pages.compare = (host, api) => {
    const { D, state, statsOf, gapOf, avatar, metricFmt, unitBalls } = api; ctx = api;
    let kind = state.tab; let pick = [D[kind][0].id, D[kind][1].id, D[kind][2].id];
    host.innerHTML = `<article class="card"><div class="card-head"><h3 class="card-title">Compare players</h3>
        <div class="tabs sm" role="tablist"><span class="slider" id="ck-s" style="width:calc(50% - 4px)"></span><button data-ck="bat" class="on">Batters</button><button data-ck="bowl">Bowlers</button></div></div>
        <div class="pickers" id="pickers"></div></article>
      <div class="page-grid two" style="margin-top:16px"><article class="card"><div class="card-head"><h3 class="card-title">Profile radar</h3><span class="muted" style="font-size:12px">percentile among the ranked ${D[kind].length}</span></div><div id="radar" class="radar-box"></div><div class="legend-row" id="rlegend"></div></article>
        <article class="card"><div class="card-head"><h3 class="card-title">Usual vs pressure</h3></div><div id="bars"></div></article></div>
      <article class="card" style="margin-top:16px"><div class="card-head"><h3 class="card-title">Head to head</h3></div><div class="table-wrap"><table class="h2h" id="h2h"></table></div></article>`;
    function draw() {
      kind = $$("[data-ck].on")[0].dataset.ck; const bat = kind === "bat"; const pool = D[kind];
      $("#ck-s").style.transform = `translateX(${bat ? 0 : 100}%)`;
      pick = pick.map((id, i) => pool.find((p) => p.id === id) ? id : pool[i].id);
      $("#pickers").innerHTML = [0, 1, 2].map((i) => `<label class="pick" style="--c:${S[i]}"><i></i><select class="select" data-pick="${i}" aria-label="Player ${i + 1}">${i === 2 ? `<option value="">— none —</option>` : ""}${pool.slice(0, 60).map((p) => `<option value="${p.id}" ${p.id === pick[i] ? "selected" : ""}>#${p.rank} ${esc(p.name)}</option>`).join("")}</select></label>`).join("");
      const sel = pick.map((id) => (id ? pool.find((p) => p.id === id) : null)).filter(Boolean);
      const sa = pool.map((p) => p.s.combined);
      const dims = bat ? [["Clutch rating", (p) => p.clutch], ["Pressure SR", (p) => p.s.combined.pm], ["SR uplift", (p) => p.s.combined.pm - (p.s.combined.um || 0)], ["Dismissal safety", (p) => -p.s.combined.prate], ["Boundary %", (p) => p.s.combined.pbnd], ["Consistency", (p) => p.cons]]
        : [["Clutch rating", (p) => p.clutch], ["Pressure economy", (p) => -p.s.combined.pm], ["Econ gain", (p) => (p.s.combined.um || 0) - p.s.combined.pm], ["Wicket rate", (p) => p.s.combined.prate], ["Dot-ball %", (p) => p.s.combined.pdot], ["Consistency", (p) => p.cons]];
      const arrs = dims.map(([, f]) => pool.map(f));
      const series = sel.map((p, i) => ({ name: p.name, color: S[i], values: dims.map(([, f], k) => pct(arrs[k], f(p))), tips: dims.map(([, f], k) => `${Math.round(100 * pct(arrs[k], f(p)))}th percentile`) }));
      $("#radar").innerHTML = Ch.radar(dims.map((d) => d[0]), series, { size: 360, label: "Radar comparison" });
      $("#rlegend").innerHTML = sel.map((p, i) => `<span><i style="background:${S[i]}"></i>${esc(p.name)}</span>`).join("");
      const mx = Math.max(...sel.map((p) => Math.max(p.s.combined.um || 0, p.s.combined.pm))) * 1.12;
      $("#bars").innerHTML = sel.map((p, i) => { const s = p.s.combined; const bar = (l, v, c) => `<div class="compare-row"><div class="top"><span>${l}</span><span class="tnum">${metricFmt(p, v)}</span></div><div class="track"><i style="width:${(v / mx) * 100}%;background:${c}"></i></div></div>`;
        return `<div class="cmp-block"><div class="pcell">${avatar(p)}<div><div class="pname" style="color:${S[i]}">${esc(p.name)}</div><div class="pteam">${bat ? "strike rate" : "economy"}</div></div></div>${bar("Usual level", s.um, "#5a4d78")}${bar("Under pressure", s.pm, S[i])}</div>`; }).join("");
      const rowsDef = [["Rank", (p) => "#" + p.rank], ["Clutch rating", (p) => p.clutch.toFixed(0)], ["Pressure " + (bat ? "balls" : "overs"), (p) => unitBalls(p, p.s.combined)], [bat ? "Pressure SR" : "Pressure economy", (p) => metricFmt(p, p.s.combined.pm)], [bat ? "Usual SR" : "Usual economy", (p) => metricFmt(p, p.s.combined.um)],
        [bat ? "Boundary %" : "Boundary conceded %", (p) => p.s.combined.pbnd.toFixed(1)], ["Dot-ball %", (p) => p.s.combined.pdot.toFixed(1)], [bat ? "Dismissal % / ball" : "Wicket % / ball", (p) => p.s.combined.prate.toFixed(2)], ["Consistency", (p) => p.cons.toFixed(2)], ["Top-10 in resamples", (p) => Math.round(p.ptop10 * 100) + "%"], ["Specifications supporting", (p) => `${p.specs}/${p.nspecs}`]];
      $("#h2h").innerHTML = `<thead><tr><th></th>${sel.map((p, i) => `<th style="color:${S[i]}">${esc(p.name)}</th>`).join("")}</tr></thead><tbody>${rowsDef.map(([l, f]) => `<tr><td class="muted">${l}</td>${sel.map((p) => `<td>${f(p)}</td>`).join("")}</tr>`).join("")}</tbody>`;
    }
    host.addEventListener("change", (e) => { const t = e.target; if (t.dataset.pick !== undefined) { pick[+t.dataset.pick] = t.value ? +t.value : null; draw(); } });
    $$("[data-ck]").forEach((b) => b.addEventListener("click", () => { $$("[data-ck]").forEach((x) => x.classList.toggle("on", x === b)); pick = [D[b.dataset.ck][0].id, D[b.dataset.ck][1].id, D[b.dataset.ck][2].id]; draw(); }));
    $$("[data-ck]").forEach((b) => b.classList.toggle("on", b.dataset.ck === kind)); draw(); resizers = [];
  };

  /* ================================================================ Matches */
  pages.matches = (host, api) => {
    const { D } = api; ctx = api; const thrPI = D.validation.thr_hp;
    host.innerHTML = `<article class="card"><div class="card-head"><h3 class="card-title">Match pressure timeline</h3>
        <label class="fld">Match <select class="select" id="m-pick" style="max-width:min(560px,60vw)">${D.timelines.map((t, i) => `<option value="${i}">${t.date} · ${t.stage} · ${t.home} v ${t.away} (${t.comp})</option>`).join("")}</select></label></div>
        <p class="chart-note" id="m-res" style="margin-top:0"></p><div class="chart-box" id="tl-box" style="min-height:260px"></div>
        <div class="legend-row"><span><i class="lgd line"></i>Pressure Index per ball</span><span><i class="lgd wk"></i>wicket</span><span><i class="lgd bd"></i>four or six</span><span><i class="lgd thr"></i>high-pressure threshold (${thrPI.toFixed(2)})</span></div></article>
      <div class="page-grid two" style="margin-top:16px"><article class="card"><div class="card-head"><h3 class="card-title">Win probability, chasing side</h3></div><div class="chart-box" id="wp-box" style="min-height:190px"></div><p class="chart-note">From the out-of-fold win-probability model. First innings shows the batting side's chance; it flips to the chasing side in the second.</p></article>
        <article class="card"><div class="card-head"><h3 class="card-title">Ten heaviest deliveries</h3></div><div class="table-wrap"><table class="diff" id="top-balls"></table></div></article></div>`;
    function draw() {
      const m = D.timelines[+$("#m-pick").value]; const balls = m.balls;
      $("#m-res").textContent = `${m.result} · ${m.comp}${m.stage !== "League" && m.stage !== "Others" ? " · " + m.stage : ""} · ${balls.filter((b) => b[2] >= thrPI).length} of ${balls.length} deliveries were high pressure.`;
      const box = $("#tl-box"); box.innerHTML = Ch.timeline(balls, { width: box.clientWidth, height: Math.max(box.clientHeight, 260), threshold: thrPI, label: `Pressure Index per ball, ${m.home} v ${m.away}` });
      const pts = balls.map((b, i) => ({ x: `${b[0] === 1 ? "1st" : "2nd"} ${b[1]}`, v: Math.round(b[3] * 1000) / 10, tip: `${b[0] === 1 ? "1st" : "2nd"} innings, over ${b[1]}: win probability ${(b[3] * 100).toFixed(0)}%` })).filter((_, i) => i % 3 === 0);
      const wb = $("#wp-box"); wb.innerHTML = Ch.areaChart(pts, { width: wb.clientWidth, height: Math.max(wb.clientHeight, 190), label: "Win probability", id: "wp" });
      const top = balls.map((b, i) => ({ b, i })).sort((x, y) => y.b[2] - x.b[2]).slice(0, 10);
      $("#top-balls").innerHTML = `<thead><tr><th>Inns · over</th><th>Batter v bowler</th><th>PI</th><th>Result</th></tr></thead><tbody>${top.map(({ b }) => `<tr><td>${b[0] === 1 ? "1st" : "2nd"} · ${b[1]}</td><td>${esc(b[5])} v ${esc(b[6])}</td><td>${b[2].toFixed(2)}</td><td>${b[4] === 9 ? '<span class="chip down">WICKET</span>' : b[4] + " run" + (b[4] === 1 ? "" : "s")}</td></tr>`).join("")}</tbody>`;
    }
    $("#m-pick").addEventListener("change", draw); requestAnimationFrame(draw); resizers = [draw];
  };

  /* ================================================================ Methodology */
  pages.methodology = (host, api) => {
    const { D, avatar, metricFmt } = api; ctx = api; const M = D.method, V = D.validation, Sm = D.summary;
    const pdefChosen = M.pdef[0];
    const ev = (kind) => D[kind].slice(0, 10).map((p) => { const s = p.s.combined; return `<tr data-row="${p.id}" tabindex="0"><td>${p.rank}</td><td>${esc(p.name)}</td><td>${s.pb}</td><td>${metricFmt(p, s.pm)}</td><td>${metricFmt(p, s.um)}</td><td>${p.role === "bat" ? s.pm - s.um >= 0 ? "+" : "−" : s.um - s.pm >= 0 ? "+" : "−"}${Math.abs(p.role === "bat" ? s.pm - s.um : s.um - s.pm).toFixed(p.role === "bat" ? 0 : 2)}</td><td>${Math.round(p.ptop10 * 100)}%</td><td>${p.specs}/${p.nspecs}</td></tr>`; }).join("");
    const tourRows = (k) => M.tour[k].slice(0, 8).map((t) => `<tr class="${t.chosen ? "is-top" : ""}"><td>${esc(t.name)}${t.chosen ? ' <span class="chip up">chosen</span>' : ""}</td><td>${t.mean.toFixed(3)}</td><td>${t.worst >= 0 ? "+" : "−"}${Math.abs(t.worst).toFixed(3)}</td></tr>`).join("");
    const wb = M.weights.bat, wo = M.weights.bowl;
    host.innerHTML = `
      <div class="meth">
        <aside class="toc card" aria-label="Contents"><b>Contents</b>${["Answer", "Pressure", "Performance", "Fair comparison", "Evidence", "How we chose", "How we got here", "Reliability"].map((t, i) => `<a href="#m${i}" data-toc="m${i}">${i + 1}. ${t}</a>`).join("")}
          <a class="btn dl" href="assets/SupeRR_Selector_Round1_HYBRID_Methodology_Report.pdf" download>Download as PDF</a><a class="btn btn-ghost dl" href="data/FINAL_TOP10_HYBRID.csv" download>Top 10 (CSV)</a></aside>
        <div class="meth-body">
          <section class="card" id="m0"><h2>The answer</h2>
            <div class="ans"><div><h4>Top 10 batters</h4><ol>${D.bat.slice(0, 10).map((p) => `<li data-row="${p.id}" tabindex="0">${esc(p.name)}</li>`).join("")}</ol></div><div><h4>Top 10 bowlers</h4><ol>${D.bowl.slice(0, 10).map((p) => `<li data-row="${p.id}" tabindex="0">${esc(p.name)}</li>`).join("")}</ol></div></div>
            <p>The Clutch Rating asks one question: <em>how much better or worse is this player when the match is on the line than in his own routine play?</em> Pressure is measured ball by ball from a win-probability model; performance is measured as value above what an average player would produce in the same situation; and every number is shrunk toward the league mean in proportion to how little evidence there is. Built on ${Sm.balls.toLocaleString()} deliveries from ${Sm.matches} matches (IPL and T20I, ${Sm.years[0]} to ${Sm.years[1]}).</p></section>
          <section class="card" id="m1"><h2>1 · Pressure definition</h2>
            <p>A gradient-boosted win-probability model (LightGBM, monotone constraints, out-of-fold, separate for each innings) scores every ball: AUC <b>${M.wp.auc1}</b> in the first innings and <b>${M.wp.auc2}</b> in the chase. <b>Pressure Index = expected size of the swing in win probability on the next delivery</b>, rescaled to average 1 and multiplied by 1.15 in knock-outs. High pressure is the top 30% of balls (PI ≥ ${V.thr_hp.toFixed(2)}); routine is the bottom 50% (PI ≤ ${V.thr_rt.toFixed(2)}).</p>
            <div class="tri"><figure><img src="assets/figures/calibration.png" alt="Win-probability calibration" loading="lazy"/><figcaption>Calibration: predicted vs observed win rates.</figcaption></figure><figure><img src="assets/figures/pressure_maps.png" alt="Pressure by over and wickets" loading="lazy"/><figcaption>Pressure rises late and with wickets down.</figcaption></figure></div>
            <h4>Does the definition mean anything? Pressure vs routine balls</h4>
            <div class="val-grid">${[["Run rate", V.pressure.rr, V.routine.rr, "runs per over"], ["Wicket %", V.pressure.wkt, V.routine.wkt, "per ball"], ["Boundary %", V.pressure.bnd, V.routine.bnd, "fours and sixes"], ["Dot %", V.pressure.dot, V.routine.dot, "of balls"]].map(([l, a, b, u]) => `<div><small>${l}</small><b>${a.toFixed(2)}</b><i>vs ${b.toFixed(2)} routine</i><em>${u}</em></div>`).join("")}</div>
            <p>High-pressure balls hold <b>${Math.round(V.share_abs_wpa * 100)}%</b> of all win-probability movement while being only 30% of deliveries (decisiveness ratio ${pdefChosen.ratio.toFixed(2)}×, vs ${M.pdef[1].ratio.toFixed(2)}× for a hand-weighted stress score and ${M.pdef[2].ratio.toFixed(2)}× for a simple rule). That is why leverage was chosen.</p></section>
          <section class="card" id="m2"><h2>2 · Performance measurement</h2>
            <p>Each ball is valued against an out-of-fold expectation for its exact situation: <b>runs above expected</b> plus the <b>cost of a wicket</b> (expected remaining runs lost: about 9.6 runs in the powerplay, 5.4 in the middle, 2.6 at the death). A win-probability-per-leverage lens is used for consistency. For batters the rating combines the pressure level, the <b>uplift over the player's own usual level</b> and an <b>impact-rate consistency</b> term (weights ${wb.map((v) => v.toFixed(2)).join(" / ")}, set by split-half reliability). Bowlers use the same structure with a no-failure consistency term (weights ${wo.map((v) => v.toFixed(2)).join(" / ")}) and a gate: a bowler must have delivered above league average under pressure.</p>
            <p>Batter score = 0.67 · A composite + 0.33 · multi-cut-off pressure strike-rate ensemble. Bowler score = 0.9 · [0.2 · A rating + 0.8 · (shrunk pressure economy + WPA)] + 0.1 · uplift, plus the delivered-under-pressure gate. Every candidate scoring rule was entered into the tournament below; none was chosen by hand.</p></section>
          <section class="card" id="m3"><h2>3 · Fair comparison</h2>
            <ul class="bul"><li><b>Own baseline:</b> every player is compared with his own routine balls, so a finisher is not punished for facing death overs.</li><li><b>Shrinkage:</b> empirical-Bayes (DerSimonian-Laird), run and wicket parts separately, so 150 balls cannot outrank 800.</li><li><b>Eligibility:</b> at least 150 pressure balls, 12 matches and 150 usual balls to be ranked.</li><li><b>Competition mix:</b> ${(100 * Sm.ipl / Sm.balls).toFixed(0)}% of deliveries are IPL and ${(100 * Sm.t20i / Sm.balls).toFixed(0)}% T20I; ratings are context-adjusted for phase, innings and opposition. Associate-team opposition counts at half weight. The A-side emerging tournaments are excluded.</li><li><b>Context:</b> leverage, phase, wickets and target are inside the expectation, so conditions are priced in.</li></ul></section>
          <section class="card" id="m4"><h2>4 · Evidence for the top 10</h2>
            <div class="two-tables"><div><h4>Batters</h4><div class="table-wrap"><table class="diff"><thead><tr><th>#</th><th>Player</th><th>Balls</th><th>Press. SR</th><th>Usual</th><th>Gain</th><th>P(top10)</th><th>Specs</th></tr></thead><tbody>${ev("bat")}</tbody></table></div></div>
            <div><h4>Bowlers</h4><div class="table-wrap"><table class="diff"><thead><tr><th>#</th><th>Player</th><th>Balls</th><th>Press. econ</th><th>Usual</th><th>Gain</th><th>P(top10)</th><th>Specs</th></tr></thead><tbody>${ev("bowl")}</tbody></table></div></div></div>
            <p class="chart-note">Pressure = top quartile of within-innings leverage (batters ≥75th percentile, bowlers ≥70th), the same definition as the PDF report. “Specs” counts the alternative specifications (rival scoring rules, IPL-only, T20I-only, chases only, other thresholds) in which the player stays in the top 10.</p></section>
          <section class="card" id="m5"><h2>5 · How the final recipe was chosen</h2>
            <p>Two independent solutions, A (context-adjusted, shrunk value) and B (pressure strike-rate and economy ensembles), plus baselines, were entered in a tournament on <b>unseen matches</b>: 30 random half-splits and 6 past-to-future cuts, scored on 8 held-out targets. Rule fixed in advance: the best worst-case cell wins, and only rules containing the pressure-versus-usual comparison are eligible.</p>
            <div class="two-tables"><div><h4>Batters (mean / worst cell)</h4><table class="diff"><tbody>${tourRows("bat")}</tbody></table></div><div><h4>Bowlers (mean / worst cell)</h4><table class="diff"><tbody>${tourRows("bowl")}</tbody></table></div></div>
            <div class="tri"><figure><img src="assets/figures/hyb_tournament_bat.png" alt="Batter tournament" loading="lazy"/></figure><figure><img src="assets/figures/hyb_tournament_bowl.png" alt="Bowler tournament" loading="lazy"/></figure></div></section>
          <section class="card" id="m6"><h2>6 · How we got here</h2>
            <p>The first version was a plain “most runs in the last five overs” count. Each step below was kept only if it improved prediction on matches the model had not seen; ideas that did not help were dropped and are recorded in the report.</p>
            <div class="tri"><figure><img src="assets/figures/hyb_iter_A.png" alt="Iterations of solution A" loading="lazy"/><figcaption>Solution A: simple counts → leverage → shrinkage → composite.</figcaption></figure><figure><img src="assets/figures/hyb_journey.png" alt="Journey from simple to final" loading="lazy"/><figcaption>From simple baseline to the hybrid, on held-out matches.</figcaption></figure></div></section>
          <section class="card" id="m7"><h2>7 · Reliability and limitations</h2>
            <div class="val-grid">${M.rel.filter((r) => r.lens === "val").map((r) => `<div><small>${r.role === "bat" ? "Batters" : "Bowlers"} · split-half reliability</small><b>${r.split.toFixed(2)}</b><i>past → future ρ ${r.temporal == null ? "—" : r.temporal.toFixed(2)}</i></div>`).join("")}</div>
            <p><b>Ranks 1–3 are firm; ranks 8–10 are close calls.</b> Poisson match-cluster bootstrap (300 resamples): Sooryavanshi is in the top 10 in ${Math.round(D.bat[0].ptop10 * 100)}% of draws, Hazlewood in ${Math.round(D.bowl[0].ptop10 * 100)}%, while the 8th–10th names sit near 30–40%.</p>
            <ul class="bul"><li><b>Small samples:</b> a player has 150–800 pressure balls; that caps any ranking's accuracy on unseen data (our held-out mean gain is about 0.32 SD for batters, 0.21 for bowlers, where random choice is 0).</li><li><b>Role bias:</b> openers and finishers see different pressure; context adjustment reduces but cannot remove this.</li><li><b>Data gaps:</b> no ball speed, line or length; byes and leg-byes are approximated; some T20I opposition is weak.</li><li><b>Not tested for causes:</b> a rating describes what happened, not why.</li></ul></section>
        </div>
      </div>`;
    $$("[data-toc]").forEach((a) => a.addEventListener("click", (e) => { e.preventDefault(); const t = document.getElementById(a.dataset.toc); t && t.scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start" }); }));
    resizers = [];
  };

  /* ================================================================ Watchlist (recent form) + RR review */
  pages.watchlist = (host, api) => {
    ctx = api; resizers = [];
    const W = window.CLUTCH_WATCH, { initials } = api, R = W.rule;
    const f1 = (v) => (v == null ? "–" : (v > 0 ? "+" : "") + v.toFixed(1));
    const mono = (n) => `<span class="avatar"><span>${esc(initials(n))}</span></span>`;
    const why = (p) => p.official > 20 ? `Official #${p.official}: his full 2022–26 record ranks well below his last two seasons.` : `Official #${p.official}: just outside the top 10 over 2022–26.`;
    const rows = (list, bat) => list.map((p) => `<tr data-open="${p.id}" data-kind="${p.role}" tabindex="0">
        <td><div class="pcell">${mono(p.name)}<div><div class="pname">${esc(p.name)}${p.ptop <= R.p_min + 0.005 ? ' <span class="wl-flag" title="Exactly on the 50% stability line">borderline</span>' : ""}</div><div class="pteam">${esc(p.team)}</div></div></div></td>
        <td class="num">#${p.rk}</td><td class="num">${Math.round(p.ptop * 100)}%</td><td class="num">${p.n} <span class="muted">(${p.m})</span></td>
        <td class="num">${bat ? p.pm.toFixed(1) : p.pm.toFixed(2)} <span class="muted">vs ${bat ? p.um.toFixed(1) : p.um.toFixed(2)}</span></td>
        <td class="num">${f1(p.v)}</td><td class="num">#${p.official}</td><td class="wl-why">${why(p)}</td></tr>`).join("");
    const table = (title, list, bat) => `<article class="card"><div class="card-head"><h3 class="card-title">${title}</h3><span class="muted" style="font-size:12px">${bat ? R.n_bat : R.n_bowl} players eligible</span></div>
      <div class="table-wrap"><table class="full wl"><thead><tr><th>Player</th><th title="Rank on 2025–26 pressure value, shrunk for sample size">Recent rank</th><th title="Share of ${R.resamples} bootstrap resamples with the player in the recent top 10">Stability</th><th>Pressure ${bat ? "balls" : "balls"} (matches)</th><th>${bat ? "Pressure SR vs usual" : "Pressure econ vs usual"}</th><th title="Runs-value per 100 pressure balls vs an average player in the same situation">Value /100</th><th>Official rank</th><th>Why not in the official top 10</th></tr></thead>
      <tbody>${rows(list, bat)}</tbody></table></div></article>`;
    const s26 = (r) => { const s = r.s26; if (!s) return `<p class="muted">Did not play IPL 2026.</p>`;
      const rk = r.r26 ? `${r.r26[0]} of ${r.r26[1]}` : `under 40 pressure balls`;
      return r.role === "bat"
        ? `<div class="rr-stats"><div><b>${s.runs}</b><small>runs · ${s.m} matches</small></div><div><b>${s.pm ?? "–"}</b><small>pressure SR (usual ${s.um ?? "–"})</small></div><div><b>${f1(s.v)}</b><small>value /100 · ${rk}</small></div></div>`
        : `<div class="rr-stats"><div><b>${s.w}</b><small>wickets · ${s.m} matches</small></div><div><b>${s.pm ?? "–"}</b><small>pressure econ (usual ${s.um ?? "–"})</small></div><div><b>${f1(s.v)}</b><small>value /100 · ${rk}</small></div></div>`; };
    const seasons = (r) => r.seasons.map((s) => `<span class="ss ${s.v >= 0 ? "pos" : "neg"}" title="${s.n} pressure balls">${s.y} <b>${f1(s.v)}</b></span>`).join("");
    const rr = W.rr.map((r) => `<article class="card rr-card" data-open="${r.id}" data-kind="${r.role}" tabindex="0">
        <div class="rr-photo">${r.photo ? `<img src="${esc(r.photo)}" alt="${esc(r.name)}" loading="lazy"/>` : mono(r.name)}</div>
        <div class="rr-body"><div class="rr-top"><h3>${esc(r.name)}</h3><span class="rr-rank">#${r.official} ${r.role === "bat" ? "batter" : "bowler"}</span></div>
          <div class="muted rr-sub">Clutch rating ${Math.round(r.clutch)} · top 10 in ${(r.ptop * 100).toFixed(r.ptop < 0.1 ? 1 : 0)}% of resamples</div>
          <div class="rr-lbl">IPL 2026 under pressure</div>${s26(r)}
          <div class="rr-lbl">Pressure value by season (per 100 pressure balls)</div><div class="rr-seasons">${seasons(r)}</div>
          <p class="rr-text">${esc(r.text)}</p></div></article>`).join("");
    const near = W.near.map((p) => `${esc(p.name)} (recent #${p.rk}, ${Math.round(p.ptop * 100)}%)`).join(", ");
    host.innerHTML = `
      <article class="card wl-banner"><h3 class="card-title">Recent form watchlist (2025–26)</h3>
        <p>These players can also be <b>considered</b> on their recent pressure performance. They are <b>not</b> part of the official top 10, which is built on all of 2022–26 and does not change.
        This list looks only at the last two seasons, so the samples are smaller and the risk is higher: treat these as options to scout, not core picks.</p>
        <p class="muted" style="font-size:12.5px">Rule, fixed before looking at names: deliveries from ${R.years} (IPL + T20I); pressure = top 30% of balls by Pressure Index, the model's official definition; at least ${R.min_balls} pressure balls; score = runs above expected per 100 pressure balls, shrunk for sample size as in the official method;
        in the recent top 10 <i>and</i> in the recent top 10 in at least ${Math.round(R.p_min * 100)}% of ${R.resamples} bootstrap resamples; not already in the official top 10.</p></article>
      <div class="wl-grid">${table("Batters to consider", W.bat, true)}${table("Bowlers to consider", W.bowl, false)}</div>
      <p class="chart-note" style="margin:8px 4px 0">Recent top 12 but below the stability line, so left out: ${near}.</p>
      <article class="card wl-banner" style="margin-top:20px"><h3 class="card-title">Rajasthan Royals review: why these players are not in the top 10</h3>
        <p>Last season (IPL 2026) and four-year pressure numbers for Jofra Archer and RR's main players. ${esc(W.rr_in_list.name)} is the RR player in the official list (#${W.rr_in_list.rank}, top 10 in ${Math.round(W.rr_in_list.ptop * 100)}% of resamples).
        Every number in these reviews is generated from the pipeline data. IPL 2026 ranks compare players with at least 40 pressure balls that season; pressure = top 30% Pressure Index.</p></article>
      <div class="rr-grid">${rr}</div>`;
  };

  /* ================================================================ Settings */
  pages.settings = (host, api) => {
    const { state } = api; ctx = api;
    host.innerHTML = `<article class="card narrow"><h3 class="card-title">Display and motion</h3>
      <label class="toggle"><span><b>Auto-rotate featured player</b><small>Cycles the top 3 every 8 seconds on Overview</small></span><input type="checkbox" id="s-auto" ${state.prefs.autoplay ? "checked" : ""}/></label>
      <label class="toggle"><span><b>Show confidence badges</b><small>Sample-size confidence beside each rating</small></span><input type="checkbox" id="s-conf" ${state.prefs.confidence ? "checked" : ""}/></label>
      <p class="chart-note">Motion follows your system setting (prefers-reduced-motion).</p></article>`;
    $("#s-auto").addEventListener("change", (e) => { state.prefs.autoplay = e.target.checked; e.target.checked ? api.startAuto() : api.stopAuto(); });
    $("#s-conf").addEventListener("change", (e) => { state.prefs.confidence = e.target.checked; });
  };

  window.ClutchPages = pages;
})();
