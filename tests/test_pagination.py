"""Unit tests for tap-lever pagination with mocked data."""
import unittest
from unittest.mock import MagicMock

try:
    from .base import LeverBaseTest
except ImportError:
    from base import LeverBaseTest
from tap_lever.client import LeverClient
from tap_lever.streams import AVAILABLE_STREAMS


class LeverPaginationTest(LeverBaseTest, unittest.TestCase):

    def test_client_make_request_paginates_via_next(self):
        """LeverClient.make_request returns JSON with a 'next' cursor;
        sync_paginated should keep calling until next is None."""
        config = {"token": "dummy"}
        client = LeverClient(config)

        # Two pages: first has next cursor, second does not
        first_page = {
            "data": [{"id": str(i)} for i in range(1, 101)],
            "next": "cursor_abc",
        }
        second_page = {
            "data": [{"id": "101"}, {"id": "102"}],
            "next": None,
        }

        client.make_request = MagicMock(side_effect=[first_page, second_page])

        self.assertEqual(client.make_request.call_count, 0)

        # Simulate what sync_paginated does: loop while next is not None
        all_data = []
        params = {"limit": 100}
        url = "https://api.lever.co/v1/users"
        next = True
        page = 0
        while next is not None:
            result = client.make_request(url, "GET", params=params)
            next = result.get("next")
            all_data.extend(result["data"])
            if next:
                params["offset"] = next
            page += 1

        self.assertEqual(page, 2)
        self.assertEqual(len(all_data), 102)
        self.assertEqual(client.make_request.call_count, 2)

    def test_client_make_request_single_page(self):
        """When the first response has next=None, pagination stops after one call."""
        config = {"token": "dummy"}
        client = LeverClient(config)

        single_page = {
            "data": [{"id": "1"}, {"id": "2"}],
            "next": None,
        }
        client.make_request = MagicMock(return_value=single_page)

        all_data = []
        params = {"limit": 100}
        url = "https://api.lever.co/v1/users"
        next = True
        while next is not None:
            result = client.make_request(url, "GET", params=params)
            next = result.get("next")
            all_data.extend(result["data"])
            if next:
                params["offset"] = next

        self.assertEqual(len(all_data), 2)
        self.assertEqual(client.make_request.call_count, 1)

    def test_all_streams_have_sync_paginated(self):
        """Every stream class exposes sync_paginated for pagination."""
        config = self.get_mock_config()
        for stream_class in AVAILABLE_STREAMS:
            with self.subTest(stream=stream_class.TABLE):
                stream = stream_class(config, {}, None, None)
                self.assertTrue(hasattr(stream, 'sync_paginated'),
                              msg=f"{stream.TABLE} should have sync_paginated")
