from tap_lever.streams.base import BaseStream


class FeedbackTemplatesStream(BaseStream):
    API_METHOD = 'GET'
    TABLE = 'feedback_templates'

    @property
    def path(self):
        return '/feedback_templates'
