import backoff
import requests
import singer
import singer.metrics

from requests.exceptions import ConnectionError

LOGGER = singer.get_logger()  # noqa


class Server5xxError(Exception):
    pass


class Server429Error(Exception):
    pass


class OffsetInvalidException(Exception):
    pass


class LeverClient:

    MAX_TRIES = 5

    def __init__(self, config):
        self.config = config

    # 429 Too Many Requests: Apply backoff strategy to handle rate limiting.
    # Lever API uses a token bucket algorithm to enforce rate limits, capping requests per second.
    # Implementing exponential backoff ensures compliance with these limits and avoids request throttling.
    # Reference: https://hire.lever.co/developer/documentation#rate-limits
    @backoff.on_exception(
        backoff.expo,
        (Server5xxError, Server429Error, ConnectionError),
        max_tries=MAX_TRIES,
        factor=2,
    )
    def make_request(self, url, method, params=None, body=None):
        LOGGER.info("Making {} request to {} ({})".format(method, url, params))

        response = requests.request(
            method,
            url,
            headers={"Content-Type": "application/json"},
            auth=(self.config["token"], ""),
            params=params,
            json=body,
        )

        try:
            response_json = response.json()
        except:
            response_json = None

        if response_json and "Invalid offset token" in response_json.get("message", ""):
            raise OffsetInvalidException(response.text)

        if 500 <= response.status_code < 600:
            msg = (
                f"Server error {response.status_code}"
                f"{': ' + response.text if response.text else ''}"
            )
            raise Server5xxError(msg)
        elif response.status_code == 429:
            raise Server429Error('Rate limit exceeded')
        elif response.status_code != 200:
            raise RuntimeError(response.text)

        return response.json()

