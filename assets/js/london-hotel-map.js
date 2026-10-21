/* London guides (adapted from the existing New York controller): progressive Leaflet enhancement; booking stays in static HTML.
   Sources and image restrictions: docs/qa/london-hotels-sources.json.
   All affiliate analytics use the existing delegated, consent-aware site.js handler. */
(function () {
  "use strict";
  var section = document.getElementById("hotel-map");
  if (!section || !/^london-(luxury|family|cheap)$/.test(section.getAttribute("data-map-page") || "") || section.hasAttribute("data-map-bound")) return;
  var view = document.getElementById("hotel-map-view"), canvas = document.getElementById("hotel-map-canvas");
  var status = document.getElementById("hotel-map-status"), card = document.getElementById("hotel-map-card");
  var chooser = document.getElementById("hotel-map-choices"), reset = document.getElementById("hotel-map-reset"), touch = document.getElementById("hotel-map-touch");
  if (!view || !canvas || !status || !card || !chooser || !reset || !touch) return;
  var hotels = [], choices = [], markers = [], map = null, started = false, failed = false, tileTimer, assetTimer;
  var tilesLoaded = false, tileErrors = 0, selected = 0;
  var coarse = window.matchMedia("(pointer: coarse)");
  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)");
  // Keep touch-safe defaults on hybrid devices even when a mouse is primary.
  function touchDevice() { return coarse.matches || (navigator.maxTouchPoints || 0) > 0; }
  document.querySelectorAll(".lh-hotel-card[data-offer-id]").forEach(function (article) {
    var link = article.querySelector("a.js-aff[data-offer-id]"), heading = article.querySelector("h3");
    var lat = Number(article.getAttribute("data-latitude")), lon = Number(article.getAttribute("data-longitude"));
    if (!link || !heading || link.getAttribute("data-offer-id") !== article.getAttribute("data-offer-id") || !Number.isFinite(lat) || !Number.isFinite(lon) || lat < 51.4 || lat > 51.6 || lon < -0.3 || lon > 0.1) return;
    hotels.push({article:article, link:link, name:heading.textContent, id:link.getAttribute("data-offer-id"), position:[lat,lon]});
  });
  if (hotels.length !== 3 || new Set(hotels.map(function (h) { return h.id; })).size !== 3) return;
  section.setAttribute("data-map-bound", "1");
  view.hidden = false;
  function sync() {
    choices.forEach(function (button, i) { button.setAttribute("aria-pressed", String(i === selected)); });
    hotels.forEach(function (hotel, i) {
      hotel.article.classList.toggle("is-selected", i === selected);
      var button = hotel.article.querySelector(".lh-show-map");
      if (button) button.setAttribute("aria-pressed", String(i === selected));
      var icon = markers[i] && markers[i].getElement();
      if (icon) { icon.classList.toggle("is-selected", i === selected); icon.setAttribute("aria-pressed", String(i === selected)); }
    });
  }
  function select(index, focus) {
    selected = index;
    var hotel = hotels[index];
    card.replaceChildren();
    var eyebrow = document.createElement("p");
    eyebrow.className = "lh-eyebrow"; eyebrow.textContent = "STAY " + (index + 1) + " OF 3";
    var title = document.createElement("h3"); title.id = "hotel-map-card-title"; title.tabIndex = -1; title.textContent = hotel.name;
    card.append(eyebrow, title);
    [".lh-hotel-fit"].forEach(function (selector) {
      var source = hotel.article.querySelector(selector);
      if (source) card.appendChild(source.cloneNode(true));
    });
    var link = hotel.link.cloneNode(true);
    link.setAttribute("data-cta-id", hotel.id + "_map");
    link.setAttribute("data-cta-location", "map");
    card.appendChild(link);
    var facts = hotel.article.querySelector(".lh-hotel-facts");
    if (facts) card.appendChild(facts.cloneNode(true));
    var note = document.createElement("p"); note.textContent = "Check the exact room, guests, total and cancellation conditions for your dates.";
    card.appendChild(note);
    // Each selection starts at its heading, including previously scrolled panels.
    card.scrollTop = 0;
    sync();
    if (map) map.panTo(hotel.position, {animate:!reduced.matches});
    if (focus) title.focus({preventScroll:true});
  }
  hotels.forEach(function (hotel, index) {
    var button = document.createElement("button"); button.type = "button";
    button.textContent = (index + 1) + ". " + hotel.name;
    button.setAttribute("aria-controls", "hotel-map-card");
    button.addEventListener("click", function () { select(index, false); });
    chooser.appendChild(button); choices.push(button);
    var show = hotel.article.querySelector(".lh-show-map");
    if (show) {
      show.hidden = false;
      show.addEventListener("click", function () {
        start(); select(index, true);
        section.scrollIntoView({behavior:reduced.matches ? "auto" : "smooth", block:"start"});
      });
    }
  });
  select(0, false);
  function fit() { if (map) map.fitBounds(hotels.map(function (h) { return h.position; }), {padding:[44,44], maxZoom:15, animate:false}); }
  function movement(enabled) {
    if (map) { if (enabled) map.dragging.enable(); else map.dragging.disable(); }
    canvas.classList.toggle("lh-map-scroll", !enabled);
    canvas.classList.toggle("lh-map-move", enabled);
    touch.setAttribute("aria-pressed", String(enabled));
    touch.textContent = enabled ? "Lock map movement" : "Enable map movement";
    if (map) status.textContent = enabled ? "Map movement enabled. Drag to pan; press Escape or lock to resume page scrolling." : "Scroll the page over the map. Enable map movement to pan; zoom buttons and hotel choices remain available.";
  }
  function pointerMode() { touch.hidden = !touchDevice() || !map; movement(!touchDevice()); }
  touch.addEventListener("click", function () { movement(touch.getAttribute("aria-pressed") !== "true"); });
  canvas.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && touchDevice()) { movement(false); touch.focus(); }
  });
  if (coarse.addEventListener) coarse.addEventListener("change", pointerMode);
  reset.addEventListener("click", fit);
  function tileFailure() {
    if (tilesLoaded) return;
    status.textContent = "The map background is unavailable. Use the numbered hotel choices and full address list; booking links remain available.";
    section.setAttribute("data-map-state", "tiles-unavailable");
  }
  function fail() {
    failed = true; clearTimeout(assetTimer);
    section.setAttribute("data-map-state", "unavailable");
    status.textContent = "The interactive map could not load. Use the hotel choices, addresses and booking links below.";
    canvas.hidden = true;
  }
  function initialize() {
    if (failed || map || !window.L || !window.L.map) return;
    clearTimeout(assetTimer);
    try {
      map = L.map(canvas, {scrollWheelZoom:false, dragging:!touchDevice(), tap:false, zoomAnimation:!reduced.matches, fadeAnimation:!reduced.matches, markerZoomAnimation:!reduced.matches});
      var layer = L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {maxZoom:19, attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'}).addTo(map);
      layer.on("tileload", function () {
        tilesLoaded = true; clearTimeout(tileTimer);
        section.setAttribute("data-map-state", "ready");
        if (!touchDevice()) status.textContent = "Choose a numbered hotel. Drag or use arrow keys to pan; use + and − to zoom. Page scrolling stays enabled.";
        else movement(touch.getAttribute("aria-pressed") === "true");
      });
      layer.on("tileerror", function () { tileErrors++; if (tileErrors >= 3) tileFailure(); });
      fit();
      hotels.forEach(function (hotel, index) {
        var marker = L.marker(hotel.position, {keyboard:true, title:hotel.name, alt:hotel.name,
          icon:L.divIcon({className:"lh-map-pin", html:String(index+1), iconSize:[44,44], iconAnchor:[22,22]})}).addTo(map);
        marker.on("click", function () { select(index, false); });
        var icon = marker.getElement();
        if (icon) {
          icon.setAttribute("role", "button"); icon.setAttribute("aria-label", "Select " + hotel.name);
          icon.setAttribute("aria-controls", "hotel-map-card");
          icon.addEventListener("keydown", function (event) {
            if (event.key === " " || event.key === "Enter") { event.preventDefault(); select(index, false); }
          });
        }
        markers.push(marker);
      });
      sync(); pointerMode(); reset.disabled = false;
      if (!touchDevice()) status.textContent = "Choose a numbered hotel. Drag or use arrow keys to pan; use + and − to zoom. Page scrolling stays enabled.";
      tileTimer = setTimeout(tileFailure, 10000);
      section.setAttribute("data-map-state", "loading-tiles");
    } catch (error) {
      if (map) { map.remove(); map = null; }
      fail();
    }
  }
  function start() {
    if (started) return; started = true;
    section.setAttribute("data-map-state", "loading");
    status.textContent = "Loading the map. Hotel choices and booking links are already available.";
    if (window.L && window.L.map) { initialize(); return; }
    var style = document.createElement("link"); style.rel = "stylesheet"; style.href = "/assets/vendor/leaflet-1.9.4/leaflet.css";
    var script = document.createElement("script"); script.src = "/assets/vendor/leaflet-1.9.4/leaflet.js"; script.async = true;
    var loaded = 0;
    function assetReady() { if (++loaded === 2) initialize(); }
    style.onload = assetReady; script.onload = assetReady;
    style.onerror = fail; script.onerror = fail;
    assetTimer = setTimeout(fail, 12000);
    document.head.append(style, script);
  }
  if ("IntersectionObserver" in window) {
    var observer = new IntersectionObserver(function (entries) {
      if (entries.some(function (entry) { return entry.isIntersecting; })) { observer.disconnect(); start(); }
    }, {rootMargin:"250px"});
    observer.observe(section);
  } else {
    function nearby() { if (section.getBoundingClientRect().top < innerHeight + 250) { removeEventListener("scroll", nearby); removeEventListener("resize", nearby); start(); } }
    addEventListener("scroll", nearby, {passive:true}); addEventListener("resize", nearby); nearby();
  }
}());
