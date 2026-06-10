"""Sources stream for the Lever tap."""

import singer

from tap_lever.streams.base import BaseStream

LOGGER = singer.get_logger()  # noqa


class SourcesStream(BaseStream):
    """All candidate sources in the Lever account."""

    API_METHOD = 'GET'
    TABLE = 'sources'
    KEY_PROPERTIES = ['text']

    @property
    def path(self):
        """Return the API path for sources."""
        return '/sources'
