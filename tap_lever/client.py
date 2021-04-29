import requests
import singer
import singer.metrics
import backoff
import functools

LOGGER = singer.get_logger()  # noqa
MAX_ERROR_RETRIES = 10

class OffsetInvalidException(Exception):
    pass


def safe_json_parse(response):
    try:
        return response.json()
    except:
        return None


def leaky_bucket_handler(details):
    LOGGER.info(details)
    LOGGER.info("Received Error -- sleeping for %s seconds",
                details['wait'])


def error_handling(fnc):
    @backoff.on_exception(backoff.expo,
                          Exception,
                          on_backoff=leaky_bucket_handler,
                          max_tries=MAX_ERROR_RETRIES,
                          # No jitter as we want a constant value
                          jitter=None)
    @functools.wraps(fnc)
    def wrapper(*args, **kwargs):
        return fnc(*args, **kwargs)

    return wrapper


class LeverClient:
    MAX_TRIES = 10

    def __init__(self, config):
        self.config = config

    @error_handling
    def make_request(self, url, method, params=None, body=None):
        LOGGER.info("Making {} request to {} ({})".format(method, url, params))

        response = requests.request(
            method,
            url,
            headers={
                'Content-Type': 'application/json'
            },
            auth=(self.config['token'], ''),
            params=params,
            json=body)

        response_json = safe_json_parse(response)
        # NB: Observed - "Invalid offset token: Offset token is invalid for sort"
        if response_json and "Invalid offset token" in response_json.get("message", ""):
            raise OffsetInvalidException(response.text)

        if response.status_code != 200:
            raise RuntimeError(response.text)

        return response.json()
