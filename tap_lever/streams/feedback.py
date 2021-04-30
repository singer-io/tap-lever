from tap_lever.streams.base import ChildAsync


class OpportunityFeedbackStream(ChildAsync):
    API_METHOD = "GET"
    TABLE = "opportunity_feedback"

    @property
    def path(self):
        return "/opportunities/{opportunity_id}/feedback"

    def get_url(self, opportunity):
        _path = self.path.format(opportunity_id=opportunity)
        return "https://api.lever.co/v1{}".format(_path)
