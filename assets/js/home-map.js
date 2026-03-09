(function () {
  const MAP_FILE = "/assets/images/ui/world-map.svg";

  const destinations = {
    CA: {
      name: "Canada",
      label: "Quebec City travel guide",
      url: "/travel-guides/quebec-city/"
    },
    US: {
      name: "United States",
      label: "New York travel guide",
      url: "/travel-guides/new-york/"
    },
    FR: {
      name: "France",
      label: "Paris travel guide",
      url: "/travel-guides/paris/"
    },
    GB: {
      name: "United Kingdom",
      label: "London travel guide",
      url: "/travel-guides/london/"
    },
    IT: {
      name: "Italy",
      label: "Rome travel guide",
      url: "/travel-guides/rome/"
    },
    JP: {
      name: "Japan",
      label: "Tokyo travel guide",
      url: "/travel-guides/tokyo/"
    },
    TH: {
      name: "Thailand",
      label: "Bangkok travel guide",
      url: "/travel-guides/bangkok/"
    },
    AE: {
      name: "United Arab Emirates",
      label: "Dubai travel guide",
      url: "/travel-guides/dubai/"
    }
  };

  const selectorMap = {
    CA: ["#CA", "#ca", "#Canada", "#canada"],
    US: ["#US", "#us", "#USA", "#usa", "#UnitedStates", "#united-states"],
    FR: ["#FR", "#fr", "#France", "#france"],
    GB: ["#GB", "#gb", "#UK", "#uk", "#UnitedKingdom", "#united-kingdom"],
    IT: ["#IT", "#it", "#Italy", "#italy"],
    JP: ["#JP", "#jp", "#Japan", "#japan"],
    TH: ["#TH", "#th", "#Thailand", "#thailand"],
    AE: ["#AE", "#ae", "#UAE", "#uae", "#UnitedArabEmirates", "#united-arab-emirates"]
  };

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

      svg.classList.add("map-explorer__svg");
      svg.setAttribute("aria-label", "World map with clickable TripGuidely destinations");
      svg.setAttribute("role", "img");
      svg.setAttribute("preserveAspectRatio", "xMidYMid meet");

      const shapes = svg.querySelectorAll("path, polygon");
      shapes.forEach((node) => {
        node.classList.add("is-inactive");
      });

      Object.keys(destinations).forEach((code) => {
        const selectors = selectorMap[code] || [];
        const meta = destinations[code];
        const matched = new Set();

        selectors.forEach((selector) => {
          svg.querySelectorAll(selector).forEach((el) => matched.add(el));
        });

        matched.forEach((node) => {
          node.classList.remove("is-inactive");
          node.classList.add("is-active");
          node.setAttribute("data-country", code);
          node.setAttribute("data-label", meta.label);
          node.setAttribute("data-url", meta.url);
          node.setAttribute("tabindex", "0");
          node.setAttribute("role", "link");

          node.addEventListener("mouseenter", () => {
            tooltip.textContent = meta.label;
            tooltip.classList.add("is-visible");
          });

          node.addEventListener("mousemove", (e) => {
            const rect = canvas.getBoundingClientRect();
            tooltip.style.left = (e.clientX - rect.left) + "px";
            tooltip.style.top = (e.clientY - rect.top) + "px";
          });

          node.addEventListener("mouseleave", () => {
            tooltip.classList.remove("is-visible");
          });

          node.addEventListener("focus", () => {
            tooltip.textContent = meta.label;
            tooltip.classList.add("is-visible");
            const rect = node.getBoundingClientRect();
            const canvasRect = canvas.getBoundingClientRect();
            tooltip.style.left = (rect.left + rect.width / 2 - canvasRect.left) + "px";
            tooltip.style.top = (rect.top - canvasRect.top) + "px";
          });

          node.addEventListener("blur", () => {
            tooltip.classList.remove("is-visible");
          });

          node.addEventListener("click", () => {
            window.location.href = meta.url;
          });

          node.addEventListener("keydown", (e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              window.location.href = meta.url;
            }
          });
        });
      });

      loading.remove();
      canvas.insertBefore(svg, tooltip);
    })
    .catch((error) => {
      console.error(error);
      loading.textContent = "Map unavailable. Check /assets/images/ui/world-map.svg and /assets/js/home-map.js.";
    });
})();
