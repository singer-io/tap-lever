"""Unit tests for tap-lever bookmarking.

All streams in tap-lever use FULL_TABLE replication, so bookmark tests do not apply.
"""
import unittest


@unittest.skip("All streams are FULL_TABLE; bookmark tests not applicable.")
class LeverBookmarkTest(unittest.TestCase):
    pass
