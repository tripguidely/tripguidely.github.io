/* Paris family hotel map. Leaflet and OSM tiles load only on explicit activation.
   Coordinates and upstream evidence: docs/paris-family-hotel-map.md. */
(function () {
  "use strict";
  var section = document.getElementById("hotel-map");
  if (!section || section.getAttribute("data-map-bound")) return;
  section.setAttribute("data-map-bound", "1");
  var trigger = document.getElementById("hotel-map-toggle");
  var view = document.getElementById("hotel-map-view");
  var canvas = document.getElementById("hotel-map-canvas");
  var status = document.getElementById("hotel-map-status");
  var chooser = document.getElementById("hotel-map-choices");
  var card = document.getElementById("hotel-map-card");
  var positions = [
    ["247912", "hotel-citadines-halles", 48.86049, 2.34748],
    ["732134", "hotel-pullman-montparnasse", 48.8385501, 2.3203257],
    ["248416", "hotel-regence-etoile", 48.876564, 2.292922],
    ["412657", "hotel-bb-batignolles", 48.894501, 2.312604]
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
  if (hotels.length !== 4) return;
  trigger.hidden = false;

  function select(index, focus) {
    selected = index;
    var hotel = hotels[index];
    while (card.firstChild) card.removeChild(card.firstChild);
    var number = document.createElement("p");
    number.className = "tg-hotel-map__eyebrow";
    number.textContent = "HOTEL " + (index + 1) + " OF 4";
    var title = document.createElement("h3");
    title.id = "hotel-map-card-title";
    title.tabIndex = -1;
    title.textContent = hotel.name;
    card.appendChild(number);
    card.appendChild(title);
    [".tg-hotel-area", ".tg-hotel-use", ".tg-hotel-facts"].forEach(function (selector) {
      var original = hotel.article.querySelector(selector);
      if (original) card.appendChild(original.cloneNode(true));
    });
    var details = document.createElement("a");
    details.href = "#" + hotel.position[1];
    details.textContent = "Read the full hotel details";
    details.className = "tg-hotel-map__details";
    card.appendChild(details);
    var booking = hotel.link.cloneNode(true);
    booking.setAttribute("data-placement", "map");
    booking.setAttribute("data-experiment-variant", "with_map");
    card.appendChild(booking);
    var note = document.createElement("p");
    note.className = "tg-hotel-map__note";
    note.textContent = "Affiliate link · Opens in a new tab";
    card.appendChild(note);
    choices.forEach(function (choice, i) { choice.setAttribute("aria-pressed", i === index ? "true" : "false"); });
    markers.forEach(function (marker, i) {
      var icon = marker.getElement();
      if (icon) {
        icon.classList.toggle("is-selected", i === index);
        icon.setAttribute("aria-pressed", i === index ? "true" : "false");
      }
    });
    if (focus) title.focus();
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
        status.textContent = "Select a numbered pin or a hotel below to see its details. Use two fingers to move the map on a touch screen.";
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
      icon.setAttribute("aria-label", "Show hotel " + (index + 1) + ": " + hotel.name);
      icon.setAttribute("aria-controls", "hotel-map-card");
      icon.addEventListener("keydown", function (event) {
        if (event.key === " " || event.key === "Enter") { event.preventDefault(); select(index, true); }
      });
      markers.push(marker);
    });
    // Keep one-finger page scrolling; users can pan with two fingers or the keyboard.
    if (window.matchMedia("(pointer: coarse)").matches) {
      map.dragging.disable();
    }
    select(selected, false);
    canvas.setAttribute("data-map-ready", "1");
    status.textContent = "Loading the street map. Hotel details and booking links are ready below.";
    tileTimer = window.setTimeout(function () { if (!tileLoaded) tileFallback(); }, 10000);
    trigger.textContent = "Hide hotel map";
  }

  trigger.addEventListener("click", function () {
    if (loading) return;
    if (map) {
      view.hidden = !view.hidden;
      trigger.setAttribute("aria-expanded", view.hidden ? "false" : "true");
      trigger.textContent = view.hidden ? "Show hotel map" : "Hide hotel map";
      if (!view.hidden) map.invalidateSize({animate: false});
      return;
    }
    view.hidden = false;
    trigger.setAttribute("aria-expanded", "true");
    if (!choices.length) {
      hotels.forEach(function (hotel, index) {
        var choice = document.createElement("button");
        choice.type = "button";
        choice.textContent = (index + 1) + ". " + hotel.name;
        choice.setAttribute("aria-controls", "hotel-map-card");
        choice.addEventListener("click", function () { select(index, true); });
        choices.push(choice); chooser.appendChild(choice);
      });
    }
    select(0, false);
    loading = true;
    trigger.disabled = true;
    trigger.textContent = "Loading hotel map…";
    status.textContent = "Loading the map. You can already choose a hotel and check availability.";
    Promise.all([
      loadAsset("link", "/assets/vendor/leaflet-1.9.4/leaflet.css"),
      loadAsset("script", "/assets/vendor/leaflet-1.9.4/leaflet.js")
    ]).then(buildMap).catch(function (error) {
      if (window.console) window.console.warn("Hotel map unavailable:", error.message);
      if (map) { map.remove(); map = null; markers = []; }
      status.textContent = "The map could not load. Choose a hotel below to see its details and check availability, or use the full hotel list.";
      trigger.textContent = "Retry hotel map";
      section.setAttribute("data-tile-state", "unavailable");
    }).then(function () { loading = false; trigger.disabled = false; });
  });
  section.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && !view.hidden && !loading) {
      view.hidden = true;
      trigger.setAttribute("aria-expanded", "false");
      trigger.textContent = "Show hotel map";
      trigger.focus();
    }
  });
})();
