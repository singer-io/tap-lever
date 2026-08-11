"""Unit tests for tap-lever stream discovery with mocked data."""
import unittest
from unittest.mock import MagicMock, patch

try:
    from .base import LeverBaseTest
except ImportError:
    from base import LeverBaseTest

from tap_lever.client import LeverForbiddenError
from tap_lever.discover import discover
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


class LeverDiscoveryExclusionTest(LeverBaseTest, unittest.TestCase):
    """Integration tests for stream exclusion during discovery.

    These tests exercise the full discover() pipeline with mocked check_access()
    to verify that unauthorized streams (and their children) are excluded from
    the returned catalog while authorized streams remain present.
    """

    def _run_discover(self, access_fn):
        """Run discover() with a custom check_access side-effect and return catalog."""
        client = MagicMock()
        config = self.get_mock_config()
        with patch("tap_lever.streams.base.BaseStream.check_access", access_fn):
            return discover(client, config, {}, AVAILABLE_STREAMS)

    # ── helpers ────────────────────────────────────────────────────────────────

    @staticmethod
    def _stream_ids(catalog):
        return {s["tap_stream_id"] for s in catalog["streams"]}

    # ── tests ──────────────────────────────────────────────────────────────────

    def test_all_streams_accessible_catalog_is_complete(self):
        """When every stream is accessible the catalog contains all streams."""
        catalog = self._run_discover(lambda self: True)
        stream_ids = self._stream_ids(catalog)
        expected = {s.TABLE for s in AVAILABLE_STREAMS}
        self.assertEqual(stream_ids, expected)

    def test_inaccessible_parent_excluded_from_catalog(self):
        """A parent stream blocked by 403 does not appear in the catalog."""
        def access(self):
            return self.TABLE != "candidates"

        catalog = self._run_discover(access)
        self.assertNotIn("candidates", self._stream_ids(catalog))

    def test_inaccessible_parent_children_excluded_from_catalog(self):
        """Children of a blocked parent stream are also excluded from the catalog."""
        def access(self):
            return self.TABLE != "candidates"

        catalog = self._run_discover(access)
        stream_ids = self._stream_ids(catalog)
        candidate_children = {
            s.TABLE for s in AVAILABLE_STREAMS if s.PARENT == "candidates"
        }
        for child in candidate_children:
            self.assertNotIn(child, stream_ids, f"child '{child}' should be excluded")

    def test_accessible_streams_unaffected_when_one_parent_blocked(self):
        """Streams unrelated to the blocked parent still appear in the catalog."""
        def access(self):
            return self.TABLE != "candidates"

        catalog = self._run_discover(access)
        stream_ids = self._stream_ids(catalog)
        # All non-candidate streams should still be present
        unrelated = {
            s.TABLE for s in AVAILABLE_STREAMS
            if s.TABLE != "candidates" and s.PARENT != "candidates"
        }
        for table in unrelated:
            self.assertIn(table, stream_ids, f"stream '{table}' should still be included")

    def test_multiple_inaccessible_parents_all_excluded(self):
        """Multiple blocked parent streams and all their children are excluded."""
        blocked = {"candidates", "opportunities"}

        def access(self):
            return self.TABLE not in blocked

        catalog = self._run_discover(access)
        stream_ids = self._stream_ids(catalog)

        blocked_with_children = blocked | {
            s.TABLE for s in AVAILABLE_STREAMS if s.PARENT in blocked
        }
        for table in blocked_with_children:
            self.assertNotIn(table, stream_ids, f"'{table}' should be excluded")

    def test_all_inaccessible_raises_lever_forbidden_error(self):
        """When no parent stream is accessible, LeverForbiddenError is raised."""
        def access(self):
            return bool(self.PARENT)  # children pass, all parents fail

        with self.assertRaises(LeverForbiddenError):
            self._run_discover(access)

    def test_catalog_entries_have_required_fields_after_exclusion(self):
        """Catalog entries for accessible streams are well-formed after exclusion."""
        def access(self):
            return self.TABLE != "candidates"

        catalog = self._run_discover(access)
        for entry in catalog["streams"]:
            with self.subTest(stream=entry["tap_stream_id"]):
                self.assertIn("tap_stream_id", entry)
                self.assertIn("schema", entry)
                self.assertIn("key_properties", entry)
                self.assertIn("forced-replication-method", entry)
                self.assertIn("metadata", entry)
