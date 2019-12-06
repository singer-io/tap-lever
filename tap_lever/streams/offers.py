import singer
from tap_lever.streams import cache as stream_cache
from tap_lever.streams.base import BaseStream

LOGGER = singer.get_logger()  # noqa


class CandidateOffersStream(BaseStream):
    API_METHOD = "GET"
    TABLE = "candidate_offers"

    @property
    def path(self):
        return "/candidates/{candidate_id}/offers"

    def get_url(self, candidate):
        _path = self.path.format(candidate_id=candidate)
        return "https://api.lever.co/v1{}".format(_path)

    def sync_data(self):
        candidates = stream_cache.get("candidates")
        LOGGER.info("Found {} candidates in cache".format(len(candidates)))

        params = self.get_params(_next=None)
        for i, candidate in enumerate(candidates):
            LOGGER.info(
                "Fetching offers for candidate {} of {}".format(i + 1, len(candidates))
            )
            candidate_id = candidate["id"]
            url = self.get_url(candidate_id)
            resources = self.sync_paginated(url, params)
