"""Candidate and opportunity offers streams for the Lever tap."""

import singer

from tap_lever.streams import cache as stream_cache
from tap_lever.streams.base import BaseStream

LOGGER = singer.get_logger()  # noqa


class CandidateOffersStream(BaseStream):
    """Offers belonging to a specific candidate."""

    API_METHOD = "GET"
    TABLE = "candidate_offers"
    PARENT = "candidates"

    @property
    def path(self):
        """Return the path template for candidate offers."""
        return "/candidates/{candidate_id}/offers"

    def get_url(self, candidate):  # noqa: arguments-differ
        """Return the fully-formed URL for *candidate*'s offers."""
        _path = self.path.format(candidate_id=candidate)
        return f"https://api.lever.co/v1{_path}"

    def sync_data(self):
        """Sync offers for every cached candidate."""
        candidates = stream_cache.get("candidates")
        LOGGER.info("Found %s candidates in cache", len(candidates))

        params = self.get_params(_next=None)
        for i, candidate in enumerate(candidates):
            LOGGER.info(
                "Fetching offers for candidate %s of %s", i + 1, len(candidates)
            )
            candidate_id = candidate["id"]
            url = self.get_url(candidate_id)
            self.sync_paginated(url, params)


class OpportunityOffersStream(BaseStream):
    """Offers belonging to a specific opportunity, enriched with the parent opportunity ID."""

    API_METHOD = "GET"
    TABLE = "opportunity_offers"
    PARENT = "opportunities"

    @property
    def path(self):
        """Return the path template for opportunity offers."""
        return "/opportunities/{opportunity_id}/offers"

    def get_url(self, opportunity):  # noqa: arguments-differ
        """Return the fully-formed URL for *opportunity*'s offers."""
        _path = self.path.format(opportunity_id=opportunity)
        return f"https://api.lever.co/v1{_path}"

    # NB: We chose to change this function to NOT call base's
    # sync_paginated since there was a request to add the parent id
    # (opportunityId) to the records, and there was no natural place to do
    # this
    def sync_data(self, opportunity_id):  # noqa: arguments-differ
        """Sync offers for *opportunity_id*, injecting the parent ID into each record."""
        params = self.get_params(_next=None)
        url = self.get_url(opportunity_id)

        transformer = singer.Transformer(singer.UNIX_MILLISECONDS_INTEGER_DATETIME_PARSING)
        with singer.metrics.record_counter(endpoint=self.TABLE) as counter:
            for page in self.paginate(url, params, opportunity_id):
                self.add_parent_id(page, opportunity_id)
                transformed_data = self.get_stream_data(page, transformer)
                singer.write_records(self.TABLE, transformed_data)
                counter.increment(len(page))
        transformer.log_warning()

    def paginate(self, url, params, _opportunity_id):
        """Yield pages of raw offer records from the API."""
        _next = True
        page = 1

        while _next is not None:
            result = self.client.make_request(url, self.API_METHOD, params=params)
            _next = result.get('next')

            yield result['data']

            if _next:
                params['offset'] = _next
            LOGGER.info('Synced page %s for %s', page, self.TABLE)
            page += 1

    def add_parent_id(self, data, opportunity_id):
        """Inject *opportunity_id* into each record in *data*."""
        for rec in data:
            rec['opportunityId'] = opportunity_id
