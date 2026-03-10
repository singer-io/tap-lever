import unittest
from unittest.mock import MagicMock, patch

from tap_lever.client import LeverClient

default_config = {
    "token": "dummy_api_token"
}


class TestClient(unittest.TestCase):
    @patch("tap_lever.client.requests.request")
    def test_make_request_returns_json_with_auth(self, mock_request):
        """make_request sends auth header and returns parsed JSON."""
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {"data": [{"id": 1}], "next": None}
        mock_request.return_value = response

        client = LeverClient(default_config)
        result = client.make_request(
            "http://example.com", "GET", params={"limit": 100}
        )

        self.assertIn("data", result)
        self.assertEqual(len(result["data"]), 1)

        mock_request.assert_called_once()
        call_kwargs = mock_request.call_args.kwargs
        self.assertEqual(call_kwargs["auth"], ("dummy_api_token", ""))

    @patch("tap_lever.client.requests.request")
    def test_make_request_passes_params(self, mock_request):
        """make_request forwards query params to requests.request."""
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {"data": [], "next": None}
        mock_request.return_value = response

        client = LeverClient(default_config)
        params = {"limit": 100, "offset": "abc123"}
        client.make_request("http://example.com", "GET", params=params)

        call_kwargs = mock_request.call_args.kwargs
        self.assertEqual(call_kwargs["params"], params)
