import singer

from tap_lever.streams.base import BaseStream, ChildAsync
import aiohttp

LOGGER = singer.get_logger()


class OpportunityFormStream(ChildAsync):
    API_METHOD = "GET"
    TABLE = "opportunity_forms"

    @property
    def path(self):
        return "/opportunities/{opportunity_id}/forms"

    def get_url(self, opportunity):
        _path = self.path.format(opportunity_id=opportunity)
        return "https://api.lever.co/v1{}".format(_path)
