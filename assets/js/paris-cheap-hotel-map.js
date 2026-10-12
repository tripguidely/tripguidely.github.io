/* Paris budget accommodation map. Open by default; Leaflet/OSM load near the viewport.
   Coordinates and upstream evidence: docs/paris-cheap-hotel-map.md. */
(function () {
  "use strict";
  var section = document.getElementById("hotel-map");
  if (!section || section.getAttribute("data-map-page") !== "paris-cheap" || section.getAttribute("data-map-bound")) return;
  section.setAttribute("data-map-bound", "1");
  var view = document.getElementById("hotel-map-view");
  var canvas = document.getElementById("hotel-map-canvas");
  var status = document.getElementById("hotel-map-status");
  var chooser = document.getElementById("hotel-map-choices");
  var card = document.getElementById("hotel-map-card");
  var positions = [
    ["2846", "hotel-ibis-cambronne", 48.847653, 2.301453],
    ["412657", "hotel-bb-batignolles", 48.894501, 2.312604],
    ["448880", "hotel-generator", 48.8781526, 2.3698083]
  ];
  var hotels = [], markers = [], choices = [], map = null, loading = false;
  var selected = 0, tileTimer = null, tileErrors = 0, tileLoaded = false;

  positions.forEach(function (position) {
    var heading = document.getElementById(position[1]);
    var article = heading && heading.parentNode;
    var link = article && article.querySelector("a.js-aff[data-hotel-id]");
    if (!link || link.getAttribute("data-hotel-id") !== position[0]) return;
    hotels.push({position: position, article: article, link: link, name: heading.textContent});
  });
  // The existing HTML list is always the booking fallback.
  if (hotels.length !== 3) return;
  view.hidden = false;

  function select(index, focus) {
    var previousDetails = card.querySelector("details");
    var keepOpen = selected === index && previousDetails && previousDetails.open;
    selected = index;
    var hotel = hotels[index];
    while (card.firstChild) card.removeChild(card.firstChild);
    var number = document.createElement("p");
    number.className = "tg-hotel-map__eyebrow";
    number.textContent = "STAY " + (index + 1) + " OF 3";
    var title = document.createElement("h3");
    title.id = "hotel-map-card-title";
    title.tabIndex = -1;
    title.textContent = hotel.name;
    card.appendChild(number);
    card.appendChild(title);
    [".tg-hotel-area", ".tg-hotel-use"].forEach(function (selector) {
      var original = hotel.article.querySelector(selector);
      if (original) card.appendChild(original.cloneNode(true));
    });
    var facts = hotel.article.querySelector(".tg-hotel-facts");
    var quickFacts = facts.cloneNode(false);
    var extraFacts = facts.cloneNode(false);
    Array.prototype.forEach.call(facts.children, function (row) {
      var key = row.getAttribute("data-fact");
      var target = key === "capacity" || key === "transport" ? quickFacts : extraFacts;
      target.appendChild(row.cloneNode(true));
    });
    card.appendChild(quickFacts);
    var details = document.createElement("details");
    details.className = "tg-hotel-map__details";
    details.open = !!keepOpen;
    var summary = document.createElement("summary");
    summary.textContent = "Full stay details";
    summary.setAttribute("aria-label", "Full stay details for " + hotel.name);
    details.appendChild(summary);
    details.appendChild(extraFacts);
    Array.prototype.forEach.call(hotel.article.children, function (child) {
      if (child.tagName === "P" && !child.matches(".tg-hotel-area, .tg-hotel-use")) {
        details.appendChild(child.cloneNode(true));
      }
    });
    var booking = hotel.link.cloneNode(true);
    booking.setAttribute("data-placement", "map");
    booking.setAttribute("data-experiment-variant", "with_map");
    var action = document.createElement("div");
    action.className = "tg-hotel-map__action";
    action.appendChild(booking);
    card.appendChild(action);
    card.appendChild(details);
    syncSelection(index);
    if (focus) title.focus();
  }

  function syncSelection(index) {
    choices.forEach(function (choice, i) { choice.setAttribute("aria-pressed", i === index ? "true" : "false"); });
    markers.forEach(function (marker, i) {
      var icon = marker.getElement();
      if (icon) {
        icon.classList.toggle("is-selected", i === index);
        icon.setAttribute("aria-pressed", i === index ? "true" : "false");
      }
    });
  }

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
    status.textContent = "Street tiles are unavailable. Choose a numbered hotel below; its details and booking link still work.";
    section.setAttribute("data-tile-state", "unavailable");
  }

  function buildMap() {
    var L = window.L;
    var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    map = L.map(canvas, {scrollWheelZoom: false, minZoom: 11, maxZoom: 17,
      zoomAnimation: !reduceMotion, fadeAnimation: !reduceMotion, markerZoomAnimation: !reduceMotion});
    map.fitBounds(hotels.map(function (hotel) { return [hotel.position[2], hotel.position[3]]; }), {padding: [36, 36], animate: false});
    map.attributionControl.setPrefix('<a href="https://leafletjs.com/">Leaflet</a>');
    var tiles = L.tileLayer(section.getAttribute("data-tile-url"), {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>',
      maxZoom: 17, updateWhenIdle: true, keepBuffer: 0, detectRetina: false
    });
    tiles.on("tileload", function () {
      tileLoaded = true;
      window.clearTimeout(tileTimer);
      if (!tileErrors) {
        status.textContent = "Select a numbered pin or a hotel below to see its details. Use the zoom controls or keyboard to explore; page scrolling remains available.";
        section.setAttribute("data-tile-state", "ready");
      }
    });
    tiles.on("tileerror", function () { tileErrors++; tileFallback(); });
    tiles.addTo(map);
    hotels.forEach(function (hotel, index) {
      var marker = L.marker([hotel.position[2], hotel.position[3]], {
        icon: L.divIcon({className: "tg-hotel-map__pin", html: '<span aria-hidden="true">' + (index + 1) + '</span>', iconSize: [44, 44], iconAnchor: [22, 22]}),
        title: (index + 1) + ". " + hotel.name, keyboard: true, riseOnHover: true
      }).addTo(map);
      marker.on("click", function () { select(index, true); });
      var icon = marker.getElement();
      icon.setAttribute("aria-label", "Show stay " + (index + 1) + ": " + hotel.name);
      icon.setAttribute("aria-controls", "hotel-map-card");
      icon.addEventListener("keydown", function (event) {
        if (event.key === " " || event.key === "Enter") { event.preventDefault(); select(index, true); }
      });
      markers.push(marker);
    });
    // Keep one-finger page scrolling; retain pinch zoom and keyboard exploration.
    if (window.matchMedia("(pointer: coarse)").matches) {
      map.dragging.disable();
    }
    // Do not replace an open details panel or its focused control on tile load.
    syncSelection(selected);
    canvas.setAttribute("data-map-ready", "1");
    status.textContent = "Loading the street map. Hotel details and booking links are ready below.";
    tileTimer = window.setTimeout(function () { if (!tileLoaded) tileFallback(); }, 10000);
  }

  hotels.forEach(function (hotel, index) {
    var choice = document.createElement("button");
    choice.type = "button";
    choice.textContent = (index + 1) + ". " + hotel.name;
    choice.setAttribute("aria-controls", "hotel-map-card");
    choice.addEventListener("click", function () { select(index, true); });
    choices.push(choice); chooser.appendChild(choice);
  });
  select(0, false);
  status.textContent = "The street map loads as you scroll closer. Hotel details and booking links are available below.";

  function loadMap() {
    if (loading || map) return;
    loading = true;
    status.textContent = "Loading the map. You can already choose a hotel and check availability.";
    Promise.all([
      loadAsset("link", "/assets/vendor/leaflet-1.9.4/leaflet.css"),
      loadAsset("script", "/assets/vendor/leaflet-1.9.4/leaflet.js")
    ]).then(buildMap).catch(function (error) {
      if (window.console) window.console.warn("Hotel map unavailable:", error.message);
      if (map) { map.remove(); map = null; markers = []; }
      status.textContent = "The map could not load. Choose a hotel below to see its details and check availability, or use the full hotel list.";
      section.setAttribute("data-tile-state", "unavailable");
    }).then(function () { loading = false; });
  }

  if ("IntersectionObserver" in window) {
    var observer = new IntersectionObserver(function (entries) {
      if (entries.some(function (entry) { return entry.isIntersecting; })) {
        observer.disconnect();
        loadMap();
      }
    }, {rootMargin: "250px 0px"});
    observer.observe(section);
  } else {
    // Older browsers still defer network activity until the section is nearby.
    function loadWhenNear() {
      var bounds = section.getBoundingClientRect();
      if (bounds.top < window.innerHeight + 250 && bounds.bottom > -250) {
        window.removeEventListener("scroll", loadWhenNear);
        window.removeEventListener("resize", loadWhenNear);
        loadMap();
      }
    }
    window.addEventListener("scroll", loadWhenNear, {passive: true});
    window.addEventListener("resize", loadWhenNear);
    loadWhenNear();
  }
})();
