"""HTTP client for the Lever API with retry and backoff support."""

import backoff
import requests
import singer
import singer.metrics

from requests.exceptions import ConnectionError as RequestsConnectionError

LOGGER = singer.get_logger()  # noqa


class Server5xxError(Exception):
    """Raised when the Lever API returns a 5xx HTTP status code."""


class Server429Error(Exception):
    """Raised when the Lever API returns a 429 (rate-limit) HTTP status code."""


class OffsetInvalidException(Exception):
    """Raised when the Lever API returns an invalid pagination offset."""


class LeverForbiddenError(Exception):
    """Raised when the Lever API returns a 403 Forbidden HTTP status code."""


class LeverClient:
    """Authenticated HTTP client for the Lever API."""

    MAX_TRIES = 5

    def __init__(self, config):
        """Store API configuration for later use in requests."""
        self.config = config

    # 429 Too Many Requests: Apply backoff strategy to handle rate limiting.
    # Lever API uses a token bucket algorithm to enforce rate limits.
    # Reference: https://hire.lever.co/developer/documentation#rate-limits
    @backoff.on_exception(
        backoff.expo,
        (Server5xxError, Server429Error, RequestsConnectionError),
        max_tries=MAX_TRIES,
        factor=2,
    )
    def make_request(self, url, method, params=None, body=None):
        """Send an authenticated request to *url* and return the parsed JSON body."""
        LOGGER.info("Making %s request to %s (%s)", method, url, params)

        response = requests.request(
            method,
            url,
            headers={"Content-Type": "application/json"},
            auth=(self.config["token"], ""),
            params=params,
            json=body,
            timeout=300,
        )

        try:
            response_json = response.json()
        except ValueError:
            response_json = None

        if response_json and "Invalid offset token" in response_json.get("message", ""):
            raise OffsetInvalidException(response.text)

        if 500 <= response.status_code < 600:
            msg = (
                f"Server error {response.status_code}"
                f"{': ' + response.text if response.text else ''}"
            )
            raise Server5xxError(msg)
        if response.status_code == 429:
            raise Server429Error('Rate limit exceeded')
        if response.status_code == 403:
            raise LeverForbiddenError(response.text)
        if response.status_code != 200:
            raise RuntimeError(response.text)

        return response_json
