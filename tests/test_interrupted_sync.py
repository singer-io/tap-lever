"""Unit tests for tap-lever interrupted sync recovery.

All streams in tap-lever use FULL_TABLE replication, so interrupted-sync
resumption (bookmark-based) tests do not apply.
"""
import unittest


@unittest.skip("All streams are FULL_TABLE; interrupted-sync tests not applicable.")
class LeverInterruptedSyncTest(unittest.TestCase):
    pass
