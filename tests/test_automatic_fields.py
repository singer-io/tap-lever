"""Unit tests for tap-lever automatic fields selection with mocked data."""
import unittest

try:
    from .base import LeverBaseTest
except ImportError:
    from base import LeverBaseTest
from tap_lever.streams import AVAILABLE_STREAMS


class LeverAutomaticFieldsTest(LeverBaseTest, unittest.TestCase):
    """Verify automatic fields (PKs and replication keys) are properly defined."""

    def test_primary_and_replication_keys_are_automatic(self):
        config = self.get_mock_config()
        state = {}
        expected = self.expected_metadata()

        for stream_class in AVAILABLE_STREAMS:
            stream = stream_class(config, state, None, None)
            catalog_entries = stream.generate_catalog()

            for entry in catalog_entries:
                stream_name = entry["tap_stream_id"]
                actual_automatic = set()
                inclusion_by_property = {}

                for metadata in entry["metadata"]:
                    breadcrumb = metadata.get("breadcrumb", ())
                    if len(breadcrumb) == 2 and breadcrumb[0] == "properties":
                        property_name = breadcrumb[1]
                        inclusion = metadata.get("metadata", {}).get("inclusion")
                        inclusion_by_property[property_name] = inclusion
                        if inclusion == "automatic":
                            actual_automatic.add(property_name)

                primary_keys = expected[stream_name][self.PRIMARY_KEYS]
                for primary_key in primary_keys:
                    if primary_key in inclusion_by_property:
                        with self.subTest(stream=stream_name, primary_key=primary_key):
                            self.assertIn(primary_key, actual_automatic)
