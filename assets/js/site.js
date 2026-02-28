/* ==========================================================================
   TripGuidely site.js (premium + compatible) — FULL (UPDATED)
   - Works even if header/footer are injected later
   - Old browser friendly (no arrow funcs, no optional chaining)
   - Mobile nav (burger + drawer + scrim + ESC) + close on link click
   - Outbound tracking (GA4 gtag) + affiliate tagging
   - Affiliate CTA tracking (.js-aff) centralized here (remove inline scripts)
   - Widget engagement tracking (#esim-search) (fires once)
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

  function trimStr(s) {
    return (s || "").replace(/^\s+|\s+$/g, "");
  }

  function setTextById(id, value) {
    var el = DOC.getElementById(id);
    if (el) el.textContent = String(value);
  }

  function parseURL(href) {
    // URL() not supported in very old browsers; fallback to anchor element.
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

  function isSameHost(urlObj) {
    try {
      return urlObj && urlObj.hostname && urlObj.hostname === WIN.location.hostname;
    } catch (_) {
      return true;
    }
  }

  function closestAnchor(el) {
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
    // Uses actual header height (most reliable with injected partials)
    var header = $(".header");
    var h = header ? header.offsetHeight : 0;
    return (h || 72) + 12;
  }

  function scrollToWithOffset(el) {
    if (!el) return;

    var rect = el.getBoundingClientRect ? el.getBoundingClientRect() : null;
    var y = 0;

    if (rect && typeof rect.top === "number") {
      y = rect.top + (WIN.pageYOffset || DOC.documentElement.scrollTop || 0);
    } else {
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
    var host = (urlObj.hostname || "").toLowerCase();
    if (!host) return false;

    if (host.indexOf("tp-em.com") !== -1) return true;
    if (host.indexOf("tpemb.com") !== -1) return true;
    if (host.indexOf("travelpayouts") !== -1) return true;

    // Add more partners later if needed
    // if (host.indexOf("booking.com") !== -1) return true;
    return false;
  }

  function classifyOutbound(urlObj) {
    var path = (urlObj.pathname || "").toLowerCase();
    var host = (urlObj.hostname || "").toLowerCase();

    if (isAffiliateOrPartner(urlObj)) return "affiliate";

    if (host.indexOf("booking") !== -1 || host.indexOf("hotels") !== -1) return "booking";
    if (host.indexOf("cruise") !== -1) return "cruise";
    if (path.indexOf("car") !== -1 && path.indexOf("rent") !== -1) return "car_rental";

    return "outbound";
  }

  /* ---------- Partials injection (optional) ---------- */

  function injectPartial(targetSelector, url, cb) {
    var mount = $(targetSelector);
    if (!mount) { if (cb) cb(false); return; }

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

    setTextById("year", now.getFullYear());

    var lastUpdatedEl = DOC.getElementById("lastUpdated");
    if (lastUpdatedEl) {
      var txt = trimStr(lastUpdatedEl.textContent);
      if (!txt) lastUpdatedEl.textContent = now.toISOString().slice(0, 10);
    }
  }

  function highlightActiveNav() {
    // Apply aria-current="page" to best match in desktop nav + drawer
    var path = (WIN.location.pathname || "/").toLowerCase();
    if (path.indexOf("/index.html") !== -1) path = path.replace("/index.html", "/");

    function applyTo(containerSelector) {
      var nav = $(containerSelector);
      if (!nav) return;

      var links = nav.getElementsByTagName("a");
      if (!links || !links.length) return;

      var best = null;
      var bestLen = -1;

      for (var i = 0; i < links.length; i++) {
        var href = links[i].getAttribute("href") || "";
        if (!href) continue;

        // ignore external
        if (href.indexOf("http") === 0) continue;

        var h = href.toLowerCase();
        if (h === "/") {
          if (path === "/") { best = links[i]; bestLen = 1; }
          continue;
        }

        if (h.charAt(0) === "/" && path.indexOf(h) === 0 && h.length > bestLen) {
          best = links[i];
          bestLen = h.length;
        }
      }

      for (var j = 0; j < links.length; j++) {
        if (links[j].getAttribute("aria-current") === "page") {
          links[j].removeAttribute("aria-current");
        }
      }

      if (best) best.setAttribute("aria-current", "page");
    }

    applyTo(".nav");
    applyTo(".nav-drawer");
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

      var rawHref = a.getAttribute("href") || "";
      var lower = rawHref.toLowerCase();
      if (lower.indexOf("mailto:") === 0) return;
      if (lower.indexOf("tel:") === 0) return;
      if (lower.indexOf("javascript:") === 0) return;
      if (lower.indexOf("#") === 0) return;

      var urlObj = parseURL(a.href);
      if (isSameHost(urlObj)) return;

      var type = classifyOutbound(urlObj);

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

      var wrap = DOC.getElementById("esim-search");
      if (!wrap) return;

      var target = e.target || e.srcElement;
      try {
        if (wrap.contains(target)) {
          fired = true;
          gtagEvent("widget_engagement", {
            widget: "tp_esim_search",
            page_type: "hub"
          });
        }
      } catch (_) {}
    }, { passive: true });
  }

  function initMobileNav() {
    // Important: header is injected. So we init AFTER injection (initAll).
    // Also: use querySelector each init (no stale nodes).
    var burger = $(".burger");
    if (!burger) return;

    var scrim = $(".nav-scrim");
    var drawer = $(".nav-drawer");

    function isOpen() {
      return DOC.body.classList.contains("nav-open");
    }

    function setOpen(open) {
      if (open) {
        DOC.body.classList.add("nav-open");
        burger.setAttribute("aria-expanded", "true");
      } else {
        DOC.body.classList.remove("nav-open");
        burger.setAttribute("aria-expanded", "false");
      }
    }

    // Avoid double-binding if initAll runs again
    if (burger.getAttribute("data-nav-bound") === "1") {
      // Still ensure aria-expanded matches state
      burger.setAttribute("aria-expanded", isOpen() ? "true" : "false");
      return;
    }
    burger.setAttribute("data-nav-bound", "1");

    on(burger, "click", function (e) {
      if (e && e.preventDefault) e.preventDefault();
      setOpen(!isOpen());
    });

    if (scrim) {
      on(scrim, "click", function () { setOpen(false); });
    }

    // ESC closes
    on(DOC, "keydown", function (e) {
      e = e || WIN.event;
      var key = e.key || e.keyCode;
      if (!isOpen()) return;
      if (key === "Escape" || key === "Esc" || key === 27) setOpen(false);
    });

    // Clicking a link inside drawer closes (same page or navigation)
    if (drawer) {
      on(drawer, "click", function (e) {
        var target = e.target || e.srcElement;
        var a = getClosestLink(target);
        if (a) setOpen(false);
      });
    }

    // Optional: clicking any normal in-page anchor while open closes too
    on(DOC, "click", function (e) {
      if (!isOpen()) return;
      var target = e.target || e.srcElement;
      var a = getClosestLink(target);
      if (!a) return;

      var href = a.getAttribute("href") || "";
      if (href && href.charAt(0) === "#") setOpen(false);
    });
  }

  function measureVitalsHints() {
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
