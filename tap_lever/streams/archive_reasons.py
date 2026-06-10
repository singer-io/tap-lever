"""Archive reasons stream for the Lever tap."""

import singer

from tap_lever.streams.base import BaseStream

LOGGER = singer.get_logger()  # noqa


class ArchiveReasonsStream(BaseStream):
    """All archive reasons configured in the Lever account."""

    API_METHOD = "GET"
    TABLE = "archive_reasons"

    @property
    def path(self):
        """Return the API path for archive reasons."""
        return "/archive_reasons"
