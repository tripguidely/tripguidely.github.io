/* Neighborhood reference pins, not boundaries or hotel locations.
   Evidence and editorial profile mapping: docs/paris-neighborhood-map.md. */
(function () {
  "use strict";
  var section = document.getElementById("area-map");
  if (!section || section.getAttribute("data-map-bound")) return;
  var canvas = document.getElementById("area-map-canvas");
  var view = document.getElementById("area-map-view");
  var status = document.getElementById("area-map-status");
  var chooser = document.getElementById("area-map-choices");
  var profiles = document.getElementById("area-map-profiles");
  var card = document.getElementById("area-map-card");
  var picker = document.getElementById("area-map-select");
  var pickerWrap = document.getElementById("area-map-picker");
  var selectionStatus = document.getElementById("area-map-selection-status");
  var data = [
  {
    "id": "areas-first",
    "name": "Le Marais",
    "lat": 48.863992,
    "lon": 2.361532,
    "reference": "Square du Temple / Paris Centre town hall",
    "summary": "A lively, central base for cafés, shops and evenings.",
    "profiles": [
      "couple",
      "attractions",
      "nightlife"
    ]
  },
  {
    "id": "area-saint-germain",
    "name": "Saint-Germain-des-Prés",
    "lat": 48.854148,
    "lon": 2.333399,
    "reference": "Place Saint-Germain-des-Prés",
    "summary": "Classic Left Bank atmosphere with strong walkability.",
    "profiles": [
      "couple",
      "attractions"
    ]
  },
  {
    "id": "area-latin",
    "name": "Latin Quarter",
    "lat": 48.848614,
    "lon": 2.342377,
    "reference": "Place de la Sorbonne",
    "summary": "A central alternative with more price flexibility.",
    "profiles": [
      "budget",
      "family",
      "attractions"
    ]
  },
  {
    "id": "area-first",
    "name": "1st Arrondissement",
    "lat": 48.863356,
    "lon": 2.336069,
    "reference": "Place Colette",
    "summary": "Central sightseeing for a short Paris stay.",
    "profiles": [
      "attractions"
    ]
  },
  {
    "id": "areas-family",
    "name": "7th Arrondissement",
    "lat": 48.85288,
    "lon": 2.303337,
    "reference": "Place Joffre",
    "summary": "A calmer base for family and Eiffel Tower plans.",
    "profiles": [
      "family",
      "attractions"
    ]
  },
  {
    "id": "areas-romance",
    "name": "Montmartre",
    "lat": 48.886518,
    "lon": 2.340671,
    "reference": "Place du Tertre",
    "summary": "Character and views, with hillier daily routes.",
    "profiles": [
      "couple"
    ]
  },
  {
    "id": "areas-nightlife",
    "name": "Bastille / Oberkampf",
    "lat": 48.853711,
    "lon": 2.370213,
    "reference": "Place de la Bastille",
    "summary": "An eastern base for nightlife and late evenings.",
    "profiles": [
      "nightlife"
    ]
  },
  {
    "id": "area-south-pigalle",
    "name": "South Pigalle",
    "lat": 48.879563,
    "lon": 2.337431,
    "reference": "Place Gustave Toudouze",
    "summary": "Bars and dining south of Pigalle.",
    "profiles": [
      "nightlife"
    ]
  },
  {
    "id": "area-canal",
    "name": "Canal Saint-Martin",
    "lat": 48.873548,
    "lon": 2.364072,
    "reference": "Quai de Jemmapes",
    "summary": "A slower stay around cafés and the canal.",
    "profiles": [
      "couple"
    ]
  },
  {
    "id": "areas-budget",
    "name": "Opéra / 9th Arrondissement",
    "lat": 48.871044,
    "lon": 2.332135,
    "reference": "Place de l’Opéra",
    "summary": "A practical base for transport and shopping.",
    "profiles": [
      "budget"
    ]
  }
];
  var zones = [], markers = [], choices = [], profileButtons = [];
  var map = null, loading = false, attempted = false, selected = 0, profile = "all";
  var tileTimer = null, tileLoaded = false;
  data.forEach(function (zone) {
    var heading = document.getElementById(zone.id);
    var article = heading && heading.closest(".tg-area-card");
    var item = chooser.querySelector('[data-zone="' + zone.id + '"]');
    if (article && article.querySelectorAll("li").length === 3 && item) {
      zone.article = article; zone.name = heading.textContent; zone.item = item; zones.push(zone);
    }
  });
  // A malformed source keeps the original native area links and cards usable.
  if (zones.length !== 10 || !picker || !pickerWrap || !selectionStatus) return;
  section.setAttribute("data-map-bound", "1");
  view.hidden = false; profiles.hidden = false; card.hidden = false;
  pickerWrap.hidden = false; selectionStatus.hidden = false;

  function matches(zone) { return profile === "all" || zone.profiles.indexOf(profile) !== -1; }
  function announceSelection() {
    var label = profileButtons.find(function (button) { return button.dataset.profile === profile; });
    var text = (label ? label.textContent : "All areas") + ": " + zones.filter(matches).length +
      " suggested areas. Selected area " + (selected + 1) + " of 10: " + zones[selected].name +
      ".";
    if (selectionStatus.textContent !== text) selectionStatus.textContent = text;
  }
  function refreshPicker() {
    while (picker.firstChild) picker.removeChild(picker.firstChild);
    zones.forEach(function (zone, index) {
      if (!matches(zone)) return;
      var option = document.createElement("option");
      option.value = zone.id; option.textContent = (index + 1) + ". " + zone.name;
      picker.appendChild(option);
    });
  }
  picker.addEventListener("change", function () {
    var index = zones.findIndex(function (zone) { return zone.id === picker.value && matches(zone); });
    // Native select arrow keys keep their focus instead of jumping out of the chooser.
    if (index !== -1) select(index, false);
  });
  function select(index, focus) {
    selected = index;
    var zone = zones[index];
    while (card.firstChild) card.removeChild(card.firstChild);
    var number = document.createElement("p");
    number.className = "tg-zone-map__note";
    number.textContent = "AREA " + (index + 1) + " OF 10";
    var heading = document.createElement("h3");
    heading.id = "area-map-card-title"; heading.tabIndex = -1; heading.textContent = zone.name;
    var summary = document.createElement("p"); summary.textContent = zone.summary;
    var reference = document.createElement("p");
    reference.className = "tg-zone-map__note"; reference.textContent = "Reference pin: " + zone.reference + ".";
    card.appendChild(number); card.appendChild(heading); card.appendChild(summary); card.appendChild(reference);
    var facts = document.createElement("dl");
    var labels = ["Good for", "Main advantages", "Main trade-offs"];
    Array.prototype.forEach.call(zone.article.querySelectorAll("li"), function (item, i) {
      var group = document.createElement("div"), term = document.createElement("dt"), detail = document.createElement("dd");
      term.textContent = labels[i];
      detail.textContent = item.textContent.slice(item.querySelector("strong").textContent.length).trim();
      group.appendChild(term); group.appendChild(detail); facts.appendChild(group);
    });
    card.appendChild(facts);
    var links = document.createElement("div"); links.className = "tg-zone-map__links";
    Array.prototype.forEach.call(zone.article.querySelectorAll('a[href^="/"]'), function (original) {
      // Reuse existing internal routes. Booking anchors stay exclusively in the original shortlist.
      links.appendChild(original.cloneNode(true));
    });
    card.appendChild(links);
    syncSelection(); announceSelection();
    if (focus) heading.focus();
  }
  function syncSelection() {
    picker.value = zones[selected].id;
    choices.forEach(function (choice, i) { choice.setAttribute("aria-pressed", i === selected ? "true" : "false"); });
    markers.forEach(function (marker, i) {
      var icon = marker.getElement();
      marker.setZIndexOffset(i === selected ? 1000 : 0);
      if (icon) {
        icon.classList.toggle("is-selected", i === selected);
        icon.setAttribute("aria-pressed", i === selected ? "true" : "false");
      }
    });
  }
  function applyProfile(value) {
    profile = value;
    profileButtons.forEach(function (button) { button.setAttribute("aria-pressed", button.dataset.profile === profile ? "true" : "false"); });
    zones.forEach(function (zone, i) {
      zone.item.hidden = !matches(zone);
    });
    refreshPicker();
    if (map) {
      markers.forEach(function (marker) { marker.remove(); });
      zones.forEach(function (zone, i) { if (matches(zone)) markers[i].addTo(map); });
    }
    if (!matches(zones[selected])) select(zones.findIndex(matches), false);
    syncSelection(); announceSelection();
    if (map) fit();
  }
  function fit() {
    map.fitBounds(zones.filter(matches).map(function (zone) { return [zone.lat, zone.lon]; }), {padding: [32, 32], maxZoom: 14, animate: false});
  }
  zones.forEach(function (zone, index) {
    var button = document.createElement("button");
    button.type = "button"; button.textContent = (index + 1) + ". " + zone.name;
    button.setAttribute("aria-controls", "area-map-card");
    button.addEventListener("click", function () { select(index, true); });
    while (zone.item.firstChild) zone.item.removeChild(zone.item.firstChild);
    zone.item.appendChild(button); choices.push(button);
  });
  [["all","All areas"],["budget","Budget"],["family","Family"],["couple","Couple"],["attractions","Attractions"],["nightlife","Nightlife"]].forEach(function (entry) {
    var button = document.createElement("button");
    button.type = "button"; button.dataset.profile = entry[0]; button.textContent = entry[1];
    button.setAttribute("aria-controls", "area-map-choices area-map-select area-map-card area-map-canvas");
    button.addEventListener("click", function () { applyProfile(entry[0]); });
    profiles.appendChild(button); profileButtons.push(button);
  });
  applyProfile("all"); select(0, false);
  status.textContent = "Choose a travel profile and a numbered area. Area details and internal links are ready; the street map loads as you scroll closer.";

  function loadAsset(tag, url) {
    return new Promise(function (resolve, reject) {
      var asset = document.createElement(tag);
      var timer = window.setTimeout(function () { asset.remove(); reject(new Error("Map asset timeout")); }, 12000);
      if (tag === "link") { asset.rel = "stylesheet"; asset.href = url; }
      else { asset.src = url; asset.async = true; }
      asset.onload = function () { window.clearTimeout(timer); resolve(); };
      asset.onerror = function () { window.clearTimeout(timer); asset.remove(); reject(new Error("Map asset unavailable")); };
      document.head.appendChild(asset);
    });
  }
  function tileFallback() {
    section.setAttribute("data-tile-state", "unavailable");
    status.textContent = "The street map is unavailable. Use the area chooser and travel profiles; the area details and internal links still work.";
  }
  function buildMap() {
    var L = window.L;
    var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    map = L.map(canvas, {scrollWheelZoom: false, minZoom: 11, maxZoom: 17,
      zoomAnimation: !reduceMotion, fadeAnimation: !reduceMotion, markerZoomAnimation: !reduceMotion});
    fit();
    map.attributionControl.setPrefix('<a href="https://leafletjs.com/">Leaflet</a>');
    var tiles = L.tileLayer(section.getAttribute("data-tile-url"), {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>',
      maxZoom: 17, updateWhenIdle: true, keepBuffer: 0, detectRetina: false
    });
    tiles.on("tileload", function () {
      tileLoaded = true; window.clearTimeout(tileTimer);
      if (section.getAttribute("data-tile-state") !== "unavailable") {
        section.setAttribute("data-tile-state", "ready");
        status.textContent = "Select a pin or use the area chooser. Travel profiles show suggested matches; use All areas to restore the full guide. Use + to separate close pins.";
      }
    });
    tiles.on("tileerror", tileFallback); tiles.addTo(map);
    zones.forEach(function (zone, index) {
      var marker = L.marker([zone.lat, zone.lon], {
        icon: L.divIcon({className:"tg-zone-map__pin",html:'<span aria-hidden="true">'+(index+1)+'</span>',iconSize:[44,44],iconAnchor:[22,22]}),
        title:(index+1)+". "+zone.name,keyboard:true,riseOnHover:true
      });
      function decorate() {
        var icon = marker.getElement();
        icon.setAttribute("aria-label","Show area "+(index+1)+": "+zone.name);
        icon.setAttribute("aria-controls","area-map-card");
        icon.addEventListener("keydown", function (event) {
          if (event.key === " " || event.key === "Enter") { event.preventDefault(); select(index,true); }
        });
      }
      marker.on("add",decorate);
      marker.on("click",function () { select(index,true); });
      markers.push(marker);
      if (matches(zone)) marker.addTo(map);
    });
    if (window.matchMedia("(pointer: coarse)").matches) map.dragging.disable();
    syncSelection();
    canvas.setAttribute("data-map-ready","1");
    tileTimer = window.setTimeout(function () { if (!tileLoaded) tileFallback(); },10000);
  }
  function loadMap() {
    if (attempted || loading) return;
    attempted = true; loading = true;
    Promise.all([
      loadAsset("link","/assets/vendor/leaflet-1.9.4/leaflet.css"),
      loadAsset("script","/assets/vendor/leaflet-1.9.4/leaflet.js")
    ]).then(buildMap).catch(function () {
      if (map) { map.remove(); map = null; markers = []; }
      view.hidden = true; section.setAttribute("data-map-state", "unavailable");
      tileFallback();
    }).then(function () { loading = false; });
  }
  if ("IntersectionObserver" in window) {
    var observer = new IntersectionObserver(function (entries) {
      if (entries.some(function (entry) { return entry.isIntersecting; })) { observer.disconnect(); loadMap(); }
    },{rootMargin:"250px 0px"});
    observer.observe(view);
  } else {
    function loadWhenNear() {
      var bounds = view.getBoundingClientRect();
      if (bounds.top < window.innerHeight+250 && bounds.bottom > -250) {
        window.removeEventListener("scroll",loadWhenNear); window.removeEventListener("resize",loadWhenNear); loadMap();
      }
    }
    window.addEventListener("scroll",loadWhenNear,{passive:true});
    window.addEventListener("resize",loadWhenNear); loadWhenNear();
  }
})();
