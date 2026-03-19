/* ==========================================================================
   TripGuidely — transport.js
   Purpose:
   - Dedicated transport widget logic
   - Keeps site.js lighter and reduces cross-feature bugs
   - Feature scope: #transport-search-form only
   - Compatible with older browsers
   - Safe against double-binding
   - Designed to be filled with current transport code progressively
   ========================================================================== */

(function (WIN, DOC) {
  "use strict";

  /* ==========================================================================
     1) Feature guards / shared dependencies
     ========================================================================== */

  // Expected shared globals/helpers from main site bundle:
  // - on(el, eventName, handler)
  // - getAttr(el, attrName)
  // - trimStr(str)
  // - getConsent()
  // - gtagEvent(name, payload)
  // - getPageType()

  if (!WIN || !DOC) return;

  /* ==========================================================================
     2) Static config
     ========================================================================== */

  var TRAIN_MARKET_MAP = {
    "japan": {
      from: "Tokyo",
      to: "Osaka",
      title: "Trains",
      copy: "Find train tickets and rail routes for city-to-city travel and longer overland journeys.",
      h1: "Good fit for point-to-point transport searches",
      h2: "Useful for intercity travel planning",
      h3: "Fast redirect to the relevant booking category"
    },
    "china": {
      from: "Beijing",
      to: "Shanghai",
      title: "Trains",
      copy: "Search China high-speed rail routes for major city-to-city journeys and fast intercity travel.",
      h1: "Strong fit for high-speed rail planning",
      h2: "Useful for major city routes across China",
      h3: "Fast redirect to the relevant train booking category"
    },
    "europe": {
      from: "London",
      to: "Paris",
      title: "Trains",
      copy: "Compare European train routes for cross-border trips, city connections, and rail-first itineraries.",
      h1: "Useful for international rail planning",
      h2: "Better for cross-border city routes",
      h3: "Fast redirect to the relevant booking category"
    },
    "taiwan": {
      from: "Taipei",
      to: "ZuoYing",
      title: "Trains",
      copy: "Compare Taiwan train options for fast north-to-south routes and city-to-city travel.",
      h1: "Good for Taiwan High Speed Rail planning",
      h2: "Useful for longer city-to-city journeys",
      h3: "Fast redirect to the relevant booking category"
    },
    "others": {
      from: "",
      to: "",
      title: "Trains",
      copy: "Explore other rail markets when your trip does not fit the main train regions shown above.",
      h1: "Useful for regional train searches",
      h2: "Better when your route is outside the main presets",
      h3: "Still keeps the booking flow category-first"
    }
  };

  var CONTENT_MAP = {
    "trains": {
      title: "Trains",
      copy: "Find train tickets and rail routes for city-to-city travel and longer overland journeys.",
      h1: "Good fit for point-to-point transport searches",
      h2: "Useful for intercity travel planning",
      h3: "Fast redirect to the relevant booking category"
    },
    "rail-passes": {
      title: "Rail passes",
      copy: "Compare rail pass options for multi-city trips, broader rail access, and more flexible itineraries.",
      h1: "Better for multiple train journeys",
      h2: "Useful for longer regional or country-level trips",
      h3: "Helps compare pass-first rail planning"
    },
    "car-rentals": {
      title: "Car rentals",
      copy: "Search car rental options when you need more flexibility beyond central city transport.",
      h1: "Good for road trips and flexible routing",
      h2: "Useful for airport pick-up and wider-area travel",
      h3: "Better fit when transit coverage is limited"
    },
    "airport-transfers": {
      title: "Airport transfers",
      copy: "Book airport transfer options for smoother arrivals, hotel drop-offs, and departure planning.",
      h1: "Strong fit for arrival and departure logistics",
      h2: "Useful after long-haul or late-night flights",
      h3: "Helps simplify airport-to-city transport planning"
    },
    "metro-passes": {
      title: "Metro passes & cards",
      copy: "Check metro cards and transit passes for getting around the city once you arrive.",
      h1: "Good for local city movement",
      h2: "Useful after airport arrival or hotel check-in",
      h3: "Better fit for public transit planning inside the city"
    }
  };

  var DEFAULTS = {
    initialTab: "trains",
    initialTrainMarket: "japan",
    defaultDepartureOffsetDays: 30,
    storageKey: "tg_transport_search_context",
    boundAttr: "data-transport-bound"
  };

  /* ==========================================================================
     3) Generic helpers
     ========================================================================== */

  function safeArray(nodeList) {
    return nodeList ? nodeList : [];
  }

  function hasClass(el, className) {
    if (!el || !className) return false;
    if (el.classList && el.classList.contains) return el.classList.contains(className);
    return new RegExp("(^|\\s)" + className + "(\\s|$)").test(el.className || "");
  }

  function toggleClass(el, className, shouldAdd) {
    if (!el || !className) return;
    if (el.classList && el.classList.toggle) {
      el.classList.toggle(className, !!shouldAdd);
      return;
    }

    var exists = hasClass(el, className);
    if (shouldAdd && !exists) {
      el.className = trimStr((el.className || "") + " " + className);
    } else if (!shouldAdd && exists) {
      el.className = trimStr((el.className || "").replace(new RegExp("(^|\\s)" + className + "(?=\\s|$)", "g"), " "));
    }
  }

  function text(el, value) {
    if (!el) return;
    el.textContent = value == null ? "" : String(value);
  }

  function safeFocus(el) {
    try {
      if (el && el.focus) el.focus();
    } catch (_) {}
  }

  function show(el) {
    if (!el) return;
    el.hidden = false;
  }

  function hide(el) {
    if (!el) return;
    el.hidden = true;
  }

  function isFunction(fn) {
    return typeof fn === "function";
  }

  /* ==========================================================================
     4) Date helpers
     ========================================================================== */

  function pad2(n) {
    n = Number(n);
    return n < 10 ? "0" + n : "" + n;
  }

  function addDaysISO(days) {
    var d = new Date();
    d.setDate(d.getDate() + Number(days || 0));
    return d.getFullYear() + "-" + pad2(d.getMonth() + 1) + "-" + pad2(d.getDate());
  }

  function parseDateOnly(dateStr) {
    var parts = String(dateStr || "").split("-");
    if (parts.length !== 3) return null;
    return new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));
  }

  function formatPrettyDate(dateStr) {
    var d = parseDateOnly(dateStr);
    var months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    if (!d || isNaN(d.getTime())) return "Choose date";
    return d.getDate() + " " + months[d.getMonth()] + " " + d.getFullYear();
  }

  function monthLabel(year, month) {
    var months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    return months[month] + " " + year;
  }

  function daysInMonth(year, month) {
    return new Date(year, month + 1, 0).getDate();
  }

  function dateISO(d) {
    return d.getFullYear() + "-" + pad2(d.getMonth() + 1) + "-" + pad2(d.getDate());
  }

  function compareISO(a, b) {
    if (a < b) return -1;
    if (a > b) return 1;
    return 0;
  }

  function todayISO() {
    var now = new Date();
    return dateISO(new Date(now.getFullYear(), now.getMonth(), now.getDate()));
  }

  /* ==========================================================================
     5) DOM registry
     ========================================================================== */

  function getTransportElements() {
    return {
      form: DOC.getElementById("transport-search-form"),

      tabs: safeArray(DOC.querySelectorAll(".transport-tab")),
      trainMarkets: safeArray(DOC.querySelectorAll(".transport-subtab")),
      popularRoutes: safeArray(DOC.querySelectorAll(".transport-route-chip")),
      departureStations: safeArray(DOC.querySelectorAll(".transport-station-chip")),

      activeTabInput: DOC.getElementById("transport-active-tab"),
      activeLinkInput: DOC.getElementById("transport-active-link"),

      panel: DOC.getElementById("transport-panel"),
      panelTitle: DOC.getElementById("transport-panel-title"),
      panelCopy: DOC.getElementById("transport-panel-copy"),
      highlight1: DOC.getElementById("transport-highlight-1"),
      highlight2: DOC.getElementById("transport-highlight-2"),
      highlight3: DOC.getElementById("transport-highlight-3"),
      errorBox: DOC.getElementById("transport-search-error"),

      destination: DOC.getElementById("transport-destination"),
      departure: DOC.getElementById("transport-start-date"),
      travelers: DOC.getElementById("transport-travelers"),

      trainFrom: DOC.getElementById("transport-train-from"),
      trainTo: DOC.getElementById("transport-train-to"),
      trainSwap: DOC.getElementById("transport-train-swap"),

      dateDisplay: DOC.getElementById("transport-date-display"),
      dateDisplayValue: DOC.getElementById("transport-date-display-value"),
      datePopover: DOC.getElementById("transport-date-popover"),
      datePrev: DOC.getElementById("transport-date-prev"),
      dateNext: DOC.getElementById("transport-date-next"),
      dateApply: DOC.getElementById("transport-date-apply"),
      dateCancel: DOC.getElementById("transport-date-cancel"),
      dateNote: DOC.getElementById("transport-date-note"),
      calLeft: DOC.getElementById("transport-cal-left"),
      calRight: DOC.getElementById("transport-cal-right"),
      calTitleLeft: DOC.getElementById("transport-cal-title-left"),
      calTitleRight: DOC.getElementById("transport-cal-title-right")
    };
  }

  /* ==========================================================================
     6) State factory
     ========================================================================== */

  function createTransportState(els) {
    var initialDate = els.departure && els.departure.value
      ? els.departure.value
      : addDaysISO(DEFAULTS.defaultDepartureOffsetDays);

    var base = parseDateOnly(initialDate) || new Date();

    return {
      viewYear: base.getFullYear(),
      viewMonth: base.getMonth(),
      draftDate: initialDate,
      appliedDate: initialDate
    };
  }

  /* ==========================================================================
     7) UI helpers
     ========================================================================== */

  function setDateDisplay(els, dateStr) {
    if (els.dateDisplayValue) {
      text(els.dateDisplayValue, formatPrettyDate(dateStr));
    }

    if (els.dateNote) {
      text(
        els.dateNote,
        dateStr ? ("Selected: " + formatPrettyDate(dateStr)) : "Choose a departure date"
      );
    }
  }

  function updatePanelContent(els, map) {
    if (!map) return;
    text(els.panelTitle, map.title);
    text(els.panelCopy, map.copy);
    text(els.highlight1, map.h1);
    text(els.highlight2, map.h2);
    text(els.highlight3, map.h3);
  }

  function clearError(els) {
    if (els.errorBox) text(els.errorBox, "");
  }

  function showError(els, message) {
    if (els.errorBox) text(els.errorBox, message || "");
  }

  function setActiveTab(els, state, tabKey, tabEl) {
    var map = CONTENT_MAP[tabKey];
    var link = tabEl ? (getAttr(tabEl, "data-transport-link") || "") : "";
    var i, isActive;

    if (!map || !link) return;

    if (els.activeTabInput) els.activeTabInput.value = tabKey;
    if (els.activeLinkInput) els.activeLinkInput.value = link;
    if (els.panel && tabEl && tabEl.id) els.panel.setAttribute("aria-labelledby", tabEl.id);

    for (i = 0; i < els.tabs.length; i++) {
      isActive = els.tabs[i] === tabEl;
      toggleClass(els.tabs[i], "is-active", isActive);
      els.tabs[i].setAttribute("aria-selected", isActive ? "true" : "false");
    }

    updatePanelContent(els, map);
  }

  function setActiveTrainMarket(els, state, key, btn) {
    var map = TRAIN_MARKET_MAP[key];
    var i;

    if (!map) return;

    for (i = 0; i < els.trainMarkets.length; i++) {
      toggleClass(els.trainMarkets[i], "is-active", els.trainMarkets[i] === btn);
    }

    if (els.trainFrom && typeof map.from === "string") els.trainFrom.value = map.from;
    if (els.trainTo && typeof map.to === "string") els.trainTo.value = map.to;

    updatePanelContent(els, map);
  }

  /* ==========================================================================
     8) Calendar logic
     ========================================================================== */

  function renderMonth(container, titleEl, state, year, month) {
    if (!container || !titleEl) return;

    var first = new Date(year, month, 1);
    var startWeekday = first.getDay();
    var totalDays = daysInMonth(year, month);
    var today = todayISO();
    var html = "";
    var i, d, iso, cls, disabled, selected;

    text(titleEl, monthLabel(year, month));

    for (i = 0; i < startWeekday; i++) {
      html += '<span class="transport-cal__blank" aria-hidden="true"></span>';
    }

    for (i = 1; i <= totalDays; i++) {
      d = new Date(year, month, i);
      iso = dateISO(d);
      cls = "transport-cal__day";
      disabled = compareISO(iso, today) < 0;
      selected = state.draftDate === iso;

      if (disabled) cls += " is-disabled";
      if (selected) cls += " is-selected";

      html += '<button type="button" class="' + cls + '" data-date="' + iso + '"' + (disabled ? ' disabled' : '') + '>' + i + '</button>';
    }

    container.innerHTML = html;
  }

  function renderCalendars(els, state) {
    var rightMonth = state.viewMonth + 1;
    var rightYear = state.viewYear;

    renderMonth(els.calLeft, els.calTitleLeft, state, state.viewYear, state.viewMonth);

    if (rightMonth > 11) {
      rightMonth = 0;
      rightYear += 1;
    }

    renderMonth(els.calRight, els.calTitleRight, state, rightYear, rightMonth);
  }

  function openDatePopover(els, state) {
    var base;

    if (!els.datePopover || !els.departure) return;

    if (!els.departure.value) {
      els.departure.value = addDaysISO(DEFAULTS.defaultDepartureOffsetDays);
    }

    state.appliedDate = els.departure.value;
    state.draftDate = els.departure.value;

    base = parseDateOnly(state.draftDate) || new Date();
    state.viewYear = base.getFullYear();
    state.viewMonth = base.getMonth();

    renderCalendars(els, state);
    setDateDisplay(els, state.draftDate);

    show(els.datePopover);
    if (els.dateDisplay) els.dateDisplay.setAttribute("aria-expanded", "true");
  }

  function closeDatePopover(els) {
    if (!els.datePopover) return;
    hide(els.datePopover);
    if (els.dateDisplay) els.dateDisplay.setAttribute("aria-expanded", "false");
  }

  function applyDatePopover(els, state) {
    if (!els.departure) return;

    els.departure.value = state.draftDate || state.appliedDate || els.departure.value;
    state.appliedDate = els.departure.value;

    setDateDisplay(els, els.departure.value);
    closeDatePopover(els);
  }

  function cancelDatePopover(els, state) {
    state.draftDate = state.appliedDate || (els.departure ? els.departure.value : "");
    setDateDisplay(els, state.appliedDate || (els.departure ? els.departure.value : ""));
    closeDatePopover(els);
  }

  function moveCalendarMonth(state, delta) {
    state.viewMonth += delta;

    if (state.viewMonth < 0) {
      state.viewMonth = 11;
      state.viewYear -= 1;
    } else if (state.viewMonth > 11) {
      state.viewMonth = 0;
      state.viewYear += 1;
    }
  }

  function selectDraftDate(els, state, selectedDate) {
    if (!selectedDate) return;
    state.draftDate = selectedDate;
    setDateDisplay(els, state.draftDate);
    renderCalendars(els, state);
  }

  /* ==========================================================================
     9) Data collection / validation
     ========================================================================== */

  function normalizeInputValue(value) {
    return trimStr(String(value || "").replace(/\s+/g, " "));
  }

  function collectFormData(els) {
    return {
      tab: els.activeTabInput ? els.activeTabInput.value : "",
      destination: els.destination ? normalizeInputValue(els.destination.value) : "",
      departure_date: els.departure ? els.departure.value : "",
      travelers: els.travelers ? els.travelers.value : "2",
      train_from: els.trainFrom ? normalizeInputValue(els.trainFrom.value) : "",
      train_to: els.trainTo ? normalizeInputValue(els.trainTo.value) : ""
    };
  }

  function validateTransportData(data) {
    if (data.tab === "trains") {
      if (!trimStr(data.train_from)) return "Please enter a departure station.";
      if (!trimStr(data.train_to)) return "Please enter an arrival station.";
      if (!trimStr(data.departure_date)) return "Please choose a departure date.";
      return "";
    }

    if (!trimStr(data.destination)) {
      return "Please enter a destination.";
    }

    return "";
  }

  function focusFirstInvalidField(els, data) {
    if (data.tab === "trains") {
      if (!data.train_from && els.trainFrom) {
        safeFocus(els.trainFrom);
        return;
      }
      if (!data.train_to && els.trainTo) {
        safeFocus(els.trainTo);
        return;
      }
      if (!data.departure_date && els.dateDisplay) {
        safeFocus(els.dateDisplay);
      }
      return;
    }

    if (els.destination) {
      safeFocus(els.destination);
    }
  }

  /* ==========================================================================
     10) Persistence / analytics / redirect
     ========================================================================== */

  function persistSearchContext(data) {
    try {
      if (WIN.sessionStorage) {
        WIN.sessionStorage.setItem(DEFAULTS.storageKey, JSON.stringify({
          tab: data.tab,
          destination: data.destination,
          departure_date: data.departure_date,
          travelers: data.travelers,
          train_from: data.train_from,
          train_to: data.train_to
        }));
      }
    } catch (_) {}
  }

  function trackTransportSearch(els, data) {
    if (!isFunction(WIN.getConsent) || !isFunction(WIN.gtagEvent) || !isFunction(WIN.getPageType)) {
      return;
    }

    if (WIN.getConsent() !== "granted") return;

    WIN.gtagEvent("transport_search", {
      page_type: WIN.getPageType(),
      transport_category: data.tab,
      destination: data.destination,
      departure_date: data.departure_date,
      travelers: data.travelers,
      train_from: data.train_from,
      train_to: data.train_to,
      affiliate_program: String((getAttr(els.form, "data-aff") || "klook"))
    });
  }

  function getTargetUrl(els) {
    return els.activeLinkInput ? (els.activeLinkInput.value || "") : "";
  }

  function redirectToTarget(url) {
    if (!url) return;
    WIN.location.href = url;
  }

  /* ==========================================================================
     11) Submit handler
     ========================================================================== */

  function handleTransportSubmit(e, els, state) {
    var data, error, targetUrl;

    if (e && e.preventDefault) e.preventDefault();
    else if (e) e.returnValue = false;

    clearError(els);

    data = collectFormData(els);
    error = validateTransportData(data);

    if (error) {
      showError(els, error);
      focusFirstInvalidField(els, data);
      return;
    }

    targetUrl = getTargetUrl(els);
    if (!targetUrl) return;

    persistSearchContext(data);
    trackTransportSearch(els, data);
    redirectToTarget(targetUrl);
  }

  /* ==========================================================================
     12) Event binding
     ========================================================================== */

  function bindTabEvents(els, state) {
    var i;

    for (i = 0; i < els.tabs.length; i++) {
      (function (tab) {
        on(tab, "click", function () {
          var tabKey = getAttr(tab, "data-transport-tab");
          setActiveTab(els, state, tabKey, tab);
        });
      })(els.tabs[i]);
    }
  }

  function bindTrainMarketEvents(els, state) {
    var i;

    for (i = 0; i < els.trainMarkets.length; i++) {
      (function (btn) {
        on(btn, "click", function () {
          var market = getAttr(btn, "data-train-market");
          if (market) setActiveTrainMarket(els, state, market, btn);
        });
      })(els.trainMarkets[i]);
    }
  }

  function bindPopularRouteEvents(els) {
    var i;

    for (i = 0; i < els.popularRoutes.length; i++) {
      (function (chip) {
        on(chip, "click", function () {
          if (els.trainFrom) els.trainFrom.value = getAttr(chip, "data-from") || "";
          if (els.trainTo) els.trainTo.value = getAttr(chip, "data-to") || "";
        });
      })(els.popularRoutes[i]);
    }
  }

  function bindDepartureStationEvents(els) {
    var i;

    for (i = 0; i < els.departureStations.length; i++) {
      (function (chip) {
        on(chip, "click", function () {
          if (els.trainFrom) els.trainFrom.value = getAttr(chip, "data-station") || "";
          safeFocus(els.trainTo);
        });
      })(els.departureStations[i]);
    }
  }

  function bindSwapEvent(els) {
    if (!els.trainSwap) return;

    on(els.trainSwap, "click", function () {
      var fromVal = els.trainFrom ? els.trainFrom.value : "";
      var toVal = els.trainTo ? els.trainTo.value : "";

      if (els.trainFrom) els.trainFrom.value = toVal;
      if (els.trainTo) els.trainTo.value = fromVal;
    });
  }

  function bindDateEvents(els, state) {
    if (els.dateDisplay) {
      on(els.dateDisplay, "click", function () {
        openDatePopover(els, state);
      });
    }

    if (els.datePrev) {
      on(els.datePrev, "click", function () {
        moveCalendarMonth(state, -1);
        renderCalendars(els, state);
      });
    }

    if (els.dateNext) {
      on(els.dateNext, "click", function () {
        moveCalendarMonth(state, 1);
        renderCalendars(els, state);
      });
    }

    if (els.calLeft) {
      on(els.calLeft, "click", function (e) {
        e = e || WIN.event;
        var t = e.target || e.srcElement;
        var selectedDate = getAttr(t, "data-date");
        selectDraftDate(els, state, selectedDate);
      });
    }

    if (els.calRight) {
      on(els.calRight, "click", function (e) {
        e = e || WIN.event;
        var t = e.target || e.srcElement;
        var selectedDate = getAttr(t, "data-date");
        selectDraftDate(els, state, selectedDate);
      });
    }

    if (els.dateApply) {
      on(els.dateApply, "click", function () {
        applyDatePopover(els, state);
      });
    }

    if (els.dateCancel) {
      on(els.dateCancel, "click", function () {
        cancelDatePopover(els, state);
      });
    }

    on(DOC, "click", function (e) {
      var target;

      e = e || WIN.event;
      target = e.target || e.srcElement;

      if (!els.datePopover || els.datePopover.hidden) return;
      if (els.datePopover.contains && els.datePopover.contains(target)) return;
      if (els.dateDisplay && els.dateDisplay.contains && els.dateDisplay.contains(target)) return;

      closeDatePopover(els);
    });

    on(DOC, "keydown", function (e) {
      var key;

      e = e || WIN.event;
      key = e.key || e.keyCode;

      if (!els.datePopover || els.datePopover.hidden) return;

      if (key === "Escape" || key === "Esc" || key === 27) {
        cancelDatePopover(els, state);
      }
    });
  }

  function bindSubmitEvents(els, state) {
    if (!els.form) return;

    on(els.form, "submit", function (e) {
      handleTransportSubmit(e, els, state);
    });

    on(els.form, "keydown", function (e) {
      var key, evt;

      e = e || WIN.event;
      key = e.key || e.keyCode;

      if (key === "Enter" || key === 13) {
        if (e.preventDefault) e.preventDefault();
        else e.returnValue = false;

        if (els.form.requestSubmit) {
          els.form.requestSubmit();
        } else if (els.form.submit) {
          try {
            evt = DOC.createEvent("Event");
            evt.initEvent("submit", true, true);
            els.form.dispatchEvent(evt);
          } catch (_) {
            els.form.submit();
          }
        }
      }
    });
  }

  function bindEvents(els, state) {
    bindTabEvents(els, state);
    bindTrainMarketEvents(els, state);
    bindPopularRouteEvents(els);
    bindDepartureStationEvents(els);
    bindSwapEvent(els);
    bindDateEvents(els, state);
    bindSubmitEvents(els, state);
  }

  /* ==========================================================================
     13) Initial defaults
     ========================================================================== */

  function applyInitialDefaults(els, state) {
    if (els.departure && !els.departure.value) {
      els.departure.value = addDaysISO(DEFAULTS.defaultDepartureOffsetDays);
    }

    state.appliedDate = els.departure ? els.departure.value : "";
    state.draftDate = state.appliedDate;

    setDateDisplay(els, state.appliedDate);

    if (els.tabs.length) {
      setActiveTab(els, state, DEFAULTS.initialTab, els.tabs[0]);
    }

    if (els.trainMarkets.length) {
      setActiveTrainMarket(els, state, DEFAULTS.initialTrainMarket, els.trainMarkets[0]);
    }
  }

  /* ==========================================================================
     14) Main init
     ========================================================================== */

  function initTransportSearch() {
    var els = getTransportElements();
    var state;

    if (!els.form) return;
    if (els.form.getAttribute(DEFAULTS.boundAttr) === "1") return;

    els.form.setAttribute(DEFAULTS.boundAttr, "1");

    state = createTransportState(els);

    applyInitialDefaults(els, state);
    bindEvents(els, state);
  }

  /* ==========================================================================
     15) Public export
     ========================================================================== */

  WIN.initTransportSearch = initTransportSearch;

  /* ==========================================================================
     16) Optional auto-init
     ========================================================================== */

  // Uncomment if you want transport.js to self-init on DOM ready
  // instead of being called explicitly from site.js.
  //
  // on(DOC, "DOMContentLoaded", function () {
  //   initTransportSearch();
  // });

})(window, document);
