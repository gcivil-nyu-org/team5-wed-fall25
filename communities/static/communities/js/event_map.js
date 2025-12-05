/**
 * Event Map Display - JavaScript
 *
 * This script initializes an interactive Mapbox map showing the event location.
 */

/**
 * Initialize the event map
 */
function initEventMap(mapboxToken, longitude, latitude, location) {
  // Validate inputs
  if (!mapboxToken || mapboxToken === "None" || mapboxToken === "") {
    console.warn("Mapbox token not configured");
    showMapMessage("Map service not configured");
    return;
  }

  if (!longitude || !latitude) {
    console.warn("No coordinates available for this event");
    showMapMessage("Location coordinates not available");
    return;
  }

  // Set the Mapbox access token
  mapboxgl.accessToken = mapboxToken;

  try {
    // Create the map
    const map = new mapboxgl.Map({
      container: "eventMap",
      style: "mapbox://styles/mapbox/streets-v12",
      center: [longitude, latitude],
      zoom: 15,
      scrollZoom: true,
    });

    // Add navigation controls
    map.addControl(new mapboxgl.NavigationControl(), "top-right");

    // Add fullscreen control
    map.addControl(new mapboxgl.FullscreenControl(), "top-right");

    // Create a marker at the event location
    const marker = new mapboxgl.Marker({
      color: "#667eea", // Purple color matching communities theme
      draggable: false,
    })
      .setLngLat([longitude, latitude])
      .addTo(map);

    // Create a popup with event location
    const popup = new mapboxgl.Popup({
      offset: 25,
      closeButton: true,
      closeOnClick: false,
    }).setLngLat([longitude, latitude]).setHTML(`
            <div style="padding: 8px; max-width: 250px;">
                <h3 style="margin: 0 0 8px 0; font-size: 16px; font-weight: 600; color: #1f2937;">
                    Event Location
                </h3>
                <p style="margin: 0; font-size: 14px; color: #6b7280; line-height: 1.4;">
                    📍 ${escapeHtml(location)}
                </p>
            </div>
        `);

    // Attach popup to marker
    marker.setPopup(popup);

    // Show popup on page load
    popup.addTo(map);

    console.log("Event map initialized successfully at:", latitude, longitude);
  } catch (error) {
    console.error("Error initializing event map:", error);
    showMapError("Failed to load map");
  }
}

/**
 * Escape HTML to prevent XSS attacks
 */
function escapeHtml(unsafe) {
  if (!unsafe) return "";
  return unsafe
    .toString()
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

/**
 * Show an error message in the map container
 */
function showMapError(message) {
  const mapDiv = document.getElementById("eventMap");
  if (mapDiv) {
    mapDiv.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: center; height: 100%; background: #1a1a1a; color: #9ca3af;">
                ⚠️ ${message}
            </div>
        `;
  }
}

/**
 * Show an informational message in the map container
 */
function showMapMessage(message) {
  const mapDiv = document.getElementById("eventMap");
  if (mapDiv) {
    mapDiv.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: center; height: 100%; background: #1a1a1a; color: #9ca3af;">
                ${message}
            </div>
        `;
  }
}

/**
 * Auto-initialize map when DOM is ready
 */
document.addEventListener("DOMContentLoaded", function () {
  const mapDiv = document.getElementById("eventMap");

  if (mapDiv) {
    // Read data from HTML data attributes
    const token = mapDiv.dataset.mapboxToken;
    const longitude = parseFloat(mapDiv.dataset.lng);
    const latitude = parseFloat(mapDiv.dataset.lat);
    const location = mapDiv.dataset.location;

    // Initialize the map
    initEventMap(token, longitude, latitude, location);
  }
});
