(function () {
  // Footer year
  var now = new Date();
  var yearEl = document.getElementById("year");
  if (yearEl) yearEl.textContent = String(now.getFullYear());

  // Keep a visible last-updated (trust + reviewers). Update manually when you ship major edits.
  var lastUpdatedEl = document.getElementById("lastUpdated");
  if (lastUpdatedEl && !lastUpdatedEl.textContent.trim()) {
    lastUpdatedEl.textContent = now.toISOString().slice(0, 10);
  }

  // Track outbound clicks (affiliate / partners / booking links)
  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("a");
    if (!a) return;

    // only track real outbound
    try {
      var url = new URL(a.href, window.location.href);
      if (url.hostname && url.hostname !== window.location.hostname) {
        if (typeof gtag === "function") {
          gtag("event", "outbound_click", {
            event_category: "outbound",
            event_label: url.href,
            transport_type: "beacon"
          });
        }
      }
    } catch (_) {}
  });
})();
