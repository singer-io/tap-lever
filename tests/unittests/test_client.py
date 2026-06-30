import unittest
from unittest.mock import MagicMock, patch

from tap_lever.client import LeverClient, LeverForbiddenError, LeverUnauthorizedError

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


class TestVerifyCredentials(unittest.TestCase):
    @patch("tap_lever.client.requests.request")
    def test_verify_credentials_succeeds_on_200(self, mock_request):
        """verify_credentials does not raise when the API returns 200."""
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {"data": [], "next": None}
        mock_request.return_value = response

        client = LeverClient(default_config)
        client.verify_credentials()  # should not raise

    @patch("tap_lever.client.requests.request")
    def test_verify_credentials_raises_on_401(self, mock_request):
        """verify_credentials raises LeverUnauthorizedError on HTTP 401."""
        response = MagicMock()
        response.status_code = 401
        response.text = "Unauthorized"
        response.json.return_value = {}
        mock_request.return_value = response

        client = LeverClient(default_config)
        with self.assertRaises(LeverUnauthorizedError) as ctx:
            client.verify_credentials()

        self.assertIn("401", str(ctx.exception))
        self.assertIn("credentials", str(ctx.exception).lower())

    @patch("tap_lever.client.requests.request")
    def test_verify_credentials_raises_on_403_not_authorized(self, mock_request):
        """verify_credentials raises LeverUnauthorizedError when Lever returns
        403 with code='NotAuthorized' (invalid API key)."""
        response = MagicMock()
        response.status_code = 403
        response.text = '{"code":"NotAuthorized","message":"Authentication incorrect."}'
        response.json.return_value = {"code": "NotAuthorized", "message": "Authentication incorrect."}
        mock_request.return_value = response

        client = LeverClient(default_config)
        with self.assertRaises(LeverUnauthorizedError) as ctx:
            client.verify_credentials()

        self.assertIn("credentials", str(ctx.exception).lower())

    @patch("tap_lever.client.requests.request")
    def test_verify_credentials_hits_users_endpoint(self, mock_request):
        """verify_credentials probes the /users endpoint."""
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {"data": [], "next": None}
        mock_request.return_value = response

        client = LeverClient(default_config)
        client.verify_credentials()

        # requests.request is called positionally: (method, url, ...)
        call_args = mock_request.call_args
        url = call_args.args[1] if call_args.args else call_args.kwargs.get("url", "")
        self.assertIn("/users", url)

    @patch("tap_lever.client.requests.request")
    def test_verify_credentials_does_not_raise_on_403(self, mock_request):
        """verify_credentials does not raise when /users returns 403.
        Valid credentials with limited permissions should pass credential verification;
        stream-level access is handled separately during discovery.
        """
        response = MagicMock()
        response.status_code = 403
        response.text = "Forbidden"
        response.json.return_value = {}
        mock_request.return_value = response

        client = LeverClient(default_config)
        client.verify_credentials()  # should not raise

    @patch("tap_lever.client.requests.request")
    def test_verify_credentials_does_not_claim_success_on_server_error(self, mock_request):
        """verify_credentials does not raise and does not log success on a 5xx error.
        A transient server error cannot confirm credentials; execution should continue
        with a warning, not a success message.
        """
        response = MagicMock()
        response.status_code = 500
        response.text = "Internal Server Error"
        response.json.return_value = {}
        mock_request.return_value = response

        import logging
        with self.assertLogs("root", level="WARNING") as log_ctx:
            client = LeverClient(default_config)
            client.verify_credentials()  # should not raise

        log_output = "\n".join(log_ctx.output)
        self.assertIn("transient error", log_output.lower())
        self.assertNotIn("verified successfully", log_output.lower())
