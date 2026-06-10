"""Stages stream for the Lever tap."""

import singer

from tap_lever.streams.base import BaseStream

LOGGER = singer.get_logger()  # noqa


class StagesStream(BaseStream):
    """All pipeline stages in the Lever account."""

    API_METHOD = 'GET'
    TABLE = 'stages'
    KEY_PROPERTIES = ['id']

    @property
    def path(self):
        """Return the API path for stages."""
        return '/stages'
