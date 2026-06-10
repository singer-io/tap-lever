"""Users stream for the Lever tap."""

import singer

from tap_lever.streams.base import BaseStream

LOGGER = singer.get_logger()  # noqa


class UsersStream(BaseStream):
    """All users in the Lever account."""

    API_METHOD = "GET"
    TABLE = "users"

    @property
    def path(self):
        """Return the API path for users."""
        return "/users"
