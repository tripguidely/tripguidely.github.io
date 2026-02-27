/* ==========================================================================
   TripGuidely site.js (premium + compatible) — UPDATED
   - Works even if header/footer are injected later
   - Old browser friendly (no arrow funcs, no optional chaining)
   - Mobile nav (burger + drawer + scrim + ESC)
   - Outbound tracking (GA4 gtag) + affiliate tagging
   - Affiliate CTA tracking (.js-aff) centralized here (remove inline scripts)
   - Widget engagement tracking (#esim-search)
   - Smooth internal anchors w/ sticky header offset (fallback-safe)
   - Safe console usage + error guards
   ========================================================================== */

(function () {
  "use strict";

  var DOC = document;
  var WIN = window;

  /* ---------- tiny utils (compatible) ---------- */

  function $(sel, root) {
    return (root || DOC).querySelector(sel);
  }

  function on(el, evt, fn, opts) {
    if (!el) return;
    if (el.addEventListener) el.addEventListener(evt, fn, opts || false);
    else if (el.attachEvent) el.attachEvent("on" + evt, fn);
  }

  function safeConsole() {
    try { return WIN.console && WIN.console.log; } catch (_) { return null; }
  }

  function trimStr(s) {
    return (s || "").replace(/^\s+|\s+$/g, "");
  }

  function setTextById(id, value) {
    var el = DOC.getElementById(id);
    if (el) el.textContent = String(value);
  }

  function isSameHost(url) {
    try {
      return url && url.hostname && url.hostname === WIN.location.hostname;
    } catch (_) {
      return true;
    }
  }

  function parseURL(href) {
    // URL() is not supported in very old browsers; fallback to anchor element.
    try {
      return new URL(href, WIN.location.href);
    } catch (_) {
      var a = DOC.createElement("a");
      a.href = href;
      // IE sometimes needs absolute normalization:
      if (!a.hostname && WIN.location && WIN.location.hostname) {
        a.href = a.href;
      }
      return {
        href: a.href,
        hostname: a.hostname || "",
        pathname: a.pathname || "",
        search: a.search || "",
        hash: a.hash || ""
      };
    }
  }

  function closestAnchor(el) {
    // closest() fallback
    while (el && el !== DOC) {
      if (el.tagName && el.tagName.toLowerCase() === "a") return el;
      el = el.parentNode;
    }
    return null;
  }

  function getClosestLink(target) {
    if (!target) return null;
    if (target.closest) return target.closest("a");
    return closestAnchor(target);
  }

  function getHeaderOffset() {
    // Uses CSS var if available, fallback to actual header height
    var header = $(".header");
    var h = header ? header.offsetHeight : 0;
    // If header is sticky, add a little breathing room
    return (h || 72) + 12;
  }

  function scrollToWithOffset(el) {
    if (!el) return;
    var y = 0;

    // compute absolute top
    var rect = el.getBoundingClientRect ? el.getBoundingClientRect() : null;
    if (rect && typeof rect.top === "number") {
      y = rect.top + (WIN.pageYOffset || DOC.documentElement.scrollTop || 0);
    } else {
      // fallback
      y = el.offsetTop || 0;
    }

    y = y - getHeaderOffset();

    try {
      WIN.scrollTo({ top: y, behavior: "smooth" });
    } catch (_) {
      WIN.scrollTo(0, y);
    }
  }

  /* ---------- GA helpers ---------- */

  function hasGtag() {
    return typeof WIN.gtag === "function";
  }

  function gtagEvent(name, params) {
    if (!hasGtag()) return;
    try { WIN.gtag("event", name, params || {}); } catch (_) {}
  }

  function isAffiliateOrPartner(urlObj) {
    // Customize this list over time
    var host = (urlObj.hostname || "").toLowerCase();
    if (!host) return false;

    // Common travel / affiliate patterns (safe defaults)
    if (host.indexOf("tp-em.com") !== -1) return true;
    if (host.indexOf("tpemb.com") !== -1) return true;
    if (host.indexOf("travelpayouts") !== -1) return true;

    // Add your partners here as you go:
    // if (host.indexOf("booking.com") !== -1) return true;
    // if (host.indexOf("agoda.com") !== -1) return true;
    // if (host.indexOf("expedia.") !== -1) return true;

    return false;
  }

  function classifyOutbound(urlObj) {
    // Simple categorization for GA4 reports
    var path = (urlObj.pathname || "").toLowerCase();
    var host = (urlObj.hostname || "").toLowerCase();

    // Partner/affiliate
    if (isAffiliateOrPartner(urlObj)) return "affiliate";

    // Travel intent guess (optional)
    if (host.indexOf("booking") !== -1 || host.indexOf("hotels") !== -1) return "booking";
    if (host.indexOf("cruise") !== -1) return "cruise";
    if (path.indexOf("car") !== -1 && path.indexOf("rent") !== -1) return "car_rental";

    return "outbound";
  }

  /* ---------- Partials injection (optional) ---------- */

  function injectPartial(targetSelector, url, cb) {
    var mount = $(targetSelector);
    if (!mount) { if (cb) cb(false); return; }

    // fetch support check
    if (!WIN.fetch) { if (cb) cb(false); return; }

    WIN.fetch(url, { cache: "no-cache" })
      .then(function (res) {
        if (!res || !res.ok) throw new Error("Partial fetch failed: " + (res ? res.status : "no response"));
        return res.text();
      })
      .then(function (html) {
        mount.innerHTML = html;
        if (cb) cb(true);
      })
      .catch(function () {
        if (cb) cb(false);
      });
  }

  /* ---------- DOM init tasks ---------- */

  function setFooterDates() {
    var now = new Date();

    // Year
    setTextById("year", now.getFullYear());

    // Last updated (only if empty)
    var lastUpdatedEl = DOC.getElementById("lastUpdated");
    if (lastUpdatedEl) {
      var txt = trimStr(lastUpdatedEl.textContent);
      if (!txt) lastUpdatedEl.textContent = now.toISOString().slice(0, 10);
    }
  }

  function highlightActiveNav() {
    // Sets aria-current="page" on best matching nav link
    var nav = $(".nav");
    if (!nav) return;

    var links = nav.getElementsByTagName("a");
    if (!links || !links.length) return;

    var path = (WIN.location.pathname || "/").toLowerCase();

    // Normalize: treat /index.html as /
    if (path.indexOf("/index.html") !== -1) path = path.replace("/index.html", "/");

    var best = null;
    var bestLen = -1;

    for (var i = 0; i < links.length; i++) {
      var href = links[i].getAttribute("href") || "";
      if (!href) continue;

      // Only internal paths
      if (href.indexOf("http") === 0) continue;

      // Normalize
      var h = href.toLowerCase();
      if (h === "/") {
        if (path === "/") { best = links[i]; bestLen = 1; }
        continue;
      }

      // If current path starts with link path
      if (h.charAt(0) === "/" && path.indexOf(h) === 0 && h.length > bestLen) {
        best = links[i];
        bestLen = h.length;
      }
    }

    // Clear old
    for (var j = 0; j < links.length; j++) {
      if (links[j].getAttribute("aria-current") === "page") {
        links[j].removeAttribute("aria-current");
      }
    }

    if (best) best.setAttribute("aria-current", "page");
  }

  function handleAnchorClicks() {
    // Smooth scroll for internal #hash links with sticky header offset
    on(DOC, "click", function (e) {
      e = e || WIN.event;
      var target = e.target || e.srcElement;
      var a = getClosestLink(target);
      if (!a) return;

      var href = a.getAttribute("href") || "";
      if (!href) return;

      // Only same-page hashes like #featured
      if (href.charAt(0) === "#") {
        var id = href.slice(1);
        var el = id ? DOC.getElementById(id) : null;
        if (el) {
          if (e.preventDefault) e.preventDefault();
          else e.returnValue = false;

          scrollToWithOffset(el);
        }
      }
    });
  }

  function trackOutboundClicks() {
    on(DOC, "click", function (e) {
      e = e || WIN.event;
      var target = e.target || e.srcElement;
      var a = getClosestLink(target);
      if (!a || !a.href) return;

      // Ignore downloads/mailto/tel/javascript
      var rawHref = a.getAttribute("href") || "";
      var lower = rawHref.toLowerCase();
      if (lower.indexOf("mailto:") === 0) return;
      if (lower.indexOf("tel:") === 0) return;
      if (lower.indexOf("javascript:") === 0) return;

      var urlObj = parseURL(a.href);
      if (isSameHost(urlObj)) return;

      var type = classifyOutbound(urlObj);

      // Track
      gtagEvent("outbound_click", {
        event_category: type,
        event_label: urlObj.href,
        transport_type: "beacon"
      });
    });
  }

  function trackAffiliateClicks() {
    // Tracks clicks on explicit affiliate CTAs marked with .js-aff
    on(DOC, "click", function (e) {
      e = e || WIN.event;
      var target = e.target || e.srcElement;
      var a = getClosestLink(target);
      if (!a) return;

      var cls = a.className || "";
      if ((" " + cls + " ").indexOf(" js-aff ") === -1) return;

      var url = a.getAttribute("href") || a.href || "";
      if (!url) return;

      // Optional: detect program from URL
      var program = "affiliate";
      try {
        var u = parseURL(url);
        var host = (u.hostname || "").toLowerCase();
        if (host.indexOf("airalo") !== -1) program = "airalo";
        else if (host.indexOf("tp-em.com") !== -1 || host.indexOf("tpemb.com") !== -1) program = "travelpayouts";
      } catch (_) {}

      gtagEvent("affiliate_click", {
        affiliate_program: program,
        destination: url
      });
    }, { passive: true });
  }

  function trackWidgetEngagement() {
    // One event per pageview when user interacts with eSIM widget section
    var fired = false;

    on(DOC, "click", function (e) {
      if (fired) return;

      var el = DOC.getElementById("esim-search");
      if (!el) return;

      var target = e.target || e.srcElement;

      // closest() fallback-free check
      try {
        if (el.contains(target)) {
          fired = true;
          gtagEvent("widget_engagement", {
            widget: "tp_esim_search"
          });
        }
      } catch (_) {}
    }, { passive: true });
  }

  function initMobileNav() {
    // Requires: .burger, .nav-scrim, .nav-drawer (in injected header)
    var burger = DOC.querySelector(".burger");
    if (!burger) return;

    var scrim = DOC.querySelector(".nav-scrim");
    var drawer = DOC.querySelector(".nav-drawer");

    function setOpen(open) {
      if (open) {
        DOC.body.classList.add("nav-open");
        burger.setAttribute("aria-expanded", "true");
      } else {
        DOC.body.classList.remove("nav-open");
        burger.setAttribute("aria-expanded", "false");
      }
    }

    on(burger, "click", function (e) {
      if (e && e.preventDefault) e.preventDefault();
      setOpen(!DOC.body.classList.contains("nav-open"));
    });

    if (scrim) {
      on(scrim, "click", function () { setOpen(false); });
    }

    // ESC closes
    on(DOC, "keydown", function (e) {
      e = e || WIN.event;
      var key = e.key || e.keyCode;
      if (!DOC.body.classList.contains("nav-open")) return;
      if (key === "Escape" || key === "Esc" || key === 27) setOpen(false);
    });

    // Clicking a link inside drawer closes
    if (drawer) {
      on(drawer, "click", function (e) {
        var target = e.target || e.srcElement;
        var a = getClosestLink(target);
        if (a) setOpen(false);
      });
    }
  }

  function measureVitalsHints() {
    // Lightweight “signals” you can use in GA4 (optional, safe)
    try {
      var t0 = (WIN.performance && WIN.performance.timing) ? WIN.performance.timing : null;
      if (!t0) return;

      var dcl = t0.domContentLoadedEventEnd - t0.navigationStart;
      if (dcl > 0 && hasGtag()) {
        gtagEvent("timing_complete", {
          name: "dom_content_loaded",
          value: dcl,
          event_category: "performance"
        });
      }
    } catch (_) {}
  }

  /* ---------- Init order (works with partials) ---------- */

  function initAll() {
    setFooterDates();
    highlightActiveNav();
    initMobileNav();
    handleAnchorClicks();
    trackOutboundClicks();
    trackAffiliateClicks();
    trackWidgetEngagement();
    measureVitalsHints();
  }

  function initWithPartials() {
    var hasHeaderSlot = !!$("#site-header");
    var hasFooterSlot = !!$("#site-footer");

    if (hasHeaderSlot || hasFooterSlot) {
      var done = 0;

      function next() {
        done++;
        if (done >= 2) initAll();
      }

      if (hasHeaderSlot) injectPartial("#site-header", "/partials/header.html", next);
      else next();

      if (hasFooterSlot) injectPartial("#site-footer", "/partials/footer.html", next);
      else next();

      return;
    }

    initAll();
  }

  // DOM ready
  if (DOC.readyState === "loading") {
    on(DOC, "DOMContentLoaded", initWithPartials);
  } else {
    initWithPartials();
  }
})();
