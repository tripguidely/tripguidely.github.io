/* ==========================================================================
   TripGuidely home.js
   - Home-only hero tabs (Hotels / Flights / Transport / eSIM)
   - Safe with existing site.js home hotel search
   - Old-browser friendly
   - Accessible tab behavior
   - Simple validation + redirect for Flights and eSIM
   ========================================================================== */

(function () {
  "use strict";

  var DOC = document;
  var WIN = window;

  function $(sel, root) {
    return (root || DOC).querySelector(sel);
  }

  function $all(sel, root) {
    return (root || DOC).querySelectorAll(sel);
  }

  function on(el, evt, fn, opts) {
    if (!el) return;
    try {
      if (el.addEventListener) el.addEventListener(evt, fn, opts || false);
      else if (el.attachEvent) el.attachEvent("on" + evt, fn);
    } catch (_) {
      try {
        if (el.addEventListener) el.addEventListener(evt, fn, false);
      } catch (__) {}
    }
  }

  function trimStr(s) {
    return String(s || "").replace(/^\s+|\s+$/g, "");
  }

  function pad2(n) {
    n = Number(n);
    return n < 10 ? "0" + n : "" + n;
  }

  function todayISO() {
    var d = new Date();
    return d.getFullYear() + "-" + pad2(d.getMonth() + 1) + "-" + pad2(d.getDate());
  }

  function addDaysISO(days) {
    var d = new Date();
    d.setDate(d.getDate() + Number(days || 0));
    return d.getFullYear() + "-" + pad2(d.getMonth() + 1) + "-" + pad2(d.getDate());
  }

  function nextDayISO(iso) {
    var parts = String(iso || "").split("-");
    if (parts.length !== 3) return addDaysISO(1);

    var d = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));
    if (isNaN(d.getTime())) return addDaysISO(1);

    d.setDate(d.getDate() + 1);
    return d.getFullYear() + "-" + pad2(d.getMonth() + 1) + "-" + pad2(d.getDate());
  }

  function setText(el, value) {
    if (el) el.textContent = String(value || "");
  }

  function tryTrack(eventName, params) {
    try {
      if (typeof WIN.gtag === "function") {
        WIN.gtag("event", eventName, params || {});
      }
    } catch (_) {}
  }

  function buildAffiliateUrl(base, subid) {
    var cleanBase = trimStr(base);
    var cleanSubid = trimStr(subid);

    if (!cleanBase) return "";

    if (!cleanSubid) return cleanBase;

    try {
      var url = new URL(cleanBase, WIN.location.href);
      if (!url.searchParams.get("subid")) {
        url.searchParams.set("subid", cleanSubid);
      }
      return url.toString();
    } catch (_) {
      if (cleanBase.indexOf("?") === -1) return cleanBase + "?subid=" + encodeURIComponent(cleanSubid);
      if (/[?&]subid=/.test(cleanBase)) return cleanBase;
      return cleanBase + "&subid=" + encodeURIComponent(cleanSubid);
    }
  }

  function setPanelControlsState(panel, isActive) {
    if (!panel) return;

    panel.hidden = !isActive;

    var fields = $all("input, select, textarea, button", panel);
    var i, field;
    for (i = 0; i < fields.length; i++) {
      field = fields[i];

      if (!isActive) {
        field.setAttribute("data-was-disabled", field.disabled ? "1" : "0");
        field.disabled = true;
      } else {
        if (field.getAttribute("data-was-disabled") === "0") {
          field.disabled = false;
        }
      }
    }

    var links = $all("a", panel);
    for (i = 0; i < links.length; i++) {
      if (!isActive) {
        links[i].setAttribute("tabindex", "-1");
        links[i].setAttribute("aria-hidden", "true");
      } else {
        links[i].removeAttribute("tabindex");
        links[i].removeAttribute("aria-hidden");
      }
    }
  }

  function initHeroTabs() {
    var root = $(".hero-tool-shell");
    if (!root) return;
    if (root.getAttribute("data-home-tabs-bound") === "1") return;
    root.setAttribute("data-home-tabs-bound", "1");

    var tabs = $all(".hero-tab", root);
    var panels = $all(".hero-tab-panel", root);

    if (!tabs.length || !panels.length) return;

    function activateTab(tabName, moveFocus) {
      var i, tab, panel, isActive;

      for (i = 0; i < tabs.length; i++) {
        tab = tabs[i];
        isActive = tab.getAttribute("data-tab") === tabName;
        tab.className = isActive ? "hero-tab active" : "hero-tab";
        tab.setAttribute("aria-selected", isActive ? "true" : "false");
        tab.tabIndex = isActive ? 0 : -1;

        if (isActive && moveFocus) {
          try {
            tab.focus();
          } catch (_) {}
        }
      }

      for (i = 0; i < panels.length; i++) {
        panel = panels[i];
        isActive = panel.getAttribute("data-panel") === tabName;
        if (isActive) {
          if (panel.className.indexOf("active") === -1) panel.className += " active";
        } else {
          panel.className = panel.className.replace(/\s?active/g, "");
        }
        setPanelControlsState(panel, isActive);
      }

      tryTrack("widget_tab_change", {
        widget: "home_hero_tabs",
        tab_name: tabName,
        page_type: "home"
      });
    }

    function getTabIndex(current) {
      var i;
      for (i = 0; i < tabs.length; i++) {
        if (tabs[i] === current) return i;
      }
      return 0;
    }

    function onTabKeydown(e) {
      e = e || WIN.event;
      var key = e.key || e.keyCode;
      var current = e.currentTarget || e.srcElement;
      var index = getTabIndex(current);
      var nextIndex = index;

      if (key === "ArrowRight" || key === 39) nextIndex = (index + 1) % tabs.length;
      else if (key === "ArrowLeft" || key === 37) nextIndex = (index - 1 + tabs.length) % tabs.length;
      else if (key === "Home" || key === 36) nextIndex = 0;
      else if (key === "End" || key === 35) nextIndex = tabs.length - 1;
      else return;

      if (e.preventDefault) e.preventDefault();
      else e.returnValue = false;

      activateTab(tabs[nextIndex].getAttribute("data-tab"), true);
    }

    var i, initialTabName;
    for (i = 0; i < tabs.length; i++) {
      on(tabs[i], "click", function () {
        activateTab(this.getAttribute("data-tab"), false);
      });

      on(tabs[i], "keydown", onTabKeydown);
    }

    initialTabName = "hotels";
    for (i = 0; i < tabs.length; i++) {
      if (tabs[i].className.indexOf("active") !== -1) {
        initialTabName = tabs[i].getAttribute("data-tab") || "hotels";
        break;
      }
    }

    activateTab(initialTabName, false);
  }

  function initFlightSearch() {
    var form = DOC.getElementById("home-flight-search-form");
    if (!form) return;
    if (form.getAttribute("data-home-flight-bound") === "1") return;
    form.setAttribute("data-home-flight-bound", "1");

    var from = DOC.getElementById("home-flight-from");
    var to = DOC.getElementById("home-flight-to");
    var departure = DOC.getElementById("home-flight-departure");
    var ret = DOC.getElementById("home-flight-return");
    var errorBox = DOC.getElementById("home-flight-search-error");

    if (!from || !to || !departure || !ret) return;

    var minDate = todayISO();
    departure.min = minDate;
    ret.min = addDaysISO(1);

    if (!departure.value) departure.value = addDaysISO(14);
    if (!ret.value) ret.value = addDaysISO(21);

    on(departure, "change", function () {
      var dep = trimStr(departure.value);
      if (!dep) {
        ret.min = addDaysISO(1);
        return;
      }

      ret.min = nextDayISO(dep);

      if (trimStr(ret.value) && ret.value <= dep) {
        ret.value = nextDayISO(dep);
      }
    });

    function validate(data) {
      if (!trimStr(data.from)) return "Please enter a departure city or airport.";
      if (!trimStr(data.to)) return "Please enter a destination city or airport.";
      if (!trimStr(data.departure)) return "Please choose a departure date.";
      if (trimStr(data.return_date) && data.return_date <= data.departure) {
        return "Return date must be after departure date.";
      }
      return "";
    }

    on(form, "submit", function (e) {
      var targetUrl, error;
      var data = {
        from: trimStr(from.value),
        to: trimStr(to.value),
        departure: trimStr(departure.value),
        return_date: trimStr(ret.value)
      };

      if (e && e.preventDefault) e.preventDefault();
      else e.returnValue = false;

      error = validate(data);
      if (error) {
        setText(errorBox, error);
        if (!data.from) {
          try { from.focus(); } catch (_) {}
        } else if (!data.to) {
          try { to.focus(); } catch (_) {}
        } else {
          try { departure.focus(); } catch (_) {}
        }
        return;
      }

      setText(errorBox, "");

      targetUrl = buildAffiliateUrl(
        form.getAttribute("data-affiliate-base"),
        form.getAttribute("data-subid")
      );

      tryTrack("flight_search", {
        page_type: "home",
        affiliate_program: "kiwi",
        origin: data.from,
        destination: data.to
      });

      if (targetUrl) WIN.location.href = targetUrl;
    });
  }

  function initEsimSearch() {
    var form = DOC.getElementById("home-esim-search-form");
    if (!form) return;
    if (form.getAttribute("data-home-esim-bound") === "1") return;
    form.setAttribute("data-home-esim-bound", "1");

    var destination = DOC.getElementById("home-esim-destination");
    var duration = DOC.getElementById("home-esim-duration");
    var usage = DOC.getElementById("home-esim-usage");
    var errorBox = DOC.getElementById("home-esim-search-error");

    if (!destination || !duration || !usage) return;

    on(form, "submit", function (e) {
      var targetUrl;
      var cleanDestination = trimStr(destination.value);

      if (e && e.preventDefault) e.preventDefault();
      else e.returnValue = false;

      if (!cleanDestination) {
        setText(errorBox, "Please enter a destination.");
        try {
          destination.focus();
        } catch (_) {}
        return;
      }

      setText(errorBox, "");

      targetUrl = buildAffiliateUrl(
        form.getAttribute("data-affiliate-base"),
        form.getAttribute("data-subid")
      );

      tryTrack("esim_search", {
        page_type: "home",
        affiliate_program: "airalo",
        destination: cleanDestination,
        trip_length: trimStr(duration.value),
        data_usage: trimStr(usage.value)
      });

      if (targetUrl) WIN.location.href = targetUrl;
    });
  }

  function initTransportPanelTracking() {
    var panel = DOC.getElementById("hero-panel-transport");
    if (!panel) return;
    if (panel.getAttribute("data-home-transport-bound") === "1") return;
    panel.setAttribute("data-home-transport-bound", "1");

    on(panel, "click", function (e) {
      e = e || WIN.event;
      var target = e.target || e.srcElement;
      var link = target;

      while (link && link !== DOC) {
        if (link.tagName && String(link.tagName).toLowerCase() === "a") break;
        link = link.parentNode;
      }

      if (!link || link === DOC) return;

      tryTrack("transport_panel_click", {
        page_type: "home",
        destination: link.getAttribute("href") || "",
        link_text: trimStr(link.textContent || "")
      });
    });
  }

  function initHome() {
    if (!DOC.body || DOC.body.getAttribute("data-page") !== "home") return;
    if (WIN.__tg_home_initialized) return;
    WIN.__tg_home_initialized = true;

    initHeroTabs();
    initFlightSearch();
    initEsimSearch();
    initTransportPanelTracking();
  }

  if (DOC.readyState === "loading") on(DOC, "DOMContentLoaded", initHome);
  else initHome();
})();
