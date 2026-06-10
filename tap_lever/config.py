"""Configuration helpers for the Lever tap."""

import pytz
import singer
from dateutil.parser import parse

LOGGER = singer.get_logger()  # noqa


def get_config_start_date(config):
    """Parse and return the configured start date as a timezone-aware datetime."""
    return parse(config.get("start_date")).replace(tzinfo=pytz.utc)
