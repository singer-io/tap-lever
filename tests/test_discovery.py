"""Unit tests for tap-lever stream discovery with mocked data."""
import unittest

try:
    from .base import LeverBaseTest
except ImportError:
    from base import LeverBaseTest

from tap_lever.streams import AVAILABLE_STREAMS


class LeverDiscoveryTest(LeverBaseTest, unittest.TestCase):

    def test_discovery_expected_streams_and_metadata(self):
        """Verify the catalog entry has the expected stream name, key_properties,
        replication method, and replication keys."""
        config = self.get_mock_config()
        state = {}
        expected = self.expected_metadata()

        stream_map = {}
        for stream_class in AVAILABLE_STREAMS:
            stream = stream_class(config, state, None, None)
            for entry in stream.generate_catalog():
                stream_map[entry["tap_stream_id"]] = entry

        # All expected streams must be discovered
        self.assertEqual(set(stream_map.keys()), set(expected.keys()))

        for stream_name, expected_stream in expected.items():
            with self.subTest(stream=stream_name):
                entry = stream_map[stream_name]

                # Verify primary keys
                self.assertEqual(
                    set(entry["key_properties"]),
                    expected_stream[self.PRIMARY_KEYS],
                )

                # Verify replication method
                self.assertEqual(
                    entry["forced-replication-method"],
                    expected_stream[self.REPLICATION_METHOD],
                )

                # Verify replication keys
                actual_replication_keys = set(entry.get("replication_keys", []))
                self.assertEqual(
                    actual_replication_keys,
                    expected_stream[self.REPLICATION_KEYS],
                )

                # Verify empty breadcrumb metadata contains required Singer spec keys
                metadata_map = {
                    tuple(e['breadcrumb']): e['metadata']
                    for e in entry['metadata']
                }
                root_meta = metadata_map.get(())
                self.assertIsNotNone(root_meta, f"{stream_name}: empty breadcrumb entry missing")
                self.assertEqual(
                    set(root_meta.get('table-key-properties', [])),
                    expected_stream[self.PRIMARY_KEYS],
                    f"{stream_name}: table-key-properties mismatch in metadata",
                )
                self.assertEqual(
                    root_meta.get('forced-replication-method'),
                    expected_stream[self.REPLICATION_METHOD],
                    f"{stream_name}: forced-replication-method mismatch in metadata",
                )
                self.assertEqual(
                    set(root_meta.get('valid-replication-keys', [])),
                    expected_stream[self.REPLICATION_KEYS],
                    f"{stream_name}: valid-replication-keys mismatch in metadata",
                )
