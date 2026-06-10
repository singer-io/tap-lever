"""Postings stream for the Lever tap."""

import singer

from tap_lever.streams.base import BaseStream

LOGGER = singer.get_logger()  # noqa


class PostingsStream(BaseStream):
    """All job postings in the Lever account."""

    API_METHOD = 'GET'
    TABLE = 'postings'

    @property
    def path(self):
        """Return the API path for postings."""
        return '/postings'
