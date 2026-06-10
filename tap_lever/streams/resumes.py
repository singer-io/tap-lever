"""Candidate and opportunity resumes streams for the Lever tap."""

import singer

from tap_lever.streams import cache as stream_cache
from tap_lever.streams.base import BaseStream

LOGGER = singer.get_logger()  # noqa


class CandidateResumesStream(BaseStream):
    """Resumes belonging to a specific candidate."""

    API_METHOD = "GET"
    TABLE = "candidate_resumes"
    PARENT = "candidates"

    @property
    def path(self):
        """Return the path template for candidate resumes."""
        return "/candidates/{candidate_id}/resumes"

    def get_url(self, candidate):  # noqa: arguments-differ
        """Return the fully-formed URL for *candidate*'s resumes."""
        _path = self.path.format(candidate_id=candidate)
        return f"https://api.lever.co/v1{_path}"

    def sync_data(self):
        """Sync resumes for every cached candidate, tolerating missing-resume API errors."""
        candidates = stream_cache.get("candidates")
        LOGGER.info("Found %s candidates in cache", len(candidates))

        for i, candidate in enumerate(candidates):
            LOGGER.info(
                "Fetching resumes for candidate %s of %s",
                i + 1,
                len(candidates),
            )
            candidate_id = candidate["id"]
            url = self.get_url(candidate_id)
            try:
                self.sync_paginated(url)
            except RuntimeError as exc:
                # There's a bug in the Lever API where a missing resume will result
                # in a ResourceNotFound error instead of returning an empty response
                if "ResourceNotFound" in str(exc):
                    LOGGER.info("Candidate %s does not have resumes", candidate_id)
                else:
                    raise


class OpportunityResumesStream(BaseStream):
    """Resumes belonging to a specific opportunity."""

    API_METHOD = "GET"
    TABLE = "opportunity_resumes"
    PARENT = "opportunities"

    @property
    def path(self):
        """Return the path template for opportunity resumes."""
        return "/opportunities/{opportunity_id}/resumes"

    def get_url(self, opportunity):  # noqa: arguments-differ
        """Return the fully-formed URL for *opportunity*'s resumes."""
        _path = self.path.format(opportunity_id=opportunity)
        return f"https://api.lever.co/v1{_path}"

    def sync_data(self, opportunity_id):  # noqa: arguments-differ
        """Sync resumes for the given *opportunity_id*, tolerating missing-resume API errors."""
        url = self.get_url(opportunity_id)
        try:
            self.sync_paginated(url)
        except RuntimeError as exc:
            # There's a bug in the Lever API where a missing resume will result
            # in a ResourceNotFound error instead of returning an empty response
            if "ResourceNotFound" in str(exc):
                LOGGER.info("Opportunity %s does not have resumes", opportunity_id)
            else:
                raise
