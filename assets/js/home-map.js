(function () {
  const MAP_FILE = "/assets/images/ui/world-map.svg";

  const cities = [
    {
      name: "New York",
      lat: 40.7128,
      lon: -74.0060,
      labelDx: 14,
      labelDy: -10,
      url: "/things-to-do/new-york/"
    },
    {
      name: "Las Vegas",
      lat: 36.1699,
      lon: -115.1398,
      labelDx: 14,
      labelDy: -10,
      url: "/things-to-do/las-vegas/"
    },
    {
      name: "Quebec City",
      lat: 46.8139,
      lon: -71.2080,
      labelDx: 14,
      labelDy: -10,
      url: "/things-to-do/quebec-city/"
    },
    {
      name: "London",
      lat: 51.5074,
      lon: -0.1278,
      labelDx: 10,
      labelDy: -12,
      url: "/things-to-do/london/"
    },
    {
      name: "Paris",
      lat: 48.8566,
      lon: 2.3522,
      labelDx: 10,
      labelDy: 18,
      url: "/things-to-do/paris/"
    },
    {
      name: "Rome",
      lat: 41.9028,
      lon: 12.4964,
      labelDx: 10,
      labelDy: 18,
      url: "/things-to-do/rome/"
    },
    {
      name: "Dubai",
      lat: 25.2048,
      lon: 55.2708,
      labelDx: 12,
      labelDy: -12,
      url: "/things-to-do/dubai/"
    },
    {
      name: "Bangkok",
      lat: 13.7563,
      lon: 100.5018,
      labelDx: 12,
      labelDy: -12,
      url: "/things-to-do/bangkok/"
    },
    {
      name: "Tokyo",
      lat: 35.6762,
      lon: 139.6503,
      labelDx: 14,
      labelDy: -10,
      url: "/things-to-do/tokyo/"
    }
  ];

  const canvas = document.getElementById("home-map-explorer-canvas");
  const loading = document.getElementById("home-map-explorer-loading");
  const tooltip = document.getElementById("home-map-explorer-tooltip");

  if (!canvas || !loading || !tooltip) return;

  fetch(MAP_FILE)
    .then((res) => {
      if (!res.ok) throw new Error("SVG file not found: " + MAP_FILE);
      return res.text();
    })
    .then((svgText) => {
      const parser = new DOMParser();
      const doc = parser.parseFromString(svgText, "image/svg+xml");
      const svg = doc.querySelector("svg");

      if (!svg) throw new Error("Invalid SVG.");

      const rawViewBox = svg.getAttribute("viewBox") || svg.getAttribute("viewbox");
      const widthAttr = parseFloat(svg.getAttribute("width")) || 2000;
      const heightAttr = parseFloat(svg.getAttribute("height")) || 857;

      if (rawViewBox) {
        svg.setAttribute("viewBox", rawViewBox);
      } else {
        svg.setAttribute("viewBox", `0 0 ${widthAttr} ${heightAttr}`);
      }

      svg.removeAttribute("viewbox");
      svg.removeAttribute("width");
      svg.removeAttribute("height");
      svg.removeAttribute("baseprofile");

      const viewBox = (svg.getAttribute("viewBox") || `0 0 ${widthAttr} ${heightAttr}`)
        .split(/\s+/)
        .map(Number);

      const vbX = viewBox[0];
      const vbY = viewBox[1];
      const vbW = viewBox[2];
      const vbH = viewBox[3];

      svg.classList.add("map-explorer__svg");
      svg.setAttribute("aria-label", "World map with TripGuidely city markers");
      svg.setAttribute("role", "img");
      svg.setAttribute("preserveAspectRatio", "xMidYMid meet");

      const markerLayer = document.createElementNS("http://www.w3.org/2000/svg", "g");
      markerLayer.setAttribute("class", "map-explorer__markers");

      cities.forEach((city) => {
        const point = latLonToSvg(city.lat, city.lon, vbX, vbY, vbW, vbH);
        const marker = createMarker(
          {
            ...city,
            x: point.x,
            y: point.y
          },
          canvas,
          tooltip
        );
        markerLayer.appendChild(marker);
      });

      svg.appendChild(markerLayer);

      loading.remove();
      canvas.insertBefore(svg, tooltip);
    })
    .catch((error) => {
      console.error(error);
      loading.textContent = "Map unavailable. Check /assets/images/ui/world-map.svg and /assets/js/home-map.js.";
    });

  function latLonToSvg(lat, lon, vbX, vbY, vbW, vbH) {
    const x = vbX + ((lon + 180) / 360) * vbW;
    const y = vbY + ((90 - lat) / 180) * vbH;
    return { x, y };
  }

  function createMarker(city, canvas, tooltip) {
    const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
    g.setAttribute("class", "map-city-marker");
    g.setAttribute("tabindex", "0");
    g.setAttribute("role", "link");
    g.setAttribute("aria-label", city.name);
    g.setAttribute("data-url", city.url);
    g.style.cursor = "pointer";

    const pulse = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    pulse.setAttribute("cx", city.x);
    pulse.setAttribute("cy", city.y);
    pulse.setAttribute("r", "14");
    pulse.setAttribute("class", "map-city-marker__pulse");

    const outer = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    outer.setAttribute("cx", city.x);
    outer.setAttribute("cy", city.y);
    outer.setAttribute("r", "8");
    outer.setAttribute("class", "map-city-marker__outer");

    const inner = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    inner.setAttribute("cx", city.x);
    inner.setAttribute("cy", city.y);
    inner.setAttribute("r", "4");
    inner.setAttribute("class", "map-city-marker__inner");

    const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
    label.setAttribute("x", city.x + (city.labelDx ?? 14));
    label.setAttribute("y", city.y + (city.labelDy ?? -10));
    label.setAttribute("class", "map-city-marker__label");
    label.textContent = city.name;

    g.appendChild(pulse);
    g.appendChild(outer);
    g.appendChild(inner);
    g.appendChild(label);

    g.addEventListener("mouseenter", (e) => {
      tooltip.textContent = city.name;
      tooltip.classList.add("is-visible");
      positionTooltip(e.clientX, e.clientY, canvas, tooltip);
    });

    g.addEventListener("mousemove", (e) => {
      positionTooltip(e.clientX, e.clientY, canvas, tooltip);
    });

    g.addEventListener("mouseleave", () => {
      tooltip.classList.remove("is-visible");
    });

    g.addEventListener("focus", () => {
      tooltip.textContent = city.name;
      tooltip.classList.add("is-visible");

      const rect = g.getBoundingClientRect();
      const canvasRect = canvas.getBoundingClientRect();
      tooltip.style.left = rect.left + rect.width / 2 - canvasRect.left + "px";
      tooltip.style.top = rect.top - canvasRect.top + "px";
    });

    g.addEventListener("blur", () => {
      tooltip.classList.remove("is-visible");
    });

    g.addEventListener("click", () => {
      window.location.href = city.url;
    });

    g.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        window.location.href = city.url;
      }
    });

    return g;
  }

  function positionTooltip(clientX, clientY, canvas, tooltip) {
    const rect = canvas.getBoundingClientRect();
    tooltip.style.left = clientX - rect.left + "px";
    tooltip.style.top = clientY - rect.top + "px";
  }
})();
