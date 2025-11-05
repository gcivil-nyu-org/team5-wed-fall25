/**
 * Listing Map Display - JavaScript
 *
 * This script initializes an interactive Mapbox map showing the listing location.
 *
 * How it works:
 * 1. Check if we have valid coordinates from the backend
 * 2. Initialize Mapbox GL JS with the access token
 * 3. Create a map centered on the listing location
 * 4. Add a marker pin at the exact address
 * 5. Add a popup with listing information
 */

/**
 * Initialize the listing map
 *
 * @param {string} mapboxToken - Mapbox API access token from backend
 * @param {number} longitude - Longitude coordinate of the listing
 * @param {number} latitude - Latitude coordinate of the listing
 * @param {string} address - Full address text for display
 * @param {string} title - Listing title for popup
 */
function initListingMap(mapboxToken, longitude, latitude, address, title) {
  // Validate inputs
  if (!mapboxToken) {
    console.error("Mapbox token not provided");
    showMapError("Map configuration error");
    return;
  }

  if (!longitude || !latitude) {
    console.warn("No coordinates available for this listing");
    showMapMessage("Location coordinates not available");
    return;
  }

  // Set the Mapbox access token
  mapboxgl.accessToken = mapboxToken;

  try {
    // Create the map
    // - container: ID of the HTML element to render the map in
    // - style: Mapbox style (streets, satellite, etc.)
    // - center: [longitude, latitude] - initial map center
    // - zoom: Initial zoom level (0-22, where 14 shows neighborhood level)
    const map = new mapboxgl.Map({
      container: "listing-map", // Must match the div ID in HTML
      style: "mapbox://styles/mapbox/streets-v12", // Map style
      center: [longitude, latitude], // Center on listing location
      zoom: 14, // Zoom level - 14 is good for neighborhood view
      scrollZoom: true, // Allow zooming with mouse scroll
    });

    // Add navigation controls (zoom in/out buttons, compass)
    map.addControl(new mapboxgl.NavigationControl(), "top-right");

    // Add fullscreen control
    map.addControl(new mapboxgl.FullscreenControl(), "top-right");

    // Create a marker at the listing location
    // The marker is a visual pin on the map
    const marker = new mapboxgl.Marker({
      color: "#3b82f6", // Blue color matching your theme
      draggable: false, // User can't move the marker
    })
      .setLngLat([longitude, latitude]) // Set marker position
      .addTo(map); // Add to the map

    // Create a popup with listing information
    // This appears when user clicks the marker
    const popup = new mapboxgl.Popup({
      offset: 25, // Offset so popup doesn't cover marker
      closeButton: true,
      closeOnClick: false,
    }).setLngLat([longitude, latitude]).setHTML(`
            <div style="padding: 8px; max-width: 250px;">
                <h3 style="margin: 0 0 8px 0; font-size: 16px; font-weight: 600; color: #1f2937;">
                    ${escapeHtml(title)}
                </h3>
                <p style="margin: 0; font-size: 14px; color: #6b7280; line-height: 1.4;">
                    📍 ${escapeHtml(address)}
                </p>
            </div>
        `);

    // Attach popup to marker
    marker.setPopup(popup);

    // Show popup on page load (so user immediately sees the location)
    popup.addTo(map);

    // Log success
    console.log("Map initialized successfully at:", latitude, longitude);
  } catch (error) {
    console.error("Error initializing map:", error);
    showMapError("Failed to load map");
  }
}

/**
 * Escape HTML to prevent XSS attacks
 * This sanitizes user input before displaying in popups
 */
function escapeHtml(unsafe) {
  return unsafe
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
  const mapDiv = document.getElementById("listing-map");
  if (mapDiv) {
    mapDiv.innerHTML = `
            <div class="map-error">
                ⚠️ ${message}
            </div>
        `;
  }
}

/**
 * Show an informational message in the map container
 */
function showMapMessage(message) {
  const mapDiv = document.getElementById("listing-map");
  if (mapDiv) {
    mapDiv.innerHTML = `
            <div class="map-loading">
                ${message}
            </div>
        `;
  }
}

/**
 * Auto-initialize map when DOM is ready
 * This reads data attributes from the HTML element
 */
document.addEventListener("DOMContentLoaded", function () {
  const mapDiv = document.getElementById("listing-map");

  if (mapDiv) {
    // Read data from HTML data attributes
    const token = mapDiv.dataset.mapboxToken;
    const longitude = parseFloat(mapDiv.dataset.longitude);
    const latitude = parseFloat(mapDiv.dataset.latitude);
    const address = mapDiv.dataset.address;
    const title = mapDiv.dataset.title;

    // Initialize the map
    initListingMap(token, longitude, latitude, address, title);
  }
});
