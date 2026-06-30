"""Unit tests for tap-lever discovery functionality."""
import unittest
from unittest.mock import MagicMock, patch

from tap_lever.client import LeverForbiddenError
from tap_lever.streams import AVAILABLE_STREAMS
from tap_lever.streams.applications import CandidateApplicationsStream, OpportunityApplicationsStream
from tap_lever.streams.candidates import CandidateStream
from tap_lever.streams.opportunities import OpportunityStream
from tap_lever.streams.offers import CandidateOffersStream, OpportunityOffersStream
from tap_lever.streams.referrals import CandidateReferralsStream, OpportunityReferralsStream
from tap_lever.streams.resumes import CandidateResumesStream, OpportunityResumesStream


class TestLeverDiscovery(unittest.TestCase):

    def test_available_streams_has_all_streams(self):
        """Verify all expected streams are in AVAILABLE_STREAMS."""
        expected_streams = {
            "candidates",
            "opportunities",
            "archive_reasons",
            "candidate_applications",
            "candidate_offers",
            "candidate_referrals",
            "candidate_resumes",
            "opportunity_applications",
            "opportunity_offers",
            "opportunity_referrals",
            "opportunity_resumes",
            "postings",
            "requisitions",
            "sources",
            "stages",
            "users"
        }

        stream_tables = {stream.TABLE for stream in AVAILABLE_STREAMS}
        self.assertEqual(expected_streams, stream_tables)

    def test_candidate_stream_has_correct_properties(self):
        """Verify CandidateStream has expected configuration."""
        config = {"token": "test_token", "start_date": "2020-01-01T00:00:00Z"}
        state = {}
        catalog = MagicMock()
        client = MagicMock()

        stream = CandidateStream(config, state, catalog, client)

        self.assertEqual(stream.TABLE, "candidates")
        self.assertEqual(stream.KEY_PROPERTIES, ["id"])
        self.assertTrue(stream.CACHE_RESULTS)

    def test_opportunity_stream_has_correct_properties(self):
        config = {"token": "test_token", "start_date": "2020-01-01T00:00:00Z"}
        state = {}
        catalog = MagicMock()
        client = MagicMock()

        stream = OpportunityStream(config, state, catalog, client)

        self.assertEqual(stream.TABLE, "opportunities")
        self.assertEqual(stream.KEY_PROPERTIES, ["id"])

    def test_child_streams_have_parent_set(self):
        """Verify child streams have correct PARENT attribute."""

        # Candidate child streams
        self.assertEqual(CandidateApplicationsStream.PARENT, "candidates")
        self.assertEqual(CandidateOffersStream.PARENT, "candidates")
        self.assertEqual(CandidateReferralsStream.PARENT, "candidates")
        self.assertEqual(CandidateResumesStream.PARENT, "candidates")

        # Opportunity child streams
        self.assertEqual(OpportunityApplicationsStream.PARENT, "opportunities")
        self.assertEqual(OpportunityOffersStream.PARENT, "opportunities")
        self.assertEqual(OpportunityReferralsStream.PARENT, "opportunities")
        self.assertEqual(OpportunityResumesStream.PARENT, "opportunities")

    @patch('tap_lever.streams.base.BaseStream.load_schema_by_name')
    def test_generate_catalog_includes_forced_replication_method(self, mock_load_schema):
        """Verify generate_catalog includes forced-replication-method."""

        mock_load_schema.return_value = {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "updated_at": {"type": "integer"}
            }
        }
        config = {"token": "test_token", "start_date": "2020-01-01T00:00:00Z"}
        state = {}
        catalog = MagicMock()
        client = MagicMock()

        stream = CandidateStream(config, state, catalog, client)
        catalog_entry = stream.generate_catalog()[0]

        self.assertIn('forced-replication-method', catalog_entry)
        self.assertEqual(catalog_entry['tap_stream_id'], 'candidates')
        self.assertEqual(catalog_entry['key_properties'], ['id'])

        # Verify the empty breadcrumb metadata contains table-level singer metadata
        metadata_map = {tuple(entry['breadcrumb']): entry['metadata'] for entry in catalog_entry['metadata']}
        root_meta = metadata_map.get(())
        self.assertIsNotNone(root_meta, "Empty breadcrumb metadata entry is missing")
        self.assertEqual(root_meta.get('table-key-properties'), ['id'])
        self.assertEqual(root_meta.get('forced-replication-method'), 'FULL_TABLE')
        self.assertIn('valid-replication-keys', root_meta)
        self.assertEqual(root_meta.get('valid-replication-keys'), [])
        self.assertEqual(root_meta.get('inclusion'), 'available')

    @patch('tap_lever.streams.base.BaseStream.load_schema_by_name')
    def test_generate_catalog_empty_breadcrumb_all_required_keys(self, mock_load_schema):
        """Verify all Singer spec keys are present at empty breadcrumb for every stream class."""
        mock_load_schema.return_value = {
            "type": "object",
            "properties": {
                "id": {"type": "string"}
            }
        }
        config = {"token": "test_token", "start_date": "2020-01-01T00:00:00Z"}
        state = {}
        catalog = MagicMock()
        client = MagicMock()

        required_root_keys = {'table-key-properties', 'forced-replication-method', 'valid-replication-keys', 'inclusion'}

        for stream_class in AVAILABLE_STREAMS:
            with self.subTest(stream=stream_class.TABLE):
                stream = stream_class(config, state, catalog, client)
                catalog_entry = stream.generate_catalog()[0]

                metadata_map = {
                    tuple(e['breadcrumb']): e['metadata']
                    for e in catalog_entry['metadata']
                }
                root_meta = metadata_map.get(())

                self.assertIsNotNone(root_meta, f"{stream_class.TABLE}: empty breadcrumb entry missing")
                for key in required_root_keys:
                    self.assertIn(key, root_meta, f"{stream_class.TABLE}: '{key}' missing from empty breadcrumb metadata")
                self.assertEqual(
                    root_meta['table-key-properties'], stream_class.KEY_PROPERTIES,
                    f"{stream_class.TABLE}: table-key-properties mismatch"
                )
                self.assertEqual(
                    root_meta['forced-replication-method'], stream_class.REPLICATION_METHOD,
                    f"{stream_class.TABLE}: forced-replication-method mismatch"
                )

    @patch('tap_lever.streams.base.BaseStream.load_schema_by_name')
    def test_generate_catalog_includes_parent_for_child_streams(self, mock_load_schema):
        """Verify generate_catalog includes parent-tap-stream-id for child streams."""

        mock_load_schema.return_value = {
            "type": "object",
            "properties": {
                "id": {"type": "string"}
            }
        }

        config = {"token": "test_token", "start_date": "2020-01-01T00:00:00Z"}
        state = {}
        catalog = MagicMock()
        client = MagicMock()

        stream = CandidateApplicationsStream(config, state, catalog, client)
        catalog_entry = stream.generate_catalog()[0]

        self.assertNotIn('parent-tap-stream-id', catalog_entry)

        metadata_map = {tuple(e['breadcrumb']): e['metadata'] for e in catalog_entry['metadata']}
        root_meta = metadata_map.get(())
        self.assertIsNotNone(root_meta)
        self.assertIn('parent-tap-stream-id', root_meta)
        self.assertEqual(root_meta['parent-tap-stream-id'], 'candidates')


class TestCheckAccess(unittest.TestCase):
    """Tests for BaseStream.check_access()."""

    def _make_stream(self, stream_cls, client):
        config = {"token": "test_token", "start_date": "2020-01-01T00:00:00Z"}
        return stream_cls(config, {}, None, client)

    def test_check_access_returns_true_when_request_succeeds(self):
        """check_access() returns True when the API responds successfully."""
        client = MagicMock()
        client.make_request.return_value = {"data": [], "next": None}

        stream = self._make_stream(CandidateStream, client)
        self.assertTrue(stream.check_access())

    def test_check_access_returns_false_on_forbidden(self):
        """check_access() returns False when the API raises LeverForbiddenError."""
        client = MagicMock()
        client.make_request.side_effect = LeverForbiddenError("HTTP-error-code: 403")

        stream = self._make_stream(CandidateStream, client)
        self.assertFalse(stream.check_access())

    def test_check_access_child_stream_always_returns_true(self):
        """Child streams always return True regardless of API response."""
        client = MagicMock()
        client.make_request.side_effect = LeverForbiddenError("HTTP-error-code: 403")

        stream = self._make_stream(CandidateApplicationsStream, client)
        self.assertTrue(stream.check_access())
        client.make_request.assert_not_called()

    def test_check_access_opportunity_child_always_returns_true(self):
        """Opportunity child streams return True without making a request."""
        client = MagicMock()
        client.make_request.side_effect = LeverForbiddenError("HTTP-error-code: 403")

        stream = self._make_stream(OpportunityApplicationsStream, client)
        self.assertTrue(stream.check_access())
        client.make_request.assert_not_called()


class TestDoDiscoverAccessChecks(unittest.TestCase):
    """Tests for discovery.discover() access-check filtering."""

    _config = {"token": "test_token", "start_date": "2020-01-01T00:00:00Z"}
    _state = {}

    @patch('tap_lever.streams.base.BaseStream.check_access', return_value=True)
    @patch('tap_lever.streams.base.BaseStream.load_schema_by_name')
    def test_discover_all_accessible_builds_full_catalog(self, mock_schema, mock_access):
        """All streams accessible → catalog contains all streams."""
        from tap_lever.discovery import discover
        mock_schema.return_value = {"type": "object", "properties": {"id": {"type": "string"}}}
        client = MagicMock()

        catalog = discover(client, self._config, self._state, AVAILABLE_STREAMS)

        stream_ids = {s['tap_stream_id'] for s in catalog['streams']}
        self.assertEqual(len(stream_ids), len(AVAILABLE_STREAMS))

    @patch('tap_lever.streams.base.BaseStream.load_schema_by_name')
    def test_discover_excludes_inaccessible_parent_and_its_children(self, mock_schema):
        """When candidates is inaccessible, it and its children are excluded."""
        from tap_lever.discovery import discover
        mock_schema.return_value = {"type": "object", "properties": {"id": {"type": "string"}}}
        client = MagicMock()

        def access_side_effect(self):
            if self.PARENT:
                return True
            return self.TABLE != 'candidates'

        with patch('tap_lever.streams.base.BaseStream.check_access', access_side_effect):
            catalog = discover(client, self._config, self._state, AVAILABLE_STREAMS)

        stream_ids = {s['tap_stream_id'] for s in catalog['streams']}
        self.assertNotIn('candidates', stream_ids)
        self.assertNotIn('candidate_applications', stream_ids)
        self.assertNotIn('candidate_offers', stream_ids)
        self.assertNotIn('candidate_referrals', stream_ids)
        self.assertNotIn('candidate_resumes', stream_ids)
        self.assertIn('opportunities', stream_ids)

    @patch('tap_lever.streams.base.BaseStream.load_schema_by_name')
    def test_discover_raises_when_no_parent_accessible(self, mock_schema):
        """If no parent stream is accessible, LeverForbiddenError is raised."""
        from tap_lever.discovery import discover
        mock_schema.return_value = {"type": "object", "properties": {"id": {"type": "string"}}}
        client = MagicMock()

        def no_access(self):
            return bool(self.PARENT)  # only children return True

        with patch('tap_lever.streams.base.BaseStream.check_access', no_access):
            with self.assertRaises(LeverForbiddenError):
                discover(client, self._config, self._state, AVAILABLE_STREAMS)
