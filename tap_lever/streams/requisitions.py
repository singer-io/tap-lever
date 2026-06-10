"""Requisitions stream for the Lever tap."""

import singer

from tap_lever.streams.base import TimeRangeStream

LOGGER = singer.get_logger()  # noqa


class RequisitionStream(TimeRangeStream):
    """All requisitions in the Lever account, synced incrementally by created_at."""

    API_METHOD = 'GET'
    TABLE = 'requisitions'
    KEY_PROPERTIES = ['id']
    RANGE_FIELD = 'created_at'

    @property
    def path(self):
        """Return the API path for requisitions."""
        return '/requisitions'
