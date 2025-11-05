import requests
from django.conf import settings


def geocode_address(address):
    """
    Convert an address in str format to latitude/longitude coordinates using Mapbox Geocoding API.
    Returns:
        list or None: [longitude, latitude] if successful, None if geocoding fails
    
    """
    # Check if Mapbox token is configured
    if not settings.MAPBOX_ACCESS_TOKEN:
        print("Warning: MAPBOX_ACCESS_TOKEN not configured")
        return None
    
    # Build the Mapbox Geocoding API URL
    # Format: https://api.mapbox.com/geocoding/v5/mapbox.places/{search_text}.json
    base_url = "https://api.mapbox.com/geocoding/v5/mapbox.places"
    encoded_address = requests.utils.quote(address)  # URL-encode the address

    # url -> base_url + encoded_address
    url = f"{base_url}/{encoded_address}.json"
    
    # API parameters
    params = {
        'access_token': settings.MAPBOX_ACCESS_TOKEN,
        'limit': 1,  # Only return the best matching result
        'types': 'address,place',  # Focus on addresses and places
    }
    
    try:
        # Make HTTP GET request to Mapbox API
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()  # Raise exception for 4xx/5xx status codes
        
        # Parse JSON response
        data = response.json()
        
        # Check if we got valid results
        if data.get('features') and len(data['features']) > 0:
            # Extract coordinates from the first (best) result
            # Format: features[0].geometry.coordinates = [longitude, latitude]
            coordinates = data['features'][0]['geometry']['coordinates']
            return coordinates  # [lng, lat]
        
        # No results found for this address
        print(f"No geocoding results found for address: {address}")
        return None
        
    except requests.exceptions.Timeout:
        print(f"Geocoding timeout for address: {address}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Geocoding request error: {e}")
        return None
    except (KeyError, IndexError, ValueError) as e:
        print(f"Geocoding response parsing error: {e}")
        return None
    

def get_static_map_url(longitude, latitude, width=600, height=400, zoom=14):
    """
    Generate a static map image URL for a given location.
    
    Args:
        longitude (float): Longitude coordinate
        latitude (float): Latitude coordinate
        width (int): Image width in pixels
        height (int): Image height in pixels
        zoom (int): Zoom level (0-22, where 14 is neighborhood level)
    
    Returns:
        str: URL to static map image
    
    Example:
    --------
    >>> get_static_map_url(-73.9876, 40.7589)
    'https://api.mapbox.com/styles/v1/mapbox/streets-v11/static/...'
    """
    if not settings.MAPBOX_ACCESS_TOKEN:
        return None
    
    # Mapbox Static Images API format
    # https://api.mapbox.com/styles/v1/{username}/{style_id}/static/{overlay}/{lon},{lat},{zoom}/{width}x{height}
    
    # Add a red marker at the location
    marker = f"pin-s+ff0000({longitude},{latitude})"
    
    url = (
        f"https://api.mapbox.com/styles/v1/mapbox/streets-v11/static/"
        f"{marker}/{longitude},{latitude},{zoom}/{width}x{height}"
        f"?access_token={settings.MAPBOX_ACCESS_TOKEN}"
    )
    
    return url