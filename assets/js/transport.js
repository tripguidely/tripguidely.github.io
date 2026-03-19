/* ==========================================================================
   /assets/js/transport.js
   TripGuidely — transport.js
   Purpose:
   - Real tab switching for the transport widget
   - Syncs active tab, panel copy, highlights, placeholders, and affiliate link
   - Uses the CURRENT HTML structure you pasted
   - Safe for older browsers
   ========================================================================== */

(function (WIN, DOC) {
  "use strict";

  if (!WIN || !DOC) return;

  var DEFAULTS = {
    initialTab: "trains",
    initialTrainMarket: "japan",
    storageKey: "tg_transport_search_context",
    boundAttr: "data-transport-bound",
    defaultDepartureOffsetDays: 30
  };

  var HERO_IMAGES = {
    "trains": "/assets/images/hero/transport/transport-trains-1600x900.webp",
    "rail-passes": "/assets/images/hero/transport/transport-rail-passes-1600x900.webp",
    "car-rentals": "/assets/images/hero/transport/transport-car-rentals-1600x900.webp",
    "airport-transfers": "/assets/images/hero/transport/transport-airport-transfers-1600x900.webp",
    "metro-passes": "/assets/images/hero/transport/transport-metro-passes-1600x900.webp"
  };

  var TAB_CONFIG = {
    "trains": {
      title: "Trains",
      copy: "Find train tickets and rail routes for city-to-city travel and longer overland journeys.",
      h1: "Good fit for point-to-point transport searches",
      h2: "Useful for intercity travel planning",
      h3: "Fast redirect to the relevant booking category",
      destinationLabel: "Route or destination",
      destinationPlaceholder: "Tokyo, Osaka, Paris, London",
      travelersLabel: "Travelers",
      travelersVisible: true,
      dateVisible: true,
      subtabs: [
        {
          key: "japan",
          label: "Japan trains",
          title: "Trains",
          copy: "Compare Japan train routes for major city-to-city journeys and faster intercity travel.",
          h1: "Strong fit for Japan rail planning",
          h2: "Useful for major city routes like Tokyo and Osaka",
          h3: "Fast redirect to the relevant train booking category",
          destinationPlaceholder: "Tokyo, Osaka, Kyoto, Hiroshima"
        },
        {
          key: "china",
          label: "China High Speed Rail",
          title: "Trains",
          copy: "Search China high-speed rail routes for major city-to-city journeys and fast intercity transport.",
          h1: "Strong fit for high-speed rail planning",
          h2: "Useful for major city routes across China",
          h3: "Fast redirect to the relevant train booking category",
          destinationPlaceholder: "Beijing, Shanghai, Guangzhou, Shenzhen"
        },
        {
          key: "europe",
          label: "Europe trains",
          title: "Trains",
          copy: "Compare European train routes for cross-border trips, city connections, and rail-first itineraries.",
          h1: "Useful for international rail planning",
          h2: "Better for cross-border city routes",
          h3: "Fast redirect to the relevant booking category",
          destinationPlaceholder: "Paris, London, Rome, Amsterdam"
        },
        {
          key: "others",
          label: "Others",
          title: "Trains",
          copy: "Explore other rail markets when your trip does not fit the main regions shown above.",
          h1: "Useful for regional train searches",
          h2: "Better when your route is outside the main presets",
          h3: "Still keeps the booking flow category-first",
          destinationPlaceholder: "Enter city, route, or region"
        }
      ]
    },

    "rail-passes": {
      title: "Rail passes",
      copy: "Compare rail pass options for multi-city trips, broader rail access, and more flexible itineraries.",
      h1: "Better for multiple train journeys",
      h2: "Useful for longer regional or country-level trips",
      h3: "Helps compare pass-first rail planning",
      destinationLabel: "Destination or region",
      destinationPlaceholder: "Tokyo, Kyoto, Osaka",
      travelersLabel: "Travelers",
      travelersVisible: false,
      dateVisible: false,
      subtabs: [
        {
          key: "japan",
          label: "Japan rail passes",
          title: "Rail passes",
          copy: "Compare Japan rail pass options for multi-city train travel and broader rail access.",
          h1: "Best for multi-city Japan rail trips",
          h2: "Useful when you expect several train journeys",
          h3: "Helps compare pass-first rail planning",
          destinationPlaceholder: "Tokyo, Kyoto, Osaka"
        },
        {
          key: "europe",
          label: "Europe rail passes",
          title: "Rail passes",
          copy: "Compare Europe rail pass options for broader country or cross-border train access.",
          h1: "Useful for wider regional rail access",
          h2: "Good for flexible multi-city itineraries",
          h3: "Best when point-to-point tickets are not enough",
          destinationPlaceholder: "Paris, Rome, Berlin, Madrid"
        },
        {
          key: "others",
          label: "Other rail passes",
          title: "Rail passes",
          copy: "Explore other pass-based rail options when your trip falls outside the main pass markets.",
          h1: "Useful for broader rail access",
          h2: "Good for flexible itineraries",
          h3: "Best when you need more than a single route",
          destinationPlaceholder: "Enter city, region, or country"
        }
      ]
    },

    "car-rentals": {
      title: "Car rentals",
      copy: "Search car rental options when you need more flexibility beyond central city transport.",
      h1: "Good for road trips and flexible routing",
      h2: "Useful for airport pick-up and wider-area travel",
      h3: "Better fit when transit coverage is limited",
      destinationLabel: "Pick-up & drop-off location",
      destinationPlaceholder: "Tokyo, Paris, Rome, Los Angeles",
      travelersLabel: "Driver age",
      travelersVisible: true,
      dateVisible: true,
      travelerOptions: [
        { value: "18-24", label: "18–24" },
        { value: "25-29", label: "25–29" },
        { value: "30-65", label: "Between 30–65" },
        { value: "66+", label: "66+" }
      ],
      subtabs: []
    },

    "airport-transfers": {
      title: "Airport transfers",
      copy: "Book airport transfer options for smoother arrivals, hotel drop-offs, and departure planning.",
      h1: "Strong fit for arrival and departure logistics",
      h2: "Useful after long-haul or late-night flights",
      h3: "Helps simplify airport-to-city transport planning",
      destinationLabel: "Airport, hotel, or destination",
      destinationPlaceholder: "Narita Airport, Shinjuku hotel, Charles de Gaulle",
      travelersLabel: "Passengers",
      travelersVisible: true,
      dateVisible: true,
      travelerOptions: [
        { value: "1", label: "1 passenger" },
        { value: "2", label: "2 passengers" },
        { value: "3", label: "3 passengers" },
        { value: "4", label: "4 passengers" },
        { value: "5", label: "5 passengers" },
        { value: "6+", label: "6+ passengers" }
      ],
      subtabs: []
    },

    "metro-passes": {
      title: "Metro passes & cards",
      copy: "Check metro cards and transit passes for getting around the city once you arrive.",
      h1: "Good for local city movement",
      h2: "Useful after airport arrival or hotel check-in",
      h3: "Better fit for public transit planning inside the city",
      destinationLabel: "City",
      destinationPlaceholder: "Tokyo, Seoul, Hong Kong, Singapore",
      travelersLabel: "Travelers",
      travelersVisible: false,
      dateVisible: false,
      subtabs: [
        {
          key: "japan",
          label: "Japan",
          title: "Metro passes & cards",
          copy: "Explore metro cards and local transit options for major cities across Japan.",
          h1: "Useful for urban transit planning",
          h2: "Good after airport arrival or hotel check-in",
          h3: "Better fit for city movement planning",
          destinationPlaceholder: "Tokyo, Osaka, Kyoto"
        },
        {
          key: "europe",
          label: "Europe",
          title: "Metro passes & cards",
          copy: "Compare city transit cards and urban transport options for major European cities.",
          h1: "Good for local city movement",
          h2: "Useful after arrival in major European capitals",
          h3: "Better fit for public transit planning inside the city",
          destinationPlaceholder: "Paris, London, Rome, Barcelona"
        },
        {
          key: "asia",
          label: "Asia",
          title: "Metro passes & cards",
          copy: "Compare transit cards and local metro access across major Asian cities.",
          h1: "Useful for big-city transport systems",
          h2: "Better when metro is your main urban transport",
          h3: "Good for city movement after arrival",
          destinationPlaceholder: "Seoul, Hong Kong, Singapore, Taipei"
        },
        {
          key: "others",
          label: "Others",
          title: "Metro passes & cards",
          copy: "Explore metro passes and city transit cards outside the main presets.",
          h1: "Useful for local city movement",
          h2: "Good for public transport planning",
          h3: "Best when you need a city-first transit pass",
          destinationPlaceholder: "Enter city name"
        }
      ]
    }
  };

  function trimStr(str) {
    return String(str || "").replace(/^\s+|\s+$/g, "");
  }

  function getAttr(el, name) {
    if (!el || !name || !el.getAttribute) return "";
    return el.getAttribute(name) || "";
  }

  function on(el, eventName, handler) {
    if (!el || !eventName || !handler) return;
    if (el.addEventListener) {
      el.addEventListener(eventName, handler, false);
    } else if (el.attachEvent) {
      el.attachEvent("on" + eventName, handler);
    }
  }

  function safeArray(nodeList) {
    return nodeList || [];
  }

  function hasClass(el, className) {
    if (!el || !className) return false;
    if (el.classList && el.classList.contains) return el.classList.contains(className);
    return new RegExp("(^|\\s)" + className + "(\\s|$)").test(el.className || "");
  }

  function addClass(el, className) {
    if (!el || !className) return;
    if (el.classList && el.classList.add) {
      el.classList.add(className);
      return;
    }
    if (!hasClass(el, className)) {
      el.className = trimStr((el.className || "") + " " + className);
    }
  }

  function removeClass(el, className) {
    if (!el || !className) return;
    if (el.classList && el.classList.remove) {
      el.classList.remove(className);
      return;
    }
    el.className = trimStr((el.className || "").replace(new RegExp("(^|\\s)" + className + "(?=\\s|$)", "g"), " "));
  }

  function toggleClass(el, className, shouldAdd) {
    if (shouldAdd) addClass(el, className);
    else removeClass(el, className);
  }

  function text(el, value) {
    if (!el) return;
    el.textContent = value == null ? "" : String(value);
  }

  function show(el) {
    if (!el) return;
    el.hidden = false;
    el.style.display = "";
  }

  function hide(el) {
    if (!el) return;
    el.hidden = true;
    el.style.display = "none";
  }

  function pad2(n) {
    n = Number(n);
    return n < 10 ? "0" + n : "" + n;
  }

  function addDaysISO(days) {
    var d = new Date();
    d.setDate(d.getDate() + Number(days || 0));
    return d.getFullYear() + "-" + pad2(d.getMonth() + 1) + "-" + pad2(d.getDate());
  }

  function getTransportElements() {
    return {
      form: DOC.getElementById("transport-search-form"),
      searchWrap: DOC.getElementById("transport-search"),
      tabs: safeArray(DOC.querySelectorAll(".transport-tab[data-transport-tab]")),
      subtabsWrap: DOC.querySelector(".transport-subtabs"),
      subtabs: safeArray(DOC.querySelectorAll(".transport-subtab")),
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
      heroImage: DOC.querySelector(".hero-bg img"),
      destinationField: DOC.querySelector('label[for="transport-destination"]'),
      departureField: DOC.querySelector('label[for="transport-start-date"]'),
      travelersField: DOC.querySelector('label[for="transport-travelers"]')
    };
  }

  function createState() {
    return {
      activeTab: DEFAULTS.initialTab,
      activeSubtab: DEFAULTS.initialTrainMarket
    };
  }

  function clearError(els) {
    if (els.errorBox) text(els.errorBox, "");
  }

  function showError(els, message) {
    if (els.errorBox) text(els.errorBox, message || "");
  }

  function setOptions(selectEl, options, selectedValue) {
    var i;
    var html = "";

    if (!selectEl || !options || !options.length) return;

    for (i = 0; i < options.length; i++) {
      html += '<option value="' + options[i].value + '"' + (String(options[i].value) === String(selectedValue) ? ' selected' : '') + '>' + options[i].label + '</option>';
    }

    selectEl.innerHTML = html;
  }

  function setPanelContent(els, map) {
    if (!map) return;
    text(els.panelTitle, map.title);
    text(els.panelCopy, map.copy);
    text(els.highlight1, map.h1);
    text(els.highlight2, map.h2);
    text(els.highlight3, map.h3);
  }

  function setHeroImage(els, tabKey) {
    var src = HERO_IMAGES[tabKey];

    if (!els.heroImage || !src) return;

    if (els.heroImage.getAttribute("src") !== src) {
      els.heroImage.setAttribute("src", src);
    }
  }

  function getSubtabConfig(tabKey, subtabKey) {
    var config = TAB_CONFIG[tabKey];
    var subtabs;
    var i;

    if (!config || !config.subtabs || !config.subtabs.length) return null;

    subtabs = config.subtabs;
    for (i = 0; i < subtabs.length; i++) {
      if (subtabs[i].key === subtabKey) return subtabs[i];
    }

    return subtabs[0];
  }

  function renderSubtabs(els, state, tabKey) {
    var config = TAB_CONFIG[tabKey];
    var i;
    var html = "";
    var items;
    var activeKey;

    if (!els.subtabsWrap) return;

    if (!config || !config.subtabs || !config.subtabs.length) {
      els.subtabsWrap.innerHTML = "";
      hide(els.subtabsWrap);
      return;
    }

    items = config.subtabs;
    activeKey = state.activeSubtab;

    if (!getSubtabConfig(tabKey, activeKey)) {
      activeKey = items[0].key;
      state.activeSubtab = activeKey;
    }

    for (i = 0; i < items.length; i++) {
      html += '<button type="button" class="transport-subtab' + (items[i].key === activeKey ? ' is-active' : '') + '" data-transport-subtab="' + items[i].key + '">';
      html += '<span class="transport-subtab__dot" aria-hidden="true"></span>';
      html += items[i].label;
      html += "</button>";
    }

    els.subtabsWrap.innerHTML = html;
    show(els.subtabsWrap);
    els.subtabs = safeArray(DOC.querySelectorAll(".transport-subtab"));
  }

  function updateFieldLabels(els, config, subtabConfig) {
    var finalPlaceholder = subtabConfig && subtabConfig.destinationPlaceholder
      ? subtabConfig.destinationPlaceholder
      : config.destinationPlaceholder;

    if (els.destinationField) {
      text(els.destinationField.querySelector(".transport-field__label"), config.destinationLabel || "Destination");
    }

    if (els.destination) {
      els.destination.setAttribute("placeholder", finalPlaceholder || "Enter destination");
    }

    if (els.travelersField) {
      text(els.travelersField.querySelector(".transport-field__label"), config.travelersLabel || "Travelers");
    }
  }

  function updateFieldVisibility(els, config) {
    if (!els.departureField || !els.travelersField) return;

    if (config.dateVisible === false) hide(els.departureField);
    else show(els.departureField);

    if (config.travelersVisible === false) hide(els.travelersField);
    else show(els.travelersField);
  }

  function updateTravelerOptions(els, config) {
    if (!els.travelers) return;

    if (config.travelerOptions && config.travelerOptions.length) {
      setOptions(els.travelers, config.travelerOptions, config.travelerOptions[0].value);
      return;
    }

    setOptions(els.travelers, [
      { value: "1", label: "1 traveler" },
      { value: "2", label: "2 travelers" },
      { value: "3", label: "3 travelers" },
      { value: "4", label: "4 travelers" },
      { value: "5", label: "5 travelers" },
      { value: "6", label: "6+ travelers" }
    ], "2");
  }

  function syncTabClasses(els, activeTabEl) {
    var i;
    var isActive;

    for (i = 0; i < els.tabs.length; i++) {
      isActive = els.tabs[i] === activeTabEl;
      toggleClass(els.tabs[i], "is-active", isActive);
      els.tabs[i].setAttribute("aria-selected", isActive ? "true" : "false");
      els.tabs[i].setAttribute("tabindex", isActive ? "0" : "-1");
    }
  }

  function setActiveTab(els, state, tabKey, tabEl) {
    var config = TAB_CONFIG[tabKey];
    var link = tabEl ? getAttr(tabEl, "data-transport-link") : "";
    var subtabConfig;

    if (!config) return;

    state.activeTab = tabKey;

    if (config.subtabs && config.subtabs.length) {
      if (!getSubtabConfig(tabKey, state.activeSubtab)) {
        state.activeSubtab = config.subtabs[0].key;
      }
    } else {
      state.activeSubtab = "";
    }

    if (els.activeTabInput) els.activeTabInput.value = tabKey;
    if (els.activeLinkInput) els.activeLinkInput.value = link || "";
    if (els.panel && tabEl && tabEl.id) els.panel.setAttribute("aria-labelledby", tabEl.id);

    DOC.body.setAttribute("data-transport-active", tabKey);

    syncTabClasses(els, tabEl);
    renderSubtabs(els, state, tabKey);

    subtabConfig = getSubtabConfig(tabKey, state.activeSubtab);

    setPanelContent(els, subtabConfig || config);
    updateFieldLabels(els, config, subtabConfig);
    updateFieldVisibility(els, config);
    updateTravelerOptions(els, config);
    setHeroImage(els, tabKey);
    clearError(els);
  }

  function setActiveSubtab(els, state, subtabKey, subtabEl) {
    var config = TAB_CONFIG[state.activeTab];
    var subtabConfig = getSubtabConfig(state.activeTab, subtabKey);
    var i;

    if (!config || !subtabConfig) return;

    state.activeSubtab = subtabKey;

    for (i = 0; i < els.subtabs.length; i++) {
      toggleClass(els.subtabs[i], "is-active", els.subtabs[i] === subtabEl);
    }

    setPanelContent(els, subtabConfig);
    updateFieldLabels(els, config, subtabConfig);
    clearError(els);
  }

  function normalizeInputValue(value) {
    return trimStr(String(value || "").replace(/\s+/g, " "));
  }

  function collectFormData(els) {
    return {
      tab: els.activeTabInput ? els.activeTabInput.value : "",
      subtab: DOC.body.getAttribute("data-transport-active-subtab") || "",
      destination: els.destination ? normalizeInputValue(els.destination.value) : "",
      departure_date: els.departure ? els.departure.value : "",
      travelers: els.travelers ? els.travelers.value : ""
    };
  }

  function validateTransportData(els, data) {
    var tabConfig = TAB_CONFIG[data.tab];

    if (!trimStr(data.destination)) {
      return "Please enter a destination.";
    }

    if (tabConfig && tabConfig.dateVisible !== false && !trimStr(data.departure_date)) {
      return "Please choose a departure date.";
    }

    return "";
  }

  function persistSearchContext(data) {
    try {
      if (WIN.sessionStorage) {
        WIN.sessionStorage.setItem(DEFAULTS.storageKey, JSON.stringify(data));
      }
    } catch (_) {}
  }

  function trackTransportSearch(els, data) {
    if (typeof WIN.getConsent !== "function") return;
    if (typeof WIN.gtagEvent !== "function") return;
    if (typeof WIN.getPageType !== "function") return;
    if (WIN.getConsent() !== "granted") return;

    WIN.gtagEvent("transport_search", {
      page_type: WIN.getPageType(),
      transport_category: data.tab,
      destination: data.destination,
      departure_date: data.departure_date,
      travelers: data.travelers,
      affiliate_program: String(getAttr(els.form, "data-aff") || "klook")
    });
  }

  function redirectToTarget(url) {
    if (!url) return;
    WIN.location.href = url;
  }

  function handleTransportSubmit(e, els) {
    var data;
    var error;
    var targetUrl;

    if (e && e.preventDefault) e.preventDefault();
    else if (e) e.returnValue = false;

    clearError(els);

    data = collectFormData(els);
    error = validateTransportData(els, data);

    if (error) {
      showError(els, error);
      return;
    }

    targetUrl = els.activeLinkInput ? els.activeLinkInput.value : "";
    if (!targetUrl) return;

    persistSearchContext(data);
    trackTransportSearch(els, data);
    redirectToTarget(targetUrl);
  }

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

  function bindSubtabEvents(els, state) {
    if (!els.subtabsWrap) return;

    on(els.subtabsWrap, "click", function (e) {
      var target = e.target || e.srcElement;
      var btn = target;

      while (btn && btn !== els.subtabsWrap && !hasClass(btn, "transport-subtab")) {
        btn = btn.parentNode;
      }

      if (!btn || btn === els.subtabsWrap) return;

      setActiveSubtab(els, state, getAttr(btn, "data-transport-subtab"), btn);
      DOC.body.setAttribute("data-transport-active-subtab", getAttr(btn, "data-transport-subtab") || "");
    });
  }

  function bindSubmitEvents(els) {
    if (!els.form) return;

    on(els.form, "submit", function (e) {
      handleTransportSubmit(e, els);
    });
  }

  function applyInitialDefaults(els, state) {
    var firstTab;

    if (els.departure && !els.departure.value) {
      els.departure.value = addDaysISO(DEFAULTS.defaultDepartureOffsetDays);
    }

    firstTab = DOC.getElementById("transport-tab-" + DEFAULTS.initialTab) || (els.tabs.length ? els.tabs[0] : null);
    if (firstTab) {
      setActiveTab(els, state, DEFAULTS.initialTab, firstTab);
    }
  }

  function initTransportSearch() {
    var els = getTransportElements();
    var state;

    if (!els.form) return;
    if (els.form.getAttribute(DEFAULTS.boundAttr) === "1") return;

    els.form.setAttribute(DEFAULTS.boundAttr, "1");

    state = createState();

    applyInitialDefaults(els, state);
    bindTabEvents(els, state);
    bindSubtabEvents(els, state);
    bindSubmitEvents(els);
  }

  WIN.initTransportSearch = initTransportSearch;

})(window, document);
