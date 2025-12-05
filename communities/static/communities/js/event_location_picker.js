/**
 * Event Location Picker - Interactive Map for Selecting Event Location
 *
 * This script initializes a Mapbox map that allows users to:
 * 1. Click on the map to set event location
 * 2. Search for addresses using the geocoder
 * 3. Automatically update hidden lat/lng form fields
 */

document.addEventListener("DOMContentLoaded", function () {
  const mapDiv = document.getElementById("event-location-map");

  if (!mapDiv) {
    return; // Map div not found, exit
  }

  const token = mapDiv.dataset.mapboxToken;

  if (!token || token === "None" || token === "") {
    console.warn("Mapbox token not configured");
    mapDiv.innerHTML = '<div class="map-loading">📍 Map service not configured. You can still create events without map coordinates.</div>';
    return;
  }

  // Set Mapbox access token
  mapboxgl.accessToken = token;

  // Get form fields for lat/lng
  const latInput = document.getElementById("id_latitude");
  const lngInput = document.getElementById("id_longitude");

  if (!latInput || !lngInput) {
    console.error("Latitude or longitude input fields not found");
    return;
  }

  // Check if editing existing event with coordinates
  const initialLat = latInput.value ? parseFloat(latInput.value) : null;
  const initialLng = lngInput.value ? parseFloat(lngInput.value) : null;

  // Default center (New York City - center of NYC universities)
  let center = [-73.935242, 40.73061];
  let zoom = 12;

  // If editing and has coordinates, center on those
  if (initialLat && initialLng) {
    center = [initialLng, initialLat];
    zoom = 15;
  }

  try {
    // Initialize map
    const map = new mapboxgl.Map({
      container: "event-location-map",
      style: "mapbox://styles/mapbox/streets-v12",
      center: center,
      zoom: zoom,
      scrollZoom: true,
    });

    // Add navigation controls
    map.addControl(new mapboxgl.NavigationControl(), "top-right");

    // Add fullscreen control
    map.addControl(new mapboxgl.FullscreenControl(), "top-right");

    // Add geocoder (search box)
    const geocoder = new MapboxGeocoder({
      accessToken: mapboxgl.accessToken,
      mapboxgl: mapboxgl,
      marker: false, // We'll add our own marker
      placeholder: "Search for event location...",
      proximity: {
        longitude: -73.935242,
        latitude: 40.73061,
      }, // Bias results toward NYC
    });

    map.addControl(geocoder, "top-left");

    // Create a draggable marker
    let marker = null;

    // Function to update marker position and form fields
    function updateLocation(lngLat) {
      const lng = lngLat.lng;
      const lat = lngLat.lat;

      // Update form fields
      lngInput.value = lng.toFixed(6);
      latInput.value = lat.toFixed(6);

      // Update or create marker
      if (marker) {
        marker.setLngLat([lng, lat]);
      } else {
        marker = new mapboxgl.Marker({
          draggable: true,
          color: "#667eea",
        })
          .setLngLat([lng, lat])
          .addTo(map);

        // Handle marker drag
        marker.on("dragend", function () {
          const lngLat = marker.getLngLat();
          updateLocation(lngLat);
        });
      }

      console.log("Location updated:", lat, lng);
    }

    // If editing with existing coordinates, show marker
    if (initialLat && initialLng) {
      updateLocation({ lng: initialLng, lat: initialLat });
    }

    // Handle map clicks
    map.on("click", function (e) {
      updateLocation(e.lngLat);
    });

    // Handle geocoder result (when user searches for location)
    geocoder.on("result", function (e) {
      const coords = e.result.geometry.coordinates;
      updateLocation({ lng: coords[0], lat: coords[1] });

      // Also update the location text field if empty
      const locationInput = document.getElementById("id_location");
      if (locationInput && !locationInput.value) {
        locationInput.value = e.result.place_name;
      }
    });

    console.log("Event location picker initialized successfully");
  } catch (error) {
    console.error("Error initializing event location picker:", error);
    mapDiv.innerHTML = '<div class="map-loading">⚠️ Failed to load map</div>';
  }
});
