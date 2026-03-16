/* ==========================================================================
   TripGuidely site.js (premium + compatible) — FULL (UPDATED + CONSENT v2.3)
   - Works even if header/footer are injected later
   - Old browser friendly (no arrow funcs, no optional chaining)
   - Mobile nav (burger + drawer + scrim + ESC) + close on link click
   - Outbound tracking (GA4 gtag) + affiliate tagging (only after consent)
   - Affiliate CTA tracking (.js-aff) centralized here
   - Widget engagement tracking (ANY .tp-widget + #esim-search + #search) (fires once per widget)
   - Custom page tracking for clearer GA4 reporting by page_type / path / title
   - Smooth internal anchors w/ sticky header offset (fallback-safe)
   - Consent Mode v2 default denied
   - Lazy-load GA4 only if accepted
   - Binds footer “Privacy choices” link (.js-consent) (no inline onclick)
   - Contact form AJAX + success/error UI for Formspree
   - Supports generic [data-include] partial injection
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
    try {
      if (el.addEventListener) el.addEventListener(evt, fn, opts || false);
      else if (el.attachEvent) el.attachEvent("on" + evt, fn);
    } catch (_) {
      try { if (el.addEventListener) el.addEventListener(evt, fn, false); } catch (__) {}
    }
  }

  function trimStr(s) {
    return (s || "").replace(/^\s+|\s+$/g, "");
  }

  function setTextById(id, value) {
    var el = DOC.getElementById(id);
    if (el) el.textContent = String(value);
  }

  function getAttr(el, name) {
    try {
      return el && el.getAttribute ? el.getAttribute(name) : null;
    } catch (_) {
      return null;
    }
  }

  function parseURL(href) {
    try {
      return new URL(href, WIN.location.href);
    } catch (_) {
      var a = DOC.createElement("a");
      a.href = href;
      if (!a.hostname && WIN.location && WIN.location.hostname) a.href = a.href;
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

  function closestByClass(el, className) {
    while (el && el !== DOC) {
      var cn = " " + (el.className || "") + " ";
      if (cn.indexOf(" " + className + " ") !== -1) return el;
      el = el.parentNode;
    }
    return null;
  }

  function getHeaderOffset() {
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

  function getPageType() {
    var p = getAttr(DOC.body, "data-page");
    return p ? String(p) : "unknown";
  }

  /* ---------- Consent + GA4 (lazy load + Consent Mode v2) ---------- */

  var CONSENT_KEY = "tg_consent_v2";
  var GA_MEASUREMENT_ID = "G-0GGMM5GYXJ";

  var memConsent = null;
  var pageViewTracked = false;

  function storageGet(key) {
    try { if (WIN.localStorage) return WIN.localStorage.getItem(key); } catch (_) {}
    return memConsent;
  }

  function storageSet(key, value) {
    try { if (WIN.localStorage) WIN.localStorage.setItem(key, value); }
    catch (_) { memConsent = value; }
  }

  function getConsent() {
    var v = storageGet(CONSENT_KEY);
    if (v === "granted" || v === "denied") return v;
    return "unknown";
  }

  function setConsent(value) {
    if (value !== "granted" && value !== "denied") return;
    storageSet(CONSENT_KEY, value);
  }

  function ensureDataLayer() {
    WIN.dataLayer = WIN.dataLayer || [];
    if (!WIN.gtag) {
      WIN.gtag = function () {
        try { WIN.dataLayer.push(arguments); } catch (_) {}
      };
    }
  }

  function hasGtag() {
    return typeof WIN.gtag === "function";
  }

  function setConsentModeDefault() {
    ensureDataLayer();
    try {
      WIN.gtag("consent", "default", {
        ad_storage: "denied",
        analytics_storage: "denied",
        ad_user_data: "denied",
        ad_personalization: "denied",
        wait_for_update: 500
      });
    } catch (_) {}
  }

  function setConsentModeGranted() {
    ensureDataLayer();
    try {
      WIN.gtag("consent", "update", {
        ad_storage: "granted",
        analytics_storage: "granted",
        ad_user_data: "granted",
        ad_personalization: "granted"
      });
    } catch (_) {}
  }

  function setConsentModeDenied() {
    ensureDataLayer();
    try {
      WIN.gtag("consent", "update", {
        ad_storage: "denied",
        analytics_storage: "denied",
        ad_user_data: "denied",
        ad_personalization: "denied"
      });
    } catch (_) {}
  }

  function loadGA4Once() {
    if (WIN.__tg_ga_loaded) return;
    WIN.__tg_ga_loaded = true;

    ensureDataLayer();

    var s = DOC.createElement("script");
    s.async = true;
    s.src = "https://www.googletagmanager.com/gtag/js?id=" + encodeURIComponent(GA_MEASUREMENT_ID);
    DOC.head.appendChild(s);

    try {
      WIN.gtag("js", new Date());
      WIN.gtag("config", GA_MEASUREMENT_ID, {
        anonymize_ip: true,
        page_location: WIN.location.href || "",
        page_path: WIN.location.pathname || "",
        page_title: DOC.title || ""
      });
    } catch (_) {}
  }

  function gtagEvent(name, params) {
    if (!hasGtag()) return;
    try { WIN.gtag("event", name, params || {}); } catch (_) {}
  }

  function trackPageViewDetails() {
    if (pageViewTracked) return;
    if (getConsent() !== "granted") return;
    if (!hasGtag()) return;

    pageViewTracked = true;

    gtagEvent("tripguidely_page_view", {
      page_type: getPageType(),
      page_title: DOC.title || "",
      page_path: WIN.location.pathname || "",
      page_location: WIN.location.href || ""
    });
  }

  function removeConsentBanner() {
    var el = DOC.getElementById("tg-consent");
    if (el && el.parentNode) el.parentNode.removeChild(el);

    DOC.body.className = (DOC.body.className || "").replace(/\bconsent-open\b/g, "");
    DOC.body.className = trimStr(DOC.body.className || "");
  }

  function renderConsentBanner() {
    if (DOC.getElementById("tg-consent")) return;

    var banner = DOC.createElement("div");
    banner.id = "tg-consent";
    banner.className = "consent-banner";
    banner.setAttribute("role", "dialog");
    banner.setAttribute("aria-live", "polite");
    banner.setAttribute("aria-label", "Privacy choices");

    banner.innerHTML =
      '<div class="wrap">' +
        '<div class="consent-copy">' +
          '<p class="consent-title">Privacy choices</p>' +
          '<p class="consent-text">We use analytics to improve TripGuidely and measure what helps travelers most. You can accept or decline.</p>' +
        '</div>' +
        '<div class="consent-actions">' +
          '<button type="button" class="btn" id="tg-consent-decline">Decline</button>' +
          '<button type="button" class="btn primary" id="tg-consent-accept">Accept</button>' +
        '</div>' +
      '</div>';

    DOC.body.appendChild(banner);
    DOC.body.className = trimStr((DOC.body.className ? DOC.body.className + " " : "") + "consent-open");

    var btnA = DOC.getElementById("tg-consent-accept");
    var btnD = DOC.getElementById("tg-consent-decline");

    if (btnA) {
      on(btnA, "click", function () {
        setConsent("granted");
        setConsentModeGranted();
        removeConsentBanner();
        loadGA4Once();
        gtagEvent("consent_update", { status: "granted", page_type: getPageType() });
        trackPageViewDetails();
      });
    }

    if (btnD) {
      on(btnD, "click", function () {
        setConsent("denied");
        setConsentModeDenied();
        removeConsentBanner();
      });
    }
  }

  function initConsent() {
    setConsentModeDefault();

    var c = getConsent();
    if (c === "granted") {
      setConsentModeGranted();
      loadGA4Once();
      trackPageViewDetails();
      return;
    }
    if (c === "denied") {
      setConsentModeDenied();
      return;
    }
    renderConsentBanner();
  }

  function openConsentManager() {
    renderConsentBanner();
  }

  WIN.TripGuidelyConsent = WIN.TripGuidelyConsent || {};
  WIN.TripGuidelyConsent.open = openConsentManager;
  WIN.TripGuidelyConsent.get = getConsent;

  /* ---------- Bind footer “Privacy choices” link (.js-consent) ---------- */

  function bindConsentLinks() {
    if (DOC.documentElement && DOC.documentElement.getAttribute("data-consentlink-bound") === "1") return;
    try { DOC.documentElement.setAttribute("data-consentlink-bound", "1"); } catch (_) {}

    on(DOC, "click", function (e) {
      e = e || WIN.event;
      var target = e.target || e.srcElement;
      var a = getClosestLink(target);
      if (!a) return;

      var cls = a.className || "";
      if ((" " + cls + " ").indexOf(" js-consent ") === -1) return;

      if (e.preventDefault) e.preventDefault();
      else e.returnValue = false;

      try {
        if (WIN.TripGuidelyConsent && WIN.TripGuidelyConsent.open) WIN.TripGuidelyConsent.open();
      } catch (_) {}
    });
  }

  /* ---------- GA helpers (affiliate classification) ---------- */

  function isAffiliateOrPartner(urlObj) {
    var host = (urlObj.hostname || "").toLowerCase();
    if (!host) return false;

    if (host.indexOf("tp-em.com") !== -1) return true;
    if (host.indexOf("tpemb.com") !== -1) return true;
    if (host.indexOf("travelpayouts") !== -1) return true;

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

  /* ---------- Partials injection ---------- */

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

  function injectDataIncludes(cb) {
    var nodes = DOC.querySelectorAll("[data-include]");
    var total = nodes ? nodes.length : 0;
    var done = 0;

    if (!total) {
      if (cb) cb();
      return;
    }

    function next() {
      done++;
      if (done >= total && cb) cb();
    }

    for (var i = 0; i < total; i++) {
      (function (node) {
        var url = getAttr(node, "data-include");
        if (!url || !WIN.fetch) {
          next();
          return;
        }

        WIN.fetch(url, { cache: "no-cache" })
          .then(function (res) {
            if (!res || !res.ok) throw new Error("Partial fetch failed");
            return res.text();
          })
          .then(function (html) {
            node.innerHTML = html;
            next();
          })
          .catch(function () {
            next();
          });
      })(nodes[i]);
    }
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
        if (links[j].getAttribute("aria-current") === "page") links[j].removeAttribute("aria-current");
      }

      if (best) best.setAttribute("aria-current", "page");
    }

    applyTo(".nav");
    applyTo(".nav-drawer");
  }

  function handleAnchorClicks() {
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
      if (getConsent() !== "granted") return;

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
    on(DOC, "click", function (e) {
      if (getConsent() !== "granted") return;

      e = e || WIN.event;
      var target = e.target || e.srcElement;
      var a = getClosestLink(target);
      if (!a) return;

      var cls = a.className || "";
      if ((" " + cls + " ").indexOf(" js-aff ") === -1) return;

      var url = a.getAttribute("href") || a.href || "";
      if (!url) return;

      var pageType = getPageType();
      var program = getAttr(a, "data-aff");
      if (program) program = String(program);

      if (!program) {
        program = "affiliate";
        try {
          var u = parseURL(url);
          var host = (u.hostname || "").toLowerCase();
          if (host.indexOf("airalo") !== -1) program = "airalo";
          else if (host.indexOf("tp-em.com") !== -1 || host.indexOf("tpemb.com") !== -1) program = "travelpayouts";
        } catch (_) {}
      }

      gtagEvent("affiliate_click", {
        affiliate_program: program,
        page_type: pageType,
        destination: url,
        transport_type: "beacon"
      });
    });
  }

  function trackWidgetEngagement() {
    var firedMap = {};

    function markFired(key) { firedMap[key] = true; }
    function isFired(key) { return !!firedMap[key]; }

    function fire(key, meta) {
      if (isFired(key)) return;
      markFired(key);
      gtagEvent("widget_engagement", meta);
    }

    on(DOC, "click", function (e) {
      if (getConsent() !== "granted") return;

      e = e || WIN.event;
      var target = e.target || e.srcElement;
      if (!target) return;

      var esimWrap = DOC.getElementById("esim-search");
      if (esimWrap) {
        try {
          if (esimWrap.contains(target)) {
            fire("esim-search", { widget: "esim-search", page_type: getPageType() });
          }
        } catch (_) {}
      }

      var search = DOC.getElementById("search");
      if (search) {
        try {
          if (search.contains(target)) {
            fire("search-section", { widget: "search-section", page_type: getPageType() });
          }
        } catch (_) {}
      }

      var w = closestByClass(target, "tp-widget");
      if (w) {
        var wid = w.id ? String(w.id) : "tp-widget";
        fire("tp:" + wid, { widget: wid, page_type: getPageType() });
      }
    });
  }

  function initMobileNav() {
    var burger = $(".burger");
    if (!burger) return;

    var scrim = $(".nav-scrim");
    var drawer = $(".nav-drawer");

    function hasClassList() { return !!(DOC.body && DOC.body.classList); }

    function isOpen() {
      if (!hasClassList()) return ((" " + (DOC.body.className || "") + " ").indexOf(" nav-open ") !== -1);
      return DOC.body.classList.contains("nav-open");
    }

    function setOpen(open) {
      if (!DOC.body) return;

      if (hasClassList()) {
        if (open) DOC.body.classList.add("nav-open");
        else DOC.body.classList.remove("nav-open");
      } else {
        var cn = " " + (DOC.body.className || "") + " ";
        cn = cn.replace(/\snav-open\s/g, " ");
        if (open) cn += " nav-open ";
        DOC.body.className = trimStr(cn);
      }

      try { burger.setAttribute("aria-expanded", open ? "true" : "false"); } catch (_) {}
    }

    if (burger.getAttribute("data-nav-bound") === "1") {
      burger.setAttribute("aria-expanded", isOpen() ? "true" : "false");
      return;
    }
    burger.setAttribute("data-nav-bound", "1");

    on(burger, "click", function (e) {
      if (e && e.preventDefault) e.preventDefault();
      setOpen(!isOpen());
    });

    if (scrim) on(scrim, "click", function () { setOpen(false); });

    on(DOC, "keydown", function (e) {
      e = e || WIN.event;
      var key = e.key || e.keyCode;
      if (!isOpen()) return;
      if (key === "Escape" || key === "Esc" || key === 27) setOpen(false);
    });

    if (drawer) {
      on(drawer, "click", function (e) {
        var target = e.target || e.srcElement;
        var a = getClosestLink(target);
        if (a) setOpen(false);
      });
    }

    on(DOC, "click", function (e) {
      if (!isOpen()) return;
      var target = e.target || e.srcElement;
      var a = getClosestLink(target);
      if (!a) return;

      var href = a.getAttribute("href") || "";
      if (href && href.charAt(0) === "#") setOpen(false);
    });
  }

  function initContactForm() {
    var form = DOC.querySelector(".contact-form");
    if (!form) return;
    if (form.getAttribute("data-contact-bound") === "1") return;
    form.setAttribute("data-contact-bound", "1");

    var submitBtn = form.querySelector('button[type="submit"]');
    var endpoint = form.getAttribute("action");
    if (!endpoint) return;

    var status = DOC.createElement("div");
    status.className = "form-status";
    status.setAttribute("role", "status");
    status.setAttribute("aria-live", "polite");
    form.appendChild(status);

    function showStatus(type, message) {
      status.className = "form-status is-visible " + (type === "success" ? "is-success" : "is-error");
      status.textContent = message;
    }

    function clearInvalid() {
      var fields = form.querySelectorAll("input, select, textarea");
      var i;
      for (i = 0; i < fields.length; i++) {
        fields[i].removeAttribute("aria-invalid");
      }
    }

    function validateForm() {
      var required = form.querySelectorAll("[required]");
      var i, field, tag, value;

      clearInvalid();

      for (i = 0; i < required.length; i++) {
        field = required[i];
        tag = (field.tagName || "").toLowerCase();
        value = trimStr(field.value || "");

        if (!value) {
          field.setAttribute("aria-invalid", "true");
          try { field.focus(); } catch (_) {}
          return false;
        }

        if (tag === "select" && (!field.value || field.value === "")) {
          field.setAttribute("aria-invalid", "true");
          try { field.focus(); } catch (_) {}
          return false;
        }

        if ((field.type || "").toLowerCase() === "email") {
          if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
            field.setAttribute("aria-invalid", "true");
            try { field.focus(); } catch (_) {}
            return false;
          }
        }
      }

      return true;
    }

    on(form, "submit", function (e) {
      if (e && e.preventDefault) e.preventDefault();
      else e.returnValue = false;

      if (!WIN.fetch) {
        form.submit();
        return;
      }

      if (!validateForm()) {
        showStatus("error", "Please complete the required fields before sending your message.");
        return;
      }

      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.setAttribute("aria-busy", "true");
        submitBtn.textContent = "Sending...";
      }

      status.className = "form-status";
      status.textContent = "";

      var formData = new FormData(form);

      WIN.fetch(endpoint, {
        method: "POST",
        body: formData,
        headers: {
          "Accept": "application/json"
        }
      })
        .then(function (res) {
          if (!res || !res.ok) throw new Error("Form submit failed");
          return res.json ? res.json() : {};
        })
        .then(function () {
          form.reset();
          clearInvalid();
          showStatus("success", "Thanks. Your message has been sent successfully.");
          try { status.scrollIntoView({ behavior: "smooth", block: "nearest" }); } catch (_) {}

          if (getConsent() === "granted") {
            gtagEvent("contact_form_submit", {
              form_name: "tripguidely_contact",
              page_type: getPageType()
            });
          }
        })
        .catch(function () {
          showStatus("error", "Sorry, something went wrong while sending your message. Please try again or email us directly.");
        })
        .then(function () {
          if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.removeAttribute("aria-busy");
            submitBtn.textContent = "Send Message";
          }
        });
    });
  }

  function measureVitalsHints() {
    try {
      if (getConsent() !== "granted") return;

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

    initConsent();
    bindConsentLinks();

    initContactForm();

    trackOutboundClicks();
    trackAffiliateClicks();
    trackWidgetEngagement();
    measureVitalsHints();
    trackPageViewDetails();
  }

  function initWithPartials() {
    var hasHeaderSlot = !!$("#site-header");
    var hasFooterSlot = !!$("#site-footer");
    var total = 0;
    var done = 0;

    function afterCorePartials() {
      injectDataIncludes(function () {
        initAll();
      });
    }

    function next() {
      done++;
      if (done >= total) afterCorePartials();
    }

    if (hasHeaderSlot) total++;
    if (hasFooterSlot) total++;

    if (total === 0) {
      afterCorePartials();
      return;
    }

    if (hasHeaderSlot) injectPartial("#site-header", "/partials/header.html", next);
    if (hasFooterSlot) injectPartial("#site-footer", "/partials/footer.html", next);
  }

  if (DOC.readyState === "loading") on(DOC, "DOMContentLoaded", initWithPartials);
  else initWithPartials();
})();
