import backoff
import requests
import singer
import singer.metrics

from requests.exceptions import ConnectionError, HTTPError

RETRY_RATE_LIMIT = 360

LOGGER = singer.get_logger()  # noqa


class Server5xxError(Exception):
    pass


class Server429Error(Exception):
    pass


class OffsetInvalidException(Exception):
    pass

def safe_json_parse(response):
    try:
        return response.json()
    except:
        return None

class LeverClient:

    MAX_TRIES = 5

    def __init__(self, config):
        self._retry_after = RETRY_RATE_LIMIT
        self.config = config

    def _rate_limit_backoff(self):
        """
        Bound wait‐generator: on each retry backoff will call next()
        and sleep for self._retry_after seconds.
        """
        while True:
            yield self._retry_after

    def _make_request_once(self, url, method, params=None, body=None):
        LOGGER.info("Making {} request to {} ({})".format(method, url, params))

        resp = requests.request(
            method,
            url,
            headers={'Content-Type': 'application/json'},
            auth=(self.config['token'], ''),
            params=params,
            json=body,
        )

        response_json = safe_json_parse(resp)

        if response_json and "Invalid offset token" in response_json.get("message", ""):
            raise OffsetInvalidException(resp.text)

        if 500 <= resp.status_code < 600:
            raise Server5xxError()
        elif resp.status_code == 429:
            try:
                self._retry_after = int(
                    float(resp.headers.get("X-RateLimit-Reset", RETRY_RATE_LIMIT))
                )
            except (TypeError, ValueError):
                self._retry_after = RETRY_RATE_LIMIT
            raise Server429Error()
        elif resp.status_code != 200:
            raise RuntimeError(resp.text)

        return resp

    def make_request(self, url, method, params=None, body=None):
        @backoff.on_exception(
            self._rate_limit_backoff,
            Server429Error,
            max_tries=self.MAX_TRIES,
            jitter=None,
        )
        @backoff.on_exception(
            backoff.expo,
            (Server5xxError, ConnectionError),
            max_tries=self.MAX_TRIES,
        )
        def wrapped_call():
            return self._make_request_once(url, method, params, body)

        response = wrapped_call()
        return response.json()
