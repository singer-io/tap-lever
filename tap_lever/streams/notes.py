import singer
from tap_lever.streams.base import ChildAsync

LOGGER = singer.get_logger()


class OpportunityNotesStream(ChildAsync):
    API_METHOD = "GET"
    TABLE = "opportunity_notes"

    @property
    def path(self):
        return "/opportunities/{opportunity_id}/notes"

    def get_url(self, opportunity):
        _path = self.path.format(opportunity_id=opportunity)
        return "https://api.lever.co/v1{}".format(_path)

