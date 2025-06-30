"""
Test middleware functionality.
"""

from tramlines.middleware import GuardRailMiddleware


class TestMiddleware:
    """Test middleware functionality."""

    def test_initial_session_statistics_are_correct(self):
        """Test session statistics are properly tracked."""
        middleware = GuardRailMiddleware()

        initial_stats = middleware.get_session_stats()
        expected_keys = ["active_sessions", "total_calls", "max_calls_per_session"]

        for key in expected_keys:
            assert key in initial_stats

        assert initial_stats["active_sessions"] == 0
        assert initial_stats["total_calls"] == 0
