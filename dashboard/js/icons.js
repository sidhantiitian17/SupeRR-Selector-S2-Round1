/* Thin-stroke icons (Lucide-style). Filled into [data-icon] placeholders at startup. */
(function (global) {
  "use strict";
  const P = {
    overview: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/>',
    batters: '<path d="M4 20 14 10"/><path d="m14 10 4-4 2 2-4 4"/><path d="M3 21l2-2"/>',
    bowlers: '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3"/>',
    model: '<path d="M4 16a8 8 0 1 1 16 0"/><path d="m12 16 4-5"/>',
    compare: '<path d="M8 3v18M16 3v18M4 8h8M12 16h8"/>',
    matches: '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
    methodology: '<path d="M4 4h6a4 4 0 0 1 4 4v12a3 3 0 0 0-3-3H4z"/><path d="M20 4h-6a4 4 0 0 0-4 4v12a3 3 0 0 1 3-3h7z"/>',
    watchlist: '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
    settings: '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M5 19l2-2M17 7l2-2"/>',
    report: '<path d="M6 2h9l5 5v15H6z"/><path d="M14 2v6h6M9 13h7M9 17h7"/>',
    calendar: '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
    bell: '<path d="M6 8a6 6 0 1 1 12 0c0 7 3 8 3 8H3s3-1 3-8"/><path d="M10 21a2 2 0 0 0 4 0"/>',
    chevron: '<path d="m6 9 6 6 6-6"/>',
    left: '<path d="m15 18-6-6 6-6"/>',
    right: '<path d="m9 18 6-6-6-6"/>',
    trophy: '<path d="M8 21h8M12 17v4M7 4h10v5a5 5 0 0 1-10 0z"/><path d="M7 6H4v1a3 3 0 0 0 3 3M17 6h3v1a3 3 0 0 1-3 3"/>',
    target: '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3"/><path d="M12 2v2M12 20v2"/>',
    zap: '<path d="M13 2 4 14h7l-1 8 9-12h-7z"/>',
    shield: '<path d="M12 3 4 6v6c0 5 3.5 8 8 9 4.5-1 8-4 8-9V6z"/>',
    activity: '<path d="M3 12h4l3-8 4 16 3-8h4"/>',
    download: '<path d="M12 3v12m0 0-4-4m4 4 4-4M4 21h16"/>',
    search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>',
    close: '<path d="M18 6 6 18M6 6l12 12"/>',
    user: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>'
  };
  function svg(name) {
    return `<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${P[name] || ""}</svg>`;
  }
  function fill(root = document) {
    root.querySelectorAll("[data-icon]").forEach((el) => { el.innerHTML = svg(el.dataset.icon); });
  }
  global.ClutchIcons = { svg, fill };
})(window);
