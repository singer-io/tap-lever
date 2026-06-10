"""Candidates stream for the Lever tap."""

import singer

from tap_lever.streams.base import TimeRangeStream

LOGGER = singer.get_logger()  # noqa


class CandidateStream(TimeRangeStream):
    """All candidates in the Lever account, synced incrementally by updated_at."""

    API_METHOD = 'GET'
    TABLE = 'candidates'
    KEY_PROPERTIES = ['id']

    CACHE_RESULTS = True

    @property
    def path(self):
        """Return the API path for candidates."""
        return '/candidates'
