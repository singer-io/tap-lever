"""Unit tests for tap-lever start date functionality with mocked data."""
import unittest

try:
    from .base import LeverBaseTest
except ImportError:
    from base import LeverBaseTest

from tap_lever.streams.candidates import CandidateStream
from tap_lever.streams.opportunities import OpportunityStream
from tap_lever.streams.requisitions import RequisitionStream
from tap_lever.streams import AVAILABLE_STREAMS
from tap_lever.config import get_config_start_date


class LeverStartDateTest(LeverBaseTest, unittest.TestCase):
    """Verify start_date config is accepted and parsed by streams."""

    def test_get_config_start_date_parses_correctly(self):
        config = {"start_date": "2023-01-01T00:00:00Z"}
        result = get_config_start_date(config)
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2023)
        self.assertEqual(result.month, 1)
        self.assertEqual(result.day, 1)
        self.assertIsNotNone(result.tzinfo)

    def test_time_range_streams_accept_start_date(self):
        """TimeRangeStream streams accept start_date in config."""
        config = {
            "token": "mock_token",
            "start_date": "2023-01-01T00:00:00Z"
        }
        state = {}

        for stream_class in [CandidateStream, OpportunityStream, RequisitionStream]:
            with self.subTest(stream=stream_class.TABLE):
                stream = stream_class(config, state, None, None)
                self.assertIsNotNone(stream)
                self.assertIn("start_date", stream.config)

    def test_all_streams_store_config(self):
        config = self.get_mock_config()
        for stream_class in AVAILABLE_STREAMS:
            with self.subTest(stream=stream_class.TABLE):
                stream = stream_class(config, {}, None, None)
                self.assertIsNotNone(stream.config)
                self.assertIn("start_date", stream.config)
