/**
 * Item Location Picker - Interactive Map for Selecting Marketplace Item Pickup Location
 *
 * This script initializes a Mapbox map that allows users to:
 * 1. Click on the map to set item pickup location
 * 2. Search for addresses using the geocoder
 * 3. Auto-geocode when address fields are filled
 * 4. Drag the marker to adjust location
 * 5. Automatically update hidden lat/lng form fields
 */

document.addEventListener("DOMContentLoaded", function () {
  const mapDiv = document.getElementById("item-location-map");

  if (!mapDiv) {
    return; // Map div not found, exit
  }

  const token = mapDiv.dataset.mapboxToken;

  if (!token || token === "None" || token === "") {
    console.warn("Mapbox token not configured");
    mapDiv.innerHTML =
      '<div class="map-loading">📍 Map service not configured. Location will be geocoded automatically when you submit the form.</div>';
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

  // Get address form fields
  const streetInput = document.getElementById("id_street_address");
  const cityInput = document.getElementById("id_city");
  const zipcodeInput = document.getElementById("id_zipcode");

  // Check if editing existing item with coordinates
  const initialLat = latInput.value ? parseFloat(latInput.value) : null;
  const initialLng = lngInput.value ? parseFloat(lngInput.value) : null;

  // Default center (New York City - center of NYC)
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
      container: "item-location-map",
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
      placeholder: "Search for pickup location...",
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
          color: "#3b82f6", // Blue color for marketplace
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

      // Optionally populate address fields from geocoder result
      const context = e.result.context || [];
      const placeName = e.result.place_name;

      // Try to extract street address
      if (e.result.address && e.result.text) {
        const fullStreet = `${e.result.address} ${e.result.text}`;
        if (streetInput && !streetInput.value) {
          streetInput.value = fullStreet;
        }
      }

      // Extract city from context
      if (cityInput && !cityInput.value) {
        const cityContext = context.find((c) => c.id.startsWith("place."));
        if (cityContext) {
          cityInput.value = cityContext.text;
        }
      }

      // Extract zipcode from context
      if (zipcodeInput && !zipcodeInput.value) {
        const zipContext = context.find((c) => c.id.startsWith("postcode."));
        if (zipContext) {
          zipcodeInput.value = zipContext.text;
        }
      }
    });

    // Auto-geocode when address fields are filled/changed
    let geocodeTimeout = null;

    function autoGeocodeAddress() {
      clearTimeout(geocodeTimeout);

      geocodeTimeout = setTimeout(async () => {
        if (!streetInput || !cityInput || !zipcodeInput) {
          return;
        }

        const street = streetInput.value.trim();
        const city = cityInput.value.trim();
        const zipcode = zipcodeInput.value.trim();

        // Only geocode if we have at least street and city
        if (!street || !city) {
          console.log("Insufficient address information for auto-geocoding");
          return;
        }

        const fullAddress = `${street}, ${city}, NY ${zipcode}`;
        console.log("Auto-geocoding address:", fullAddress);

        try {
          const response = await fetch(
            `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(
              fullAddress
            )}.json?access_token=${mapboxgl.accessToken}&limit=1&proximity=-73.935242,40.73061`
          );

          if (!response.ok) {
            throw new Error("Geocoding request failed");
          }

          const data = await response.json();

          if (data.features && data.features.length > 0) {
            const coords = data.features[0].geometry.coordinates;
            updateLocation({ lng: coords[0], lat: coords[1] });

            // Center map on the geocoded location
            map.flyTo({
              center: coords,
              zoom: 15,
              essential: true,
            });

            console.log("Auto-geocoding successful:", coords);
          } else {
            console.warn("No geocoding results found for:", fullAddress);
          }
        } catch (error) {
          console.error("Auto-geocoding error:", error);
        }
      }, 1000); // Debounce for 1 second
    }

    // Add event listeners to address fields
    if (streetInput) {
      streetInput.addEventListener("blur", autoGeocodeAddress);
    }
    if (cityInput) {
      cityInput.addEventListener("blur", autoGeocodeAddress);
    }
    if (zipcodeInput) {
      zipcodeInput.addEventListener("blur", autoGeocodeAddress);
    }

    console.log("Item location picker initialized successfully");
  } catch (error) {
    console.error("Error initializing item location picker:", error);
    mapDiv.innerHTML = '<div class="map-loading">⚠️ Failed to load map</div>';
  }
});
