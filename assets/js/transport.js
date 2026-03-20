/* ==========================================================================
   /assets/js/transport.js
   TripGuidely — transport.js
   - Keeps Trains / Rail passes / Car rentals / Airport transfers as form tabs
   - Uses Klook-style region buttons for Airport trains & buses / Ferries /
     Cruises / Metro passes & cards
   - Opens "..." on hover / focus / click
   - Keeps overflow tab visually active for overflow categories
   - Redirects every form submit and region click to the correct affiliate link
   - Switches hero image by active tab
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
    defaultDepartureOffsetDays: 30,
    moreCloseDelay: 180
  };

  var HERO_IMAGES = {
    "trains": "/assets/images/hero/transport/transport-trains-1600x900.webp",
    "rail-passes": "/assets/images/hero/transport/transport-rail-passes-1600x900.webp",
    "car-rentals": "/assets/images/hero/transport/transport-car-rentals-1600x900.webp",
    "airport-transfers": "/assets/images/hero/transport/transport-airport-transfers-1600x900.webp",
    "airport-trains-buses": "/assets/images/hero/transport/transport-airport-trains-buses-1600x900.webp",
    "ferries": "/assets/images/hero/transport/transport-ferries-1600x900.webp",
    "cruises": "/assets/images/hero/transport/transport-cruises-1600x900.webp",
    "metro-passes": "/assets/images/hero/transport/transport-metro-passes-1600x900.webp"
  };

  var TAB_CONFIG = {
    "trains": {
      title: "Trains",
      link: "https://klook.tpk.ro/LQXw15L2",
      subid: "tg_transport_trains",
      useRegionGrid: false,
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
      link: "https://klook.tpk.ro/X7Ksor1o",
      subid: "tg_transport_rail_passes",
      useRegionGrid: false,
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
      link: "https://klook.tpk.ro/5t8ofxGh",
      subid: "tg_transport_car_rentals",
      useRegionGrid: false,
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
      link: "https://klook.tpk.ro/iB78IJzo",
      subid: "tg_transport_airport_transfers",
      useRegionGrid: false,
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

    "airport-trains-buses": {
      title: "Airport trains & buses",
      link: "https://klook.tpk.ro/VByndotO",
      subid: "tg_transport_airport_trains_buses",
      useRegionGrid: true,
      gridCols: 4,
      copy: "Compare airport-to-city trains and bus links for lower-cost arrivals and practical public transport planning.",
      h1: "Better for airport-to-city public transport",
      h2: "Useful when you want a lower-cost arrival option",
      h3: "Good fit for train and bus airport connections",
      regions: [
        "Japan",
        "Europe",
        "Hong Kong & Macau",
        "South Korea",
        "Singapore",
        "Taiwan",
        "Thailand",
        "Malaysia",
        "Indonesia",
        "United States",
        "Mainland China",
        "UAE",
        "Australia & New Zealand",
        "Philippines",
        "Vietnam",
        "Others"
      ],
      subtabs: []
    },

    "ferries": {
      title: "Ferries",
      link: "https://klook.tpk.ro/h975PijE",
      subid: "tg_transport_ferries",
      useRegionGrid: true,
      gridCols: 4,
      copy: "Compare ferry routes for island crossings, port-to-port journeys, and coastal transport planning.",
      h1: "Useful for island and port-to-port routes",
      h2: "Good for coastal crossings and practical sea transport",
      h3: "Best when your route depends on a ferry connection",
      regions: [
        "Hong Kong & Macau",
        "South Korea",
        "Singapore",
        "Taiwan",
        "Thailand",
        "Malaysia",
        "Indonesia",
        "United States",
        "Mainland China",
        "Australia & New Zealand",
        "Philippines",
        "Vietnam"
      ],
      subtabs: []
    },

    "cruises": {
      title: "Cruises",
      link: "https://klook.tpk.ro/z6Hs7Grs",
      subid: "tg_transport_cruises",
      useRegionGrid: true,
      gridCols: 3,
      copy: "Explore cruise options by region when you want itinerary-based travel rather than point-to-point transport.",
      h1: "Best for itinerary-first travel planning",
      h2: "Useful for region-based cruise discovery",
      h3: "Good when the journey is part of the experience",
      regions: [
        "Asia",
        "Australia & New Zealand",
        "Nordic"
      ],
      subtabs: []
    },

    "metro-passes": {
      title: "Metro passes & cards",
      link: "https://klook.tpk.ro/OoM3hbHE",
      subid: "tg_transport_metro_passes",
      useRegionGrid: true,
      gridCols: 4,
      copy: "Check metro cards and transit passes for getting around the city once you arrive.",
      h1: "Good for local city movement",
      h2: "Useful after airport arrival or hotel check-in",
      h3: "Better fit for public transit planning inside the city",
      regions: [
        "Japan",
        "Europe",
        "South Korea",
        "Taiwan",
        "Hong Kong & Macau",
        "Thailand",
        "Singapore",
        "Malaysia",
        "Mainland China"
      ],
      subtabs: []
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
    if (el.addEventListener) el.addEventListener(eventName, handler, false);
    else if (el.attachEvent) el.attachEvent("on" + eventName, handler);
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

  function slugify(str) {
    return trimStr(str || "")
      .toLowerCase()
      .replace(/&/g, "and")
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");
  }

  function containsNode(parent, child) {
    if (!parent || !child) return false;
    if (parent.contains) return parent.contains(child);
    while (child) {
      if (child === parent) return true;
      child = child.parentNode;
    }
    return false;
  }

  function getRelatedTarget(e) {
    if (!e) return null;
    return e.relatedTarget || e.toElement || e.fromElement || null;
  }

  function isLeavingContainer(container, e) {
    var related = getRelatedTarget(e);
    return !containsNode(container, related);
  }

  function getTransportElements() {
    return {
      form: DOC.getElementById("transport-search-form"),
      searchWrap: DOC.getElementById("transport-search"),
      tabs: safeArray(DOC.querySelectorAll(".transport-tab[data-transport-tab]")),
      subtabsWrap: DOC.querySelector(".transport-subtabs"),
      subtabs: safeArray(DOC.querySelectorAll(".transport-subtab")),
      searchGrid: DOC.getElementById("transport-search-grid"),
      regionGrid: DOC.getElementById("transport-region-grid"),
      regionButtons: [],
      activeTabInput: DOC.getElementById("transport-active-tab"),
      activeLinkInput: DOC.getElementById("transport-active-link"),
      activeSubidInput: DOC.getElementById("transport-active-subid"),
      activeRegionInput: DOC.getElementById("transport-active-region"),
      activeRegionLabelInput: DOC.getElementById("transport-active-region-label"),
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
      travelersField: DOC.querySelector('label[for="transport-travelers"]'),
      submitBtn: DOC.querySelector("#transport-search-form .transport-submit"),
      moreWrap: DOC.getElementById("transport-more"),
      moreToggle: DOC.getElementById("transport-more-toggle"),
      moreMenu: DOC.getElementById("transport-more-menu"),
      overflowActiveTab: DOC.getElementById("transport-tab-overflow-active"),
      moreItems: safeArray(DOC.querySelectorAll(".transport-more__item"))
    };
  }

  function createState() {
    return {
      activeTab: DEFAULTS.initialTab,
      activeSubtab: DEFAULTS.initialTrainMarket,
      activeRegion: "",
      activeRegionLabel: "",
      moreOpen: false,
      moreCloseTimer: null
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
    text(els.panelTitle, map.title || "");
    text(els.panelCopy, map.copy || "");
    text(els.highlight1, map.h1 || "");
    text(els.highlight2, map.h2 || "");
    text(els.highlight3, map.h3 || "");
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

    if (!config || config.useRegionGrid || !config.subtabs || !config.subtabs.length) {
      els.subtabsWrap.innerHTML = "";
      hide(els.subtabsWrap);
      els.subtabs = [];
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
    els.subtabs = safeArray(els.subtabsWrap.querySelectorAll(".transport-subtab"));
  }

  function renderRegionGrid(els, state, tabKey) {
    var config = TAB_CONFIG[tabKey];
    var html = "";
    var i;
    var regions;
    var colsClass = "transport-grid--regions-4";

    if (!els.regionGrid) return;

    if (!config || !config.useRegionGrid || !config.regions || !config.regions.length) {
      els.regionGrid.innerHTML = "";
      hide(els.regionGrid);
      els.regionButtons = [];
      return;
    }

    if (Number(config.gridCols) === 3) colsClass = "transport-grid--regions-3";

    els.regionGrid.className = "transport-grid transport-grid--klook transport-grid--regions " + colsClass;

    regions = config.regions;
    for (i = 0; i < regions.length; i++) {
      html += '<button type="button" class="transport-region-btn" data-transport-region="' + slugify(regions[i]) + '" data-transport-region-label="' + regions[i] + '">' + regions[i] + "</button>";
    }

    els.regionGrid.innerHTML = html;
    show(els.regionGrid);
    els.regionButtons = safeArray(els.regionGrid.querySelectorAll(".transport-region-btn"));

    state.activeRegion = "";
    state.activeRegionLabel = "";
    if (els.activeRegionInput) els.activeRegionInput.value = "";
    if (els.activeRegionLabelInput) els.activeRegionLabelInput.value = "";
  }

  function updateFieldLabels(els, config, subtabConfig) {
    var finalPlaceholder = subtabConfig && subtabConfig.destinationPlaceholder
      ? subtabConfig.destinationPlaceholder
      : config.destinationPlaceholder;
    var labelNode;

    if (els.destinationField) {
      labelNode = els.destinationField.querySelector(".transport-field__label");
      if (labelNode) text(labelNode, config.destinationLabel || "Destination");
    }

    if (els.destination) {
      els.destination.setAttribute("placeholder", finalPlaceholder || "Enter destination");
    }

    if (els.travelersField) {
      labelNode = els.travelersField.querySelector(".transport-field__label");
      if (labelNode) text(labelNode, config.travelersLabel || "Travelers");
    }
  }

  function updateFieldVisibility(els, config) {
    var useRegionGrid = !!(config && config.useRegionGrid);

    if (els.searchGrid) {
      if (useRegionGrid) hide(els.searchGrid);
      else show(els.searchGrid);
    }

    if (els.destinationField) {
      if (useRegionGrid) hide(els.destinationField);
      else show(els.destinationField);
    }

    if (els.departureField) {
      if (useRegionGrid || config.dateVisible === false) hide(els.departureField);
      else show(els.departureField);
    }

    if (els.travelersField) {
      if (useRegionGrid || config.travelersVisible === false) hide(els.travelersField);
      else show(els.travelersField);
    }

    if (els.submitBtn) {
      if (useRegionGrid) hide(els.submitBtn);
      else show(els.submitBtn);
    }

    if (els.destination) {
      els.destination.disabled = useRegionGrid;
      if (useRegionGrid) els.destination.value = "";
    }

    if (els.departure) {
      els.departure.disabled = useRegionGrid || config.dateVisible === false;
      if (useRegionGrid || config.dateVisible === false) els.departure.value = "";
    }

    if (els.travelers) {
      els.travelers.disabled = useRegionGrid || config.travelersVisible === false;
    }
  }

  function updateTravelerOptions(els, config) {
    if (!els.travelers || !config || config.useRegionGrid) return;

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
      { value: "6+", label: "6+ travelers" }
    ], "2");
  }

  function isOverflowTab(tabKey) {
    return tabKey === "ferries" || tabKey === "cruises" || tabKey === "metro-passes";
  }

  function setOverflowButton(els, tabKey, link, subid) {
    var item = null;
    var icon = "";
    var label = "";
    var textNode;
    var iconNode;
    var i;

    if (!els.overflowActiveTab) return;

    if (!isOverflowTab(tabKey)) {
      hide(els.overflowActiveTab);
      removeClass(els.overflowActiveTab, "is-active");
      els.overflowActiveTab.setAttribute("aria-selected", "false");
      els.overflowActiveTab.setAttribute("data-transport-tab", "");
      els.overflowActiveTab.setAttribute("data-transport-link", "");
      els.overflowActiveTab.setAttribute("data-transport-subid", "");
      return;
    }

    for (i = 0; i < els.moreItems.length; i++) {
      if (getAttr(els.moreItems[i], "data-transport-tab") === tabKey) {
        item = els.moreItems[i];
        break;
      }
    }

    label = item ? getAttr(item, "data-transport-label") : (TAB_CONFIG[tabKey] ? TAB_CONFIG[tabKey].title : "");
    icon = item ? getAttr(item, "data-transport-icon") : "";

    els.overflowActiveTab.setAttribute("data-transport-tab", tabKey);
    els.overflowActiveTab.setAttribute("data-transport-link", link || "");
    els.overflowActiveTab.setAttribute("data-transport-subid", subid || "");
    els.overflowActiveTab.setAttribute("aria-selected", "true");
    show(els.overflowActiveTab);
    addClass(els.overflowActiveTab, "is-active");

    iconNode = els.overflowActiveTab.querySelector(".transport-tab__icon");
    textNode = els.overflowActiveTab.querySelector(".transport-tab__text");

    if (iconNode) text(iconNode, icon || "•");
    if (textNode) text(textNode, label || "");
  }

  function syncMoreMenuCurrent(els, activeTab) {
    var i;
    for (i = 0; i < els.moreItems.length; i++) {
      toggleClass(els.moreItems[i], "is-current", getAttr(els.moreItems[i], "data-transport-tab") === activeTab);
    }
  }

  function syncTabClasses(els, activeTabEl, activeTabKey) {
    var i;
    var isActive;
    var key;

    for (i = 0; i < els.tabs.length; i++) {
      key = getAttr(els.tabs[i], "data-transport-tab");
      isActive = els.tabs[i] === activeTabEl && key && key === activeTabKey;

      if (els.tabs[i] === els.overflowActiveTab && !isOverflowTab(activeTabKey)) {
        isActive = false;
      }

      toggleClass(els.tabs[i], "is-active", isActive);
      els.tabs[i].setAttribute("aria-selected", isActive ? "true" : "false");
      els.tabs[i].setAttribute("tabindex", isActive ? "0" : "-1");
    }
  }

  function clearMoreCloseTimer(state) {
    if (state.moreCloseTimer) {
      WIN.clearTimeout(state.moreCloseTimer);
      state.moreCloseTimer = null;
    }
  }

  function setMenuOpen(els, state, isOpen) {
    if (!els.moreMenu || !els.moreToggle || !els.moreWrap) return;

    state.moreOpen = !!isOpen;
    els.moreToggle.setAttribute("aria-expanded", state.moreOpen ? "true" : "false");

    if (state.moreOpen) {
      addClass(els.moreWrap, "is-open");
      els.moreMenu.hidden = false;
      els.moreMenu.style.display = "block";
    } else {
      removeClass(els.moreWrap, "is-open");
      els.moreMenu.hidden = true;
      els.moreMenu.style.display = "none";
    }
  }

  function setActiveTab(els, state, tabKey, tabEl, forcedLink, forcedSubid) {
    var config = TAB_CONFIG[tabKey];
    var link = forcedLink || (tabEl ? getAttr(tabEl, "data-transport-link") : "") || (config ? config.link : "");
    var subid = forcedSubid || (tabEl ? getAttr(tabEl, "data-transport-subid") : "") || (config ? config.subid : "");
    var subtabConfig;
    var activeVisualTabEl = tabEl;

    if (!config) return;

    state.activeTab = tabKey;

    if (config.useRegionGrid) {
      state.activeSubtab = "";
    } else if (config.subtabs && config.subtabs.length) {
      if (!getSubtabConfig(tabKey, state.activeSubtab)) {
        state.activeSubtab = config.subtabs[0].key;
      }
    } else {
      state.activeSubtab = "";
    }

    state.activeRegion = "";
    state.activeRegionLabel = "";

    if (els.activeTabInput) els.activeTabInput.value = tabKey;
    if (els.activeLinkInput) els.activeLinkInput.value = link || "";
    if (els.activeSubidInput) els.activeSubidInput.value = subid || "";
    if (els.activeRegionInput) els.activeRegionInput.value = "";
    if (els.activeRegionLabelInput) els.activeRegionLabelInput.value = "";

    DOC.body.setAttribute("data-transport-active", tabKey);
    DOC.body.setAttribute("data-transport-active-subtab", state.activeSubtab || "");

    if (isOverflowTab(tabKey)) {
      setOverflowButton(els, tabKey, link, subid);
      activeVisualTabEl = els.overflowActiveTab;
    } else {
      setOverflowButton(els, "", "", "");
    }

    if (els.panel && activeVisualTabEl && activeVisualTabEl.id) {
      els.panel.setAttribute("aria-labelledby", activeVisualTabEl.id);
    }

    syncTabClasses(els, activeVisualTabEl, tabKey);
    syncMoreMenuCurrent(els, tabKey);
    renderSubtabs(els, state, tabKey);
    renderRegionGrid(els, state, tabKey);

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
    DOC.body.setAttribute("data-transport-active-subtab", subtabKey || "");

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
      travelers: els.travelers ? els.travelers.value : "",
      subid: els.activeSubidInput ? els.activeSubidInput.value : "",
      region: els.activeRegionInput ? els.activeRegionInput.value : "",
      region_label: els.activeRegionLabelInput ? els.activeRegionLabelInput.value : ""
    };
  }

  function validateTransportData(data) {
    var tabConfig = TAB_CONFIG[data.tab];

    if (!tabConfig) return "Please choose a transport category.";

    if (tabConfig.useRegionGrid) {
      if (!trimStr(data.region_label)) return "Please choose a region.";
      return "";
    }

    if (!trimStr(data.destination)) {
      return "Please enter a destination.";
    }

    if (tabConfig.dateVisible !== false && !trimStr(data.departure_date)) {
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

  function trackTransportEvent(els, data, eventName) {
    if (typeof WIN.getConsent !== "function") return;
    if (typeof WIN.gtagEvent !== "function") return;
    if (typeof WIN.getPageType !== "function") return;
    if (WIN.getConsent() !== "granted") return;

    WIN.gtagEvent(eventName || "transport_search", {
      page_type: WIN.getPageType(),
      transport_category: data.tab,
      transport_subcategory: data.subtab || "",
      transport_region: data.region || "",
      transport_region_label: data.region_label || "",
      destination: data.destination || "",
      departure_date: data.departure_date || "",
      travelers: data.travelers || "",
      affiliate_program: String(getAttr(els.form, "data-aff") || "klook"),
      affiliate_subid: data.subid || ""
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
    error = validateTransportData(data);

    if (error) {
      showError(els, error);
      return;
    }

    targetUrl = els.activeLinkInput ? els.activeLinkInput.value : "";
    if (!targetUrl) return;

    persistSearchContext(data);
    trackTransportEvent(els, data, "transport_search");
    redirectToTarget(targetUrl);
  }

  function handleRegionClick(els, state, btn) {
    var region = getAttr(btn, "data-transport-region");
    var regionLabel = getAttr(btn, "data-transport-region-label");
    var data;
    var targetUrl;

    if (!regionLabel) return;

    state.activeRegion = region || "";
    state.activeRegionLabel = regionLabel || "";

    if (els.activeRegionInput) els.activeRegionInput.value = state.activeRegion;
    if (els.activeRegionLabelInput) els.activeRegionLabelInput.value = state.activeRegionLabel;

    data = collectFormData(els);
    targetUrl = els.activeLinkInput ? els.activeLinkInput.value : "";

    if (!targetUrl) return;

    persistSearchContext(data);
    trackTransportEvent(els, data, "transport_region_click");
    redirectToTarget(targetUrl);
  }

  function bindTabEvents(els, state) {
    var i;

    for (i = 0; i < els.tabs.length; i++) {
      (function (tab) {
        on(tab, "click", function () {
          var tabKey = getAttr(tab, "data-transport-tab");
          if (!tabKey) return;
          setActiveTab(els, state, tabKey, tab);
          setMenuOpen(els, state, false);
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
    });
  }

  function bindRegionEvents(els, state) {
    if (!els.regionGrid) return;

    on(els.regionGrid, "click", function (e) {
      var target = e.target || e.srcElement;
      var btn = target;

      while (btn && btn !== els.regionGrid && !hasClass(btn, "transport-region-btn")) {
        btn = btn.parentNode;
      }

      if (!btn || btn === els.regionGrid) return;
      handleRegionClick(els, state, btn);
    });
  }

  function bindSubmitEvents(els) {
    if (!els.form) return;

    on(els.form, "submit", function (e) {
      handleTransportSubmit(e, els);
    });
  }

  function bindMoreMenuEvents(els, state) {
    var i;

    function openMenu() {
      clearMoreCloseTimer(state);
      setMenuOpen(els, state, true);
    }

    function closeMenuNow() {
      clearMoreCloseTimer(state);
      setMenuOpen(els, state, false);
    }

    function scheduleClose() {
      clearMoreCloseTimer(state);
      state.moreCloseTimer = WIN.setTimeout(function () {
        setMenuOpen(els, state, false);
      }, DEFAULTS.moreCloseDelay);
    }

    if (!els.moreWrap || !els.moreToggle || !els.moreMenu) return;

    on(els.moreWrap, "mouseover", function () {
      openMenu();
    });

    on(els.moreWrap, "mouseout", function (e) {
      if (isLeavingContainer(els.moreWrap, e)) {
        scheduleClose();
      }
    });

    on(els.moreToggle, "focus", function () {
      openMenu();
    });

    on(els.moreMenu, "focusin", function () {
      openMenu();
    });

    on(els.moreToggle, "click", function (e) {
      if (e && e.preventDefault) e.preventDefault();
      if (e && e.stopPropagation) e.stopPropagation();
      clearMoreCloseTimer(state);
      setMenuOpen(els, state, !state.moreOpen);
    });

    on(els.moreWrap, "focusin", function () {
      openMenu();
    });

    on(els.moreWrap, "focusout", function () {
      WIN.setTimeout(function () {
        var active = DOC.activeElement;
        if (!active || !containsNode(els.moreWrap, active)) {
          closeMenuNow();
        }
      }, 0);
    });

    on(DOC, "click", function (e) {
      var target = e.target || e.srcElement;
      if (!containsNode(els.moreWrap, target)) {
        closeMenuNow();
      }
    });

    for (i = 0; i < els.moreItems.length; i++) {
      (function (item) {
        on(item, "click", function (e) {
          var tabKey = getAttr(item, "data-transport-tab");
          var link = getAttr(item, "data-transport-link");
          var subid = getAttr(item, "data-transport-subid");

          if (e && e.preventDefault) e.preventDefault();
          if (e && e.stopPropagation) e.stopPropagation();

          if (!tabKey) return;

          clearMoreCloseTimer(state);
          setActiveTab(els, state, tabKey, null, link, subid);
          closeMenuNow();
        });
      })(els.moreItems[i]);
    }
  }

  function applyInitialDefaults(els, state) {
    var initialTabEl;

    if (els.departure && !els.departure.value) {
      els.departure.value = addDaysISO(DEFAULTS.defaultDepartureOffsetDays);
    }

    initialTabEl = DOC.getElementById("transport-tab-" + DEFAULTS.initialTab);
    if (!initialTabEl && els.tabs.length) initialTabEl = els.tabs[0];

    if (initialTabEl) {
      setActiveTab(els, state, DEFAULTS.initialTab, initialTabEl);
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
    bindRegionEvents(els, state);
    bindMoreMenuEvents(els, state);
    bindSubmitEvents(els);

    setMenuOpen(els, state, false);
  }

  WIN.initTransportSearch = initTransportSearch;

  if (DOC.readyState === "loading") {
    on(DOC, "DOMContentLoaded", initTransportSearch);
  } else {
    initTransportSearch();
  }

})(window, document);
