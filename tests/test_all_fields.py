"""Unit tests for tap-lever all fields replication with mocked data."""
import unittest

try:
    from .base import LeverBaseTest
except ImportError:
    from base import LeverBaseTest

from tap_lever.streams import AVAILABLE_STREAMS


class LeverAllFieldsTest(LeverBaseTest, unittest.TestCase):

    def test_all_stream_schemas_generate_valid_records(self):
        """Test that all expected streams have valid schemas with properties."""

        expected = self.expected_metadata()
        for stream_class in AVAILABLE_STREAMS:
            stream_name = stream_class.TABLE
            with self.subTest(stream=stream_name):
                schema = self._load_schema(stream_name)
                record = self._generate_value(schema, date_value="2025-02-01T00:00:00Z")

                self.assertIsInstance(record, dict)
                replication_keys = expected[stream_name][self.REPLICATION_KEYS]
                for replication_key in replication_keys:
                    if replication_key in schema.get("properties", {}):
                        self.assertIn(replication_key, record)
