import unittest
from unittest.mock import patch, MagicMock
import requests
import time

from tap_lever.client import (
    LeverClient,
    Server5xxError,
    Server429Error,
    OffsetInvalidException,
)


class TestLeverClient(unittest.TestCase):
    def setUp(self):
        self.config = {"token": "dummy_token"}
        self.client = LeverClient(self.config)
        # Patch time.sleep globally so backoff retries don't actually delay tests
        patcher = patch("time.sleep", return_value=None)
        self.addCleanup(patcher.stop)
        patcher.start()

    @patch("requests.request")
    def test_successful_make_request(self, mock_request):
        """make_request should return parsed JSON on HTTP 200."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"key": "value"}
        mock_request.return_value = mock_resp

        result = self.client.make_request(
            "http://example.com", "GET", params={"a": 1}, body={"b": 2}
        )
        self.assertEqual(result, {"key": "value"})
        mock_request.assert_called_once_with(
            "GET",
            "http://example.com",
            headers={"Content-Type": "application/json"},
            auth=(self.config["token"], ""),
            params={"a": 1},
            json={"b": 2},
        )

    @patch("requests.request")
    def test_offset_invalid_exception(self, mock_request):
        """make_request should raise OffsetInvalidException when response message indicates invalid offset."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"message": "Invalid offset token: bad"}
        mock_resp.text = "bad token"
        mock_request.return_value = mock_resp

        with self.assertRaises(OffsetInvalidException) as cm:
            self.client.make_request("url", "POST")
        self.assertIn("bad token", str(cm.exception))

    @patch("requests.request")
    def test_server5xx_retry_success(self, mock_request):
        """make_request should retry on 5xx errors and succeed when a later call returns 200."""
        resp500 = MagicMock(
            status_code=500, json=MagicMock(return_value={}), headers={}
        )
        resp200 = MagicMock(
            status_code=200, json=MagicMock(return_value={"ok": True}), headers={}
        )
        mock_request.side_effect = [resp500, resp200]

        result = self.client.make_request("url", "GET")
        self.assertEqual(result, {"ok": True})
        self.assertEqual(mock_request.call_count, 2)

    @patch("requests.request")
    def test_server5xx_max_retries(self, mock_request):
        """make_request should raise Server5xxError after exceeding max retries on 5xx errors."""
        resp500 = MagicMock(
            status_code=500, json=MagicMock(return_value={}), headers={}
        )
        mock_request.return_value = resp500

        with self.assertRaises(Server5xxError) as req_err:
            self.client.make_request("url", "GET")

        self.assertEqual(mock_request.call_count, self.client.MAX_TRIES)
        self.assertIn("Server error", str(req_err.exception))

    @patch("requests.request")
    def test_server429_max_retries(self, mock_request):
        """make_request should raise Server429Error after exceeding max retries on 429 errors."""
        resp429 = MagicMock(
            status_code=429,
            json=MagicMock(return_value={}),
            headers={"X-RateLimit-Reset": "1"},
        )
        mock_request.return_value = resp429

        with self.assertRaises(Server429Error)as req_err:
            self.client.make_request("url", "GET")
        self.assertEqual(mock_request.call_count, self.client.MAX_TRIES)
        self.assertEqual("Rate limit exceeded", str(req_err.exception))
