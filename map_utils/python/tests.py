# map_utils/python/tests.py
from django.test import TestCase, override_settings
from unittest.mock import patch, Mock
import requests
from map_utils.python.utils import geocode_address, get_static_map_url


@override_settings(MAPBOX_ACCESS_TOKEN="test_token_12345")
class GeocodeAddressTests(TestCase):
    """Test the geocode_address function with various scenarios."""

    @patch("map_utils.python.utils.requests.get")
    def test_successful_geocoding(self, mock_get):
        """Test successful geocoding returns [longitude, latitude]."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "features": [
                {
                    "geometry": {
                        "coordinates": [-73.9857, 40.7484]  # Times Square
                    }
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = geocode_address("123 Main St, New York, NY 10001")

        self.assertEqual(result, [-73.9857, 40.7484])
        mock_get.assert_called_once()
        # Verify correct API endpoint was called
        call_args = mock_get.call_args
        self.assertIn("mapbox.com/geocoding", call_args[0][0])

    @patch("map_utils.python.utils.requests.get")
    def test_no_results_found(self, mock_get):
        """Test geocoding returns None when no results found."""
        mock_response = Mock()
        mock_response.json.return_value = {"features": []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = geocode_address("Invalid Address XYZ123")

        self.assertIsNone(result)

    @patch("map_utils.python.utils.requests.get")
    def test_timeout_error(self, mock_get):
        """Test geocoding returns None on timeout."""
        mock_get.side_effect = requests.exceptions.Timeout("Connection timeout")

        result = geocode_address("123 Main St, New York, NY")

        self.assertIsNone(result)

    @patch("map_utils.python.utils.requests.get")
    def test_request_exception(self, mock_get):
        """Test geocoding returns None on request exception."""
        mock_get.side_effect = requests.exceptions.RequestException("Network error")

        result = geocode_address("123 Main St, New York, NY")

        self.assertIsNone(result)

    @patch("map_utils.python.utils.requests.get")
    def test_http_error(self, mock_get):
        """Test geocoding returns None on HTTP error (4xx/5xx)."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "404 Not Found"
        )
        mock_get.return_value = mock_response

        result = geocode_address("123 Main St, New York, NY")

        self.assertIsNone(result)

    @patch("map_utils.python.utils.requests.get")
    def test_malformed_response_keyerror(self, mock_get):
        """Test geocoding returns None when response has unexpected structure."""
        mock_response = Mock()
        mock_response.json.return_value = {"unexpected_key": "value"}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = geocode_address("123 Main St, New York, NY")

        self.assertIsNone(result)

    @patch("map_utils.python.utils.requests.get")
    def test_malformed_response_indexerror(self, mock_get):
        """Test geocoding returns None when features array is malformed."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "features": [{"geometry": {}}]  # Missing coordinates
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = geocode_address("123 Main St, New York, NY")

        self.assertIsNone(result)

    @patch("map_utils.python.utils.requests.get")
    def test_json_value_error(self, mock_get):
        """Test geocoding returns None when JSON parsing fails."""
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = geocode_address("123 Main St, New York, NY")

        self.assertIsNone(result)

    @override_settings(MAPBOX_ACCESS_TOKEN="")
    def test_missing_mapbox_token(self):
        """Test geocoding returns None when MAPBOX_ACCESS_TOKEN is not configured."""
        result = geocode_address("123 Main St, New York, NY")

        self.assertIsNone(result)

    @override_settings(MAPBOX_ACCESS_TOKEN=None)
    def test_none_mapbox_token(self):
        """Test geocoding returns None when MAPBOX_ACCESS_TOKEN is None."""
        result = geocode_address("123 Main St, New York, NY")

        self.assertIsNone(result)

    @patch("map_utils.python.utils.requests.get")
    def test_api_parameters(self, mock_get):
        """Test that correct API parameters are passed."""
        mock_response = Mock()
        mock_response.json.return_value = {"features": []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        geocode_address("123 Main St, New York, NY 10001")

        call_args = mock_get.call_args
        params = call_args[1]["params"]
        self.assertEqual(params["access_token"], "test_token_12345")
        self.assertEqual(params["limit"], 1)
        self.assertEqual(params["types"], "address,place")
        self.assertEqual(call_args[1]["timeout"], 5)

    @patch("map_utils.python.utils.requests.get")
    def test_url_encoding(self, mock_get):
        """Test that addresses with special characters are properly URL-encoded."""
        mock_response = Mock()
        mock_response.json.return_value = {"features": []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        geocode_address("123 O'Brien St, New York, NY")

        call_args = mock_get.call_args
        url = call_args[0][0]
        # URL should contain encoded characters
        self.assertIn("mapbox.com/geocoding", url)
        # Original spaces/special chars should be encoded
        self.assertNotIn(" ", url.split("?")[0])  # Check URL path only


@override_settings(MAPBOX_ACCESS_TOKEN="test_token_12345")
class GetStaticMapUrlTests(TestCase):
    """Test the get_static_map_url function."""

    def test_successful_static_map_url_generation(self):
        """Test successful generation of static map URL."""
        url = get_static_map_url(-73.9857, 40.7484)

        self.assertIsNotNone(url)
        self.assertIn("api.mapbox.com/styles/v1/mapbox/streets-v11/static", url)
        self.assertIn("-73.9857", url)
        self.assertIn("40.7484", url)
        self.assertIn("access_token=test_token_12345", url)

    def test_custom_dimensions(self):
        """Test static map URL with custom width and height."""
        url = get_static_map_url(-73.9857, 40.7484, width=800, height=600)

        self.assertIn("800x600", url)

    def test_custom_zoom_level(self):
        """Test static map URL with custom zoom level."""
        url = get_static_map_url(-73.9857, 40.7484, zoom=18)

        self.assertIn(",18/", url)  # zoom level in URL format

    def test_default_parameters(self):
        """Test static map URL uses default parameters when not specified."""
        url = get_static_map_url(-73.9857, 40.7484)

        # Default: 600x400, zoom 14
        self.assertIn("600x400", url)
        self.assertIn(",14/", url)

    def test_marker_pin_included(self):
        """Test that a red marker pin is included in the URL."""
        url = get_static_map_url(-73.9857, 40.7484)

        # Red pin marker format: pin-s+ff0000(lon,lat)
        self.assertIn("pin-s+ff0000", url)
        self.assertIn("-73.9857", url)
        self.assertIn("40.7484", url)

    @override_settings(MAPBOX_ACCESS_TOKEN="")
    def test_missing_mapbox_token_returns_none(self):
        """Test that missing MAPBOX_ACCESS_TOKEN returns None."""
        url = get_static_map_url(-73.9857, 40.7484)

        self.assertIsNone(url)

    @override_settings(MAPBOX_ACCESS_TOKEN=None)
    def test_none_mapbox_token_returns_none(self):
        """Test that None MAPBOX_ACCESS_TOKEN returns None."""
        url = get_static_map_url(-73.9857, 40.7484)

        self.assertIsNone(url)

    def test_negative_and_positive_coordinates(self):
        """Test with various coordinate combinations."""
        # New York (negative lon, positive lat)
        url_ny = get_static_map_url(-73.9857, 40.7484)
        self.assertIn("-73.9857", url_ny)
        self.assertIn("40.7484", url_ny)

        # Sydney (positive lon, negative lat)
        url_sydney = get_static_map_url(151.2093, -33.8688)
        self.assertIn("151.2093", url_sydney)
        self.assertIn("-33.8688", url_sydney)

    def test_zero_coordinates(self):
        """Test with zero coordinates (Null Island)."""
        url = get_static_map_url(0, 0)

        self.assertIsNotNone(url)
        # Coordinates should be in URL (note: "0" might appear as "0.0" or just "0")
        self.assertIn("pin-s+ff0000(0", url)
