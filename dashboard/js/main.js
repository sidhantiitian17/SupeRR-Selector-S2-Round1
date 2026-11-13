/* Boots the dashboard directly (no landing page). */
(function () {
  "use strict";
  let started = false;
  function show(view) {
    document.body.classList.add("is-app");
    if (!started) { started = true; window.ClutchApp.init(); }
    window.ClutchApp.setView(view || "overview");
  }
  function route() { const m = /^#\/dashboard(?:\/(\w+))?/.exec(location.hash); show(m && m[1]); }
  addEventListener("hashchange", route);
  document.addEventListener("click", (e) => {
    const b = e.target.closest("#brand-home"); if (b) { e.preventDefault(); history.replaceState(null, "", "#/dashboard/overview"); show("overview"); }
  });
  route();
})();
