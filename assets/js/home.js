/* ==========================================================================
   TripGuidely home.js
   - Home-only hero tabs (Hotels / Flights / Transport / eSIM)
   - Trip.com-inspired flights widget behavior
   - Safe with existing site.js home hotel search
   - Old-browser friendly
   - Accessible tab behavior
   - Validation + affiliate redirect for Flights and eSIM
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

  function todayDate() {
    var d = new Date();
    return new Date(d.getFullYear(), d.getMonth(), d.getDate());
  }

  function dateToISO(d) {
    return d.getFullYear() + "-" + pad2(d.getMonth() + 1) + "-" + pad2(d.getDate());
  }

  function todayISO() {
    return dateToISO(todayDate());
  }

  function addDaysDate(date, days) {
    var d = new Date(date.getFullYear(), date.getMonth(), date.getDate());
    d.setDate(d.getDate() + Number(days || 0));
    return d;
  }

  function addDaysISO(days) {
    return dateToISO(addDaysDate(todayDate(), Number(days || 0)));
  }

  function nextDayISO(iso) {
    var d = parseISODate(iso);
    if (!d) return addDaysISO(1);
    d.setDate(d.getDate() + 1);
    return dateToISO(d);
  }

  function parseISODate(iso) {
    var parts = String(iso || "").split("-");
    if (parts.length !== 3) return null;

    var y = Number(parts[0]);
    var m = Number(parts[1]) - 1;
    var d = Number(parts[2]);

    var date = new Date(y, m, d);
    if (isNaN(date.getTime())) return null;
    if (date.getFullYear() !== y || date.getMonth() !== m || date.getDate() !== d) return null;

    return new Date(date.getFullYear(), date.getMonth(), date.getDate());
  }

  function sameDate(a, b) {
    return !!a && !!b &&
      a.getFullYear() === b.getFullYear() &&
      a.getMonth() === b.getMonth() &&
      a.getDate() === b.getDate();
  }

  function compareDates(a, b) {
    if (!a || !b) return 0;
    var at = new Date(a.getFullYear(), a.getMonth(), a.getDate()).getTime();
    var bt = new Date(b.getFullYear(), b.getMonth(), b.getDate()).getTime();
    if (at < bt) return -1;
    if (at > bt) return 1;
    return 0;
  }

  function formatShortDate(date) {
    if (!date) return "";
    try {
      return date.toLocaleDateString("en-US", {
        weekday: "short",
        month: "short",
        day: "numeric"
      });
    } catch (_) {
      return dateToISO(date);
    }
  }

  function formatMonthYear(date) {
    if (!date) return "";
    try {
      return date.toLocaleDateString("en-US", {
        month: "long",
        year: "numeric"
      });
    } catch (_) {
      return "";
    }
  }

  function formatMonthShort(date) {
    if (!date) return "";
    try {
      return date.toLocaleDateString("en-US", {
        month: "short"
      });
    } catch (_) {
      return "";
    }
  }

  function setText(el, value) {
    if (el) el.textContent = String(value || "");
  }

  function hasClass(el, cls) {
    if (!el) return false;
    if (el.classList) return el.classList.contains(cls);
    return new RegExp("(^|\\s)" + cls + "(\\s|$)").test(el.className);
  }

  function addClass(el, cls) {
    if (!el) return;
    if (el.classList) el.classList.add(cls);
    else if (!hasClass(el, cls)) el.className += (el.className ? " " : "") + cls;
  }

  function removeClass(el, cls) {
    if (!el) return;
    if (el.classList) el.classList.remove(cls);
    else el.className = String(el.className || "")
      .replace(new RegExp("(^|\\s)" + cls + "(\\s|$)", "g"), " ")
      .replace(/\s+/g, " ")
      .replace(/^\s+|\s+$/g, "");
  }

  function toggleClass(el, cls, active) {
    if (active) addClass(el, cls);
    else removeClass(el, cls);
  }

  function tryTrack(eventName, params) {
    try {
      if (typeof WIN.gtag === "function") {
        WIN.gtag("event", eventName, params || {});
      }
    } catch (_) {}
  }

  function openUrl(url) {
    if (!url) return;
    try {
      WIN.location.href = url;
    } catch (_) {
      try {
        WIN.location.assign(url);
      } catch (__) {}
    }
  }

  function buildAffiliateUrl(base, subid, extraParams) {
    var cleanBase = trimStr(base);
    var cleanSubid = trimStr(subid);
    var key;

    if (!cleanBase) return "";

    try {
      var url = new URL(cleanBase, WIN.location.href);

      if (cleanSubid && !url.searchParams.get("subid")) {
        url.searchParams.set("subid", cleanSubid);
      }

      if (extraParams) {
        for (key in extraParams) {
          if (Object.prototype.hasOwnProperty.call(extraParams, key)) {
            if (trimStr(extraParams[key])) {
              url.searchParams.set(key, trimStr(extraParams[key]));
            }
          }
        }
      }

      return url.toString();
    } catch (_) {
      var out = cleanBase;
      var sep = out.indexOf("?") === -1 ? "?" : "&";

      if (cleanSubid && !/[?&]subid=/.test(out)) {
        out += sep + "subid=" + encodeURIComponent(cleanSubid);
        sep = "&";
      }

      if (extraParams) {
        for (key in extraParams) {
          if (Object.prototype.hasOwnProperty.call(extraParams, key) && trimStr(extraParams[key])) {
            out += sep + encodeURIComponent(key) + "=" + encodeURIComponent(trimStr(extraParams[key]));
            sep = "&";
          }
        }
      }

      return out;
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
          try { tab.focus(); } catch (_) {}
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

    var submitBtn = DOC.getElementById("home-flight-search-submit");

    var tripTypeReturn = form.querySelector('input[name="flight_trip_type"][value="return"], #home-flight-trip-return');
    var tripTypeOneWay = form.querySelector('input[name="flight_trip_type"][value="one-way"], #home-flight-trip-oneway');
    var tripTypeMulti = form.querySelector('input[name="flight_trip_type"][value="multi-city"], #home-flight-trip-multicity');
    var directOnly = form.querySelector('input[name="flight_direct_only"], #home-flight-direct-only');

    var swapBtn = form.querySelector(".flight-swap, [data-flight-swap]");
    var plusHotelBtn = form.querySelector(".flight-plus-hotel");

    var dateTrigger = form.querySelector(".flight-date-trigger, [data-flight-date-trigger]");
    var datePopover = form.querySelector(".flight-date-popover, [data-flight-date-popover]");
    var dateConfirm = form.querySelector(".flight-date-confirm, [data-flight-date-confirm]");
    var departLabel = form.querySelector("[data-flight-depart-label]");
    var returnLabel = form.querySelector("[data-flight-return-label]");
    var dateSummary = form.querySelector("[data-flight-date-summary]");
    var dateModeDepart = form.querySelector("[data-flight-date-mode='depart']");
    var dateModeReturn = form.querySelector("[data-flight-date-mode='return']");
    var calendarsWrap = form.querySelector(".flight-cal-wrap, [data-flight-cal-wrap]");
    var monthChipsWrap = form.querySelector(".flight-date-monthchips");
    var monthChipButtons = monthChipsWrap ? $all("button", monthChipsWrap) : [];
    var dateTitle = form.querySelector(".flight-date-title, .flight-date-head h3");
    var dateNote = form.querySelector(".flight-date-note");

    var travelersTrigger = form.querySelector(".flight-travelers-trigger, .flight-box--travelers, [data-flight-travelers-trigger]");
    var travelersPopover = form.querySelector(".flight-travelers-popover, [data-flight-travelers-popover]");
    var travelersApply = form.querySelector(".flight-travelers-apply, [data-flight-travelers-apply]");
    var travelersText = form.querySelector("[data-flight-travelers-text]");
    var cabinSelect = form.querySelector(".flight-cabin select, [data-flight-cabin]");
    var passengersField = form.querySelector('input[name="passengers"]');

    var minDate = todayISO();
    departure.min = minDate;
    ret.min = addDaysISO(1);

    if (!departure.value) departure.value = addDaysISO(14);
    if (!ret.value) ret.value = addDaysISO(21);

    var visibleMonth = new Date(todayDate().getFullYear(), todayDate().getMonth(), 1);
    var dateSelectionMode = "depart";

    function getTripType() {
      if (tripTypeOneWay && tripTypeOneWay.checked) return "one-way";
      if (tripTypeMulti && tripTypeMulti.checked) return "multi-city";
      return "return";
    }

    function isOneWay() {
      return getTripType() === "one-way";
    }

    function getCounterValue(key, fallback) {
      var row = travelersPopover ? travelersPopover.querySelector('[data-counter="' + key + '"]') : null;
      if (!row) return fallback;

      var output = row.querySelector("output");
      var hidden = row.querySelector('input[type="hidden"]');
      var value = hidden ? Number(hidden.value) : Number(output ? (output.value || output.textContent) : fallback);

      if (isNaN(value)) value = fallback;
      return value;
    }

    function getTravelerTotals() {
      return {
        adults: getCounterValue("adults", 1),
        children: getCounterValue("children", 0),
        infants: getCounterValue("infants", 0)
      };
    }

    function getTravelerTotalCount() {
      var counts = getTravelerTotals();
      return counts.adults + counts.children + counts.infants;
    }

    function updatePassengersHidden() {
      if (!passengersField) return;
      passengersField.value = String(getTravelerTotalCount());
    }

    function ensureVisibleMonthContainsSelected() {
      var depDate = parseISODate(trimStr(departure.value));
      var retDate = parseISODate(trimStr(ret.value));
      var anchor = dateSelectionMode === "return" && retDate ? retDate : depDate;

      if (!anchor) return;

      var month1 = new Date(visibleMonth.getFullYear(), visibleMonth.getMonth(), 1);
      var month2 = new Date(visibleMonth.getFullYear(), visibleMonth.getMonth() + 1, 1);
      var anchorMonth = new Date(anchor.getFullYear(), anchor.getMonth(), 1);

      if (!sameDate(month1, anchorMonth) && !sameDate(month2, anchorMonth)) {
        visibleMonth = anchorMonth;
      }
    }

    function updateReturnState() {
      var oneWay = isOneWay();
      var returnWrap = ret.closest ? ret.closest(".hotel-field, .flight-box-wrap, .flight-box, .flight-date-col") : null;

      if (oneWay) {
        ret.disabled = true;
        if (returnWrap) addClass(returnWrap, "is-disabled");
      } else {
        ret.disabled = false;
        if (returnWrap) removeClass(returnWrap, "is-disabled");
      }

      if (submitBtn) {
        submitBtn.setAttribute("data-trip-type", getTripType());
      }

      if (dateModeReturn) {
        dateModeReturn.disabled = oneWay;
        dateModeReturn.setAttribute("aria-disabled", oneWay ? "true" : "false");
      }

      if (oneWay && dateSelectionMode === "return") {
        dateSelectionMode = "depart";
      }

      updateDateDisplay();
      updateDateModeUi();
    }

    function updateMinDates() {
      var dep = trimStr(departure.value);
      if (!dep) {
        ret.min = addDaysISO(1);
        return;
      }

      ret.min = nextDayISO(dep);

      if (!isOneWay() && trimStr(ret.value) && ret.value <= dep) {
        ret.value = nextDayISO(dep);
      }
    }

    function updateDateDisplay() {
      var depDate = parseISODate(trimStr(departure.value));
      var retDate = parseISODate(trimStr(ret.value));

      if (departLabel) setText(departLabel, depDate ? formatShortDate(depDate) : "Select");
      if (returnLabel) setText(returnLabel, isOneWay() ? "One-way" : (retDate ? formatShortDate(retDate) : "Select"));

      if (dateSummary) {
        if (depDate && !isOneWay() && retDate) {
          setText(dateSummary, formatShortDate(depDate) + " — " + formatShortDate(retDate));
        } else if (depDate) {
          setText(dateSummary, formatShortDate(depDate));
        } else {
          setText(dateSummary, "");
        }
      }

      if (dateTitle) {
        if (isOneWay()) setText(dateTitle, "Select departure date");
        else if (dateSelectionMode === "return") setText(dateTitle, "Select return date");
        else setText(dateTitle, "Select departure date");
      }

      if (dateNote) {
        if (isOneWay()) setText(dateNote, "All dates are in local time");
        else if (retDate) setText(dateNote, "Return: " + formatShortDate(retDate));
        else setText(dateNote, "All dates are in local time");
      }
    }

    function updateMonthChips() {
      if (!monthChipButtons || !monthChipButtons.length) return;

      var month1 = new Date(visibleMonth.getFullYear(), visibleMonth.getMonth(), 1);
      var month2 = new Date(visibleMonth.getFullYear(), visibleMonth.getMonth() + 1, 1);
      var months = [month1, month2];
      var i, btn, targetMonth;

      for (i = 0; i < monthChipButtons.length; i++) {
        btn = monthChipButtons[i];
        targetMonth = months[i] || months[months.length - 1];

        if (!targetMonth) continue;

        setText(btn, formatMonthShort(targetMonth));
        btn.setAttribute("data-month-index", String(i));
        btn.setAttribute("data-month-iso", dateToISO(targetMonth));
        btn.disabled = false;
        toggleClass(btn, "active", i === 0);
      }
    }

    function closeFloatingPanels(except) {
      if (datePopover && datePopover !== except) {
        datePopover.setAttribute("hidden", "");
        if (dateTrigger) {
          removeClass(dateTrigger, "is-open");
          dateTrigger.setAttribute("aria-expanded", "false");
        }
      }
      if (travelersPopover && travelersPopover !== except) {
        travelersPopover.setAttribute("hidden", "");
        if (travelersTrigger) {
          removeClass(travelersTrigger, "is-open");
          travelersTrigger.setAttribute("aria-expanded", "false");
        }
      }
    }

    function togglePanel(trigger, panel) {
      if (!trigger || !panel) return;

      var isHidden = panel.hasAttribute("hidden");
      closeFloatingPanels(panel);

      if (isHidden) {
        panel.removeAttribute("hidden");
        addClass(trigger, "is-open");
        trigger.setAttribute("aria-expanded", "true");
      } else {
        panel.setAttribute("hidden", "");
        removeClass(trigger, "is-open");
        trigger.setAttribute("aria-expanded", "false");
      }
    }

    function focusFirstAvailableDay() {
      if (!datePopover || datePopover.hasAttribute("hidden")) return;
      var target = datePopover.querySelector(".flight-day.start, .flight-day.end, .flight-day.single, .flight-day:not(.muted):not(.disabled)");
      if (!target) return;
      try { target.focus(); } catch (_) {}
    }

    function buildDayButton(dateObj, selectedStart, selectedEnd) {
      var btn = DOC.createElement("button");
      var isPast = dateObj < todayDate();
      var isWeekendDay = dateObj.getDay() === 0 || dateObj.getDay() === 6;
      var inRange = selectedStart && selectedEnd && compareDates(dateObj, selectedStart) > 0 && compareDates(dateObj, selectedEnd) < 0;
      var isStart = sameDate(dateObj, selectedStart);
      var isEnd = sameDate(dateObj, selectedEnd);

      btn.type = "button";
      btn.className = "flight-day";
      btn.setAttribute("data-date", dateToISO(dateObj));
      btn.setAttribute("aria-label", formatShortDate(dateObj));
      btn.innerHTML = "<span>" + dateObj.getDate() + "</span>";

      if (isWeekendDay && !isPast) addClass(btn, "weekend");
      if (inRange) addClass(btn, "range");

      if (isStart && isEnd) {
        addClass(btn, "single");
      } else {
        if (isStart) addClass(btn, "start");
        if (isEnd) addClass(btn, "end");
      }

      if (isPast) {
        addClass(btn, "disabled");
        btn.disabled = true;
      }

      on(btn, "click", function () {
        if (btn.disabled) return;

        var clickedISO = btn.getAttribute("data-date");

        if (dateSelectionMode === "depart") {
          departure.value = clickedISO;

          if (!isOneWay()) {
            if (!trimStr(ret.value) || trimStr(ret.value) <= clickedISO) {
              ret.value = nextDayISO(clickedISO);
            }
            dateSelectionMode = "return";
          }

          updateMinDates();
          updateDateDisplay();
          renderCalendars();

          if (!isOneWay()) {
            WIN.setTimeout(function () {
              focusFirstAvailableDay();
            }, 0);
          }
        } else {
          if (!isOneWay()) {
            if (clickedISO <= trimStr(departure.value)) {
              departure.value = clickedISO;
              ret.value = nextDayISO(clickedISO);
            } else {
              ret.value = clickedISO;
            }
          }

          updateMinDates();
          updateDateDisplay();
          renderCalendars();

          if (!isOneWay() && dateConfirm) {
            WIN.setTimeout(function () {
              try { dateConfirm.focus(); } catch (_) {}
            }, 0);
          }
        }
      });

      on(btn, "keydown", function (e) {
        e = e || WIN.event;
        var key = e.key || e.keyCode;
        var buttons = calendarsWrap ? $all(".flight-day:not(.muted):not(.disabled)", calendarsWrap) : [];
        var idx = -1;
        var nextIdx = -1;
        var i;

        for (i = 0; i < buttons.length; i++) {
          if (buttons[i] === btn) {
            idx = i;
            break;
          }
        }

        if (idx === -1) return;

        if (key === "ArrowRight" || key === 39) nextIdx = idx + 1;
        else if (key === "ArrowLeft" || key === 37) nextIdx = idx - 1;
        else if (key === "ArrowDown" || key === 40) nextIdx = idx + 7;
        else if (key === "ArrowUp" || key === 38) nextIdx = idx - 7;
        else return;

        if (e.preventDefault) e.preventDefault();
        else e.returnValue = false;

        if (nextIdx >= 0 && nextIdx < buttons.length) {
          try { buttons[nextIdx].focus(); } catch (_) {}
        }
      });

      return btn;
    }

    function buildCalendar(monthDate, allowPrev, allowNext) {
      var cal = DOC.createElement("div");
      cal.className = "flight-cal";

      var head = DOC.createElement("div");
      head.className = "flight-cal-head";

      var title = DOC.createElement("div");
      title.className = "flight-cal-title";
      setText(title, formatMonthYear(monthDate));

      var navWrap = DOC.createElement("div");

      if (allowPrev) {
        var prev = DOC.createElement("button");
        prev.type = "button";
        prev.className = "flight-cal-nav";
        prev.setAttribute("aria-label", "Previous month");
        prev.innerHTML = "‹";
        on(prev, "click", function () {
          visibleMonth = new Date(visibleMonth.getFullYear(), visibleMonth.getMonth() - 1, 1);
          renderCalendars();
          focusFirstAvailableDay();
        });
        navWrap.appendChild(prev);
      }

      if (allowNext) {
        var next = DOC.createElement("button");
        next.type = "button";
        next.className = "flight-cal-nav";
        next.setAttribute("aria-label", "Next month");
        next.innerHTML = "›";
        on(next, "click", function () {
          visibleMonth = new Date(visibleMonth.getFullYear(), visibleMonth.getMonth() + 1, 1);
          renderCalendars();
          focusFirstAvailableDay();
        });
        navWrap.appendChild(next);
      }

      head.appendChild(title);
      head.appendChild(navWrap);

      var weekdays = DOC.createElement("div");
      weekdays.className = "flight-weekdays";

      var weekdayNames = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
      var i;
      for (i = 0; i < weekdayNames.length; i++) {
        var wd = DOC.createElement("span");
        setText(wd, weekdayNames[i]);
        weekdays.appendChild(wd);
      }

      var days = DOC.createElement("div");
      days.className = "flight-days";

      var firstDay = new Date(monthDate.getFullYear(), monthDate.getMonth(), 1);
      var lastDay = new Date(monthDate.getFullYear(), monthDate.getMonth() + 1, 0);
      var lead = firstDay.getDay();

      for (i = 0; i < lead; i++) {
        var filler = DOC.createElement("button");
        filler.type = "button";
        filler.className = "flight-day muted";
        filler.disabled = true;
        filler.tabIndex = -1;
        filler.innerHTML = "<span></span>";
        days.appendChild(filler);
      }

      var selectedStart = parseISODate(trimStr(departure.value));
      var selectedEnd = isOneWay() ? null : parseISODate(trimStr(ret.value));
      var dayNum;

      for (dayNum = 1; dayNum <= lastDay.getDate(); dayNum++) {
        days.appendChild(
          buildDayButton(
            new Date(monthDate.getFullYear(), monthDate.getMonth(), dayNum),
            selectedStart,
            selectedEnd
          )
        );
      }

      cal.appendChild(head);
      cal.appendChild(weekdays);
      cal.appendChild(days);

      return cal;
    }

    function renderCalendars() {
      if (!calendarsWrap) return;

      ensureVisibleMonthContainsSelected();
      calendarsWrap.innerHTML = "";

      var month1 = new Date(visibleMonth.getFullYear(), visibleMonth.getMonth(), 1);
      var month2 = new Date(visibleMonth.getFullYear(), visibleMonth.getMonth() + 1, 1);

      calendarsWrap.appendChild(buildCalendar(month1, true, false));
      calendarsWrap.appendChild(buildCalendar(month2, false, true));

      updateDateDisplay();
      updateDateModeUi();
      updateMonthChips();
    }

    function updateDateModeUi() {
      if (dateModeDepart) {
        if (dateSelectionMode === "depart") addClass(dateModeDepart, "active");
        else removeClass(dateModeDepart, "active");
        dateModeDepart.setAttribute("aria-pressed", dateSelectionMode === "depart" ? "true" : "false");
      }

      if (dateModeReturn) {
        if (dateSelectionMode === "return" && !isOneWay()) addClass(dateModeReturn, "active");
        else removeClass(dateModeReturn, "active");
        dateModeReturn.setAttribute("aria-pressed", dateSelectionMode === "return" && !isOneWay() ? "true" : "false");
      }
    }

    function setCounterValue(row, nextValue) {
      if (!row) return;

      var min = Number(row.getAttribute("data-min"));
      var max = Number(row.getAttribute("data-max"));
      var output = row.querySelector("output");
      var hidden = row.querySelector('input[type="hidden"]');

      if (isNaN(min)) min = 0;
      if (isNaN(max)) max = 9;
      if (isNaN(nextValue)) nextValue = min;

      nextValue = Math.max(min, Math.min(max, nextValue));

      if (output) {
        output.value = String(nextValue);
        output.textContent = String(nextValue);
      }
      if (hidden) hidden.value = String(nextValue);

      updateTravelersSummary();
    }

    function updateTravelersSummary() {
      if (!travelersText) return;

      var counts = getTravelerTotals();
      var total = counts.adults + counts.children + counts.infants;
      var cabin = cabinSelect ? trimStr(cabinSelect.value) : "Economy";

      if (!cabin) cabin = "Economy";
      setText(travelersText, total + " " + (total > 1 ? "adults" : "adult") + " · " + cabin);
      updatePassengersHidden();
    }

    function initTravelersCounters() {
      if (!travelersPopover) {
        updatePassengersHidden();
        return;
      }

      var counters = $all("[data-counter]", travelersPopover);
      var i;

      for (i = 0; i < counters.length; i++) {
        (function (row) {
          var minus = row.querySelector("[data-minus]");
          var plus = row.querySelector("[data-plus]");
          var hidden = row.querySelector('input[type="hidden"]');
          var initial = hidden ? Number(hidden.value) : Number(row.getAttribute("data-min"));

          if (isNaN(initial)) initial = 0;
          setCounterValue(row, initial);

          on(minus, "click", function () {
            setCounterValue(row, getCounterValue(row.getAttribute("data-counter"), 0) - 1);
          });

          on(plus, "click", function () {
            setCounterValue(row, getCounterValue(row.getAttribute("data-counter"), 0) + 1);
          });
        })(counters[i]);
      }

      on(cabinSelect, "change", updateTravelersSummary);

      on(travelersApply, "click", function () {
        updateTravelersSummary();
        travelersPopover.setAttribute("hidden", "");
        if (travelersTrigger) {
          removeClass(travelersTrigger, "is-open");
          travelersTrigger.setAttribute("aria-expanded", "false");
        }
      });

      updateTravelersSummary();
    }

    function validate(data) {
      if (!trimStr(data.from)) return "Please enter a departure city or airport.";
      if (!trimStr(data.to)) return "Please enter a destination city or airport.";
      if (!trimStr(data.departure)) return "Please choose a departure date.";
      if (data.tripType !== "one-way" && !trimStr(data.returnDate)) return "Please choose a return date.";
      if (data.tripType !== "one-way" && trimStr(data.returnDate) && data.returnDate <= data.departure) {
        return "Return date must be after departure date.";
      }
      return "";
    }

    function buildFlightAffiliateUrl(data) {
      var counts = getTravelerTotals();
      var totalPassengers = counts.adults + counts.children + counts.infants;
      var cabin = cabinSelect ? trimStr(cabinSelect.value) : "Economy";

      var params = {
        origin: data.from,
        destination: data.to,
        departure: data.departure,
        return: data.tripType === "one-way" ? "" : data.returnDate,
        trip_type: data.tripType,
        direct: data.directOnly ? "1" : "",
        adults: String(counts.adults),
        children: counts.children ? String(counts.children) : "",
        infants: counts.infants ? String(counts.infants) : "",
        passengers: String(totalPassengers),
        cabin: cabin
      };

      return buildAffiliateUrl(
        form.getAttribute("data-affiliate-base"),
        form.getAttribute("data-subid"),
        params
      );
    }

    function goFlightHotel() {
      var url = buildAffiliateUrl(
        form.getAttribute("data-affiliate-base"),
        "tg_home_flights_hotel",
        {
          origin: trimStr(from.value),
          destination: trimStr(to.value),
          departure: trimStr(departure.value),
          return: isOneWay() ? "" : trimStr(ret.value),
          trip_type: getTripType()
        }
      );

      tryTrack("flight_hotel_click", {
        page_type: "home",
        affiliate_program: "kiwi"
      });

      openUrl(url);
    }

    on(departure, "change", function () {
      updateMinDates();
      updateDateDisplay();
      renderCalendars();
    });

    on(ret, "change", function () {
      updateDateDisplay();
      renderCalendars();
    });

    on(tripTypeReturn, "change", function () {
      updateReturnState();
      updateMinDates();
      renderCalendars();
    });

    on(tripTypeOneWay, "change", function () {
      updateReturnState();
      renderCalendars();
    });

    on(tripTypeMulti, "change", function () {
      updateReturnState();
      renderCalendars();
    });

    on(swapBtn, "click", function () {
      var a = from.value;
      var b = to.value;
      from.value = b;
      to.value = a;
    });

    on(plusHotelBtn, "click", function (e) {
      if (e && e.preventDefault) e.preventDefault();
      else if (e) e.returnValue = false;
      goFlightHotel();
    });

    on(dateTrigger, "click", function (e) {
      if (e && e.preventDefault) e.preventDefault();
      if (e && e.stopPropagation) e.stopPropagation();

      togglePanel(dateTrigger, datePopover);

      if (datePopover && !datePopover.hasAttribute("hidden")) {
        ensureVisibleMonthContainsSelected();
        renderCalendars();
        WIN.setTimeout(function () {
          focusFirstAvailableDay();
        }, 0);
      }
    });

    on(dateModeDepart, "click", function () {
      dateSelectionMode = "depart";
      updateDateDisplay();
      updateDateModeUi();
      renderCalendars();
      focusFirstAvailableDay();
    });

    on(dateModeReturn, "click", function () {
      if (!isOneWay()) {
        dateSelectionMode = "return";
        updateDateDisplay();
        updateDateModeUi();
        renderCalendars();
        focusFirstAvailableDay();
      }
    });

    if (monthChipButtons && monthChipButtons.length) {
      var m;
      for (m = 0; m < monthChipButtons.length; m++) {
        on(monthChipButtons[m], "click", function () {
          var monthIso = this.getAttribute("data-month-iso");
          var monthDate = parseISODate(monthIso);
          if (!monthDate) return;
          visibleMonth = new Date(monthDate.getFullYear(), monthDate.getMonth(), 1);
          renderCalendars();
          focusFirstAvailableDay();
        });
      }
    }

    on(dateConfirm, "click", function () {
      if (datePopover) datePopover.setAttribute("hidden", "");
      if (dateTrigger) {
        removeClass(dateTrigger, "is-open");
        dateTrigger.setAttribute("aria-expanded", "false");
        try { dateTrigger.focus(); } catch (_) {}
      }
      updateDateDisplay();
    });

    on(travelersTrigger, "click", function (e) {
      if (e && e.preventDefault) e.preventDefault();
      if (e && e.stopPropagation) e.stopPropagation();
      togglePanel(travelersTrigger, travelersPopover);
    });

    on(datePopover, "click", function (e) {
      if (e && e.stopPropagation) e.stopPropagation();
    });

    on(travelersPopover, "click", function (e) {
      if (e && e.stopPropagation) e.stopPropagation();
    });

    on(DOC, "click", function (e) {
      var target = e.target || e.srcElement;

      if (datePopover && !datePopover.hasAttribute("hidden")) {
        if (!(datePopover.contains && datePopover.contains(target)) &&
            target !== dateTrigger &&
            !(dateTrigger && dateTrigger.contains && dateTrigger.contains(target))) {
          datePopover.setAttribute("hidden", "");
          if (dateTrigger) {
            removeClass(dateTrigger, "is-open");
            dateTrigger.setAttribute("aria-expanded", "false");
          }
        }
      }

      if (travelersPopover && !travelersPopover.hasAttribute("hidden")) {
        if (!(travelersPopover.contains && travelersPopover.contains(target)) &&
            target !== travelersTrigger &&
            !(travelersTrigger && travelersTrigger.contains && travelersTrigger.contains(target))) {
          travelersPopover.setAttribute("hidden", "");
          if (travelersTrigger) {
            removeClass(travelersTrigger, "is-open");
            travelersTrigger.setAttribute("aria-expanded", "false");
          }
        }
      }
    });

    on(DOC, "keydown", function (e) {
      e = e || WIN.event;
      var key = e.key || e.keyCode;

      if (key === "Escape" || key === 27) {
        closeFloatingPanels(null);
        return;
      }

      if ((key === "Enter" || key === 13) && dateTrigger && DOC.activeElement === dateTrigger) {
        if (e.preventDefault) e.preventDefault();
        else e.returnValue = false;
        togglePanel(dateTrigger, datePopover);
        if (datePopover && !datePopover.hasAttribute("hidden")) {
          ensureVisibleMonthContainsSelected();
          renderCalendars();
          focusFirstAvailableDay();
        }
      }
    });

    initTravelersCounters();
    updateMinDates();
    updateReturnState();
    updateDateDisplay();
    updatePassengersHidden();

    if (dateTrigger) dateTrigger.setAttribute("aria-expanded", "false");
    if (travelersTrigger) travelersTrigger.setAttribute("aria-expanded", "false");

    if (calendarsWrap) {
      renderCalendars();
    } else {
      if (datePopover) datePopover.setAttribute("hidden", "");
    }

    if (travelersPopover) {
      travelersPopover.setAttribute("hidden", "");
    }

    on(form, "submit", function (e) {
      var targetUrl, error;
      var data = {
        from: trimStr(from.value),
        to: trimStr(to.value),
        departure: trimStr(departure.value),
        returnDate: trimStr(ret.value),
        tripType: getTripType(),
        directOnly: !!(directOnly && directOnly.checked)
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
      updatePassengersHidden();

      targetUrl = buildFlightAffiliateUrl(data);

      tryTrack("flight_search", {
        page_type: "home",
        affiliate_program: "kiwi",
        origin: data.from,
        destination: data.to,
        trip_type: data.tripType,
        direct_only: data.directOnly ? "true" : "false",
        passengers: String(getTravelerTotalCount())
      });

      openUrl(targetUrl);
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
        try { destination.focus(); } catch (_) {}
        return;
      }

      setText(errorBox, "");

      targetUrl = buildAffiliateUrl(
        form.getAttribute("data-affiliate-base"),
        form.getAttribute("data-subid"),
        {
          destination: cleanDestination,
          duration: trimStr(duration.value),
          usage: trimStr(usage.value)
        }
      );

      tryTrack("esim_search", {
        page_type: "home",
        affiliate_program: "airalo",
        destination: cleanDestination,
        trip_length: trimStr(duration.value),
        data_usage: trimStr(usage.value)
      });

      openUrl(targetUrl);
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
