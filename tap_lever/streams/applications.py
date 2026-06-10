"""Candidate and opportunity applications streams for the Lever tap."""

import singer

from tap_lever.streams import cache as stream_cache
from tap_lever.streams.base import BaseStream

LOGGER = singer.get_logger()  # noqa


class CandidateApplicationsStream(BaseStream):
    """Applications belonging to a specific candidate."""

    API_METHOD = "GET"
    TABLE = "candidate_applications"
    PARENT = "candidates"

    @property
    def path(self):
        """Return the path template for candidate applications."""
        return "/candidates/{candidate_id}/applications"

    def get_url(self, candidate):  # noqa: arguments-differ
        """Return the fully-formed URL for *candidate*'s applications."""
        _path = self.path.format(candidate_id=candidate)
        return f"https://api.lever.co/v1{_path}"

    def sync_data(self):
        """Sync applications for every cached candidate."""
        candidates = stream_cache.get("candidates")
        LOGGER.info("Found %s candidates in cache", len(candidates))

        params = self.get_params(_next=None)
        for i, candidate in enumerate(candidates):
            LOGGER.info(
                "Fetching applications for candidate %s of %s",
                i + 1,
                len(candidates),
            )
            candidate_id = candidate["id"]
            url = self.get_url(candidate_id)
            self.sync_paginated(url, params)


class OpportunityApplicationsStream(BaseStream):
    """Applications belonging to a specific opportunity."""

    API_METHOD = "GET"
    TABLE = "opportunity_applications"
    PARENT = "opportunities"

    @property
    def path(self):
        """Return the path template for opportunity applications."""
        return "/opportunities/{opportunity_id}/applications"

    def get_url(self, opportunity):  # noqa: arguments-differ
        """Return the fully-formed URL for *opportunity*'s applications."""
        _path = self.path.format(opportunity_id=opportunity)
        return f"https://api.lever.co/v1{_path}"

    def sync_data(self, opportunity_id):  # noqa: arguments-differ
        """Sync applications for the given *opportunity_id*."""
        params = self.get_params(_next=None)
        url = self.get_url(opportunity_id)
        self.sync_paginated(url, params)
