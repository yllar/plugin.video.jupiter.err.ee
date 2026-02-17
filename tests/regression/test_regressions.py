"""Regression tests for previously fixed bugs."""
import json
import os
import time
import pytest
from unittest.mock import MagicMock, Mock, patch
import requests

from tests.mocks.kodi_mocks import MockListItem


FIXTURE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fixtures', 'api_responses')


# ============================================================================
# Regression: Retry Logic (was broken - raised on first failure, never retried)
# ============================================================================

@pytest.mark.regression
class TestRetryLogicRegression:
    """Verify that download_url actually retries on failure."""

    @patch('time.sleep')
    @patch('requests.get')
    def test_retries_on_failure_then_succeeds(self, mock_get, mock_sleep):
        """Bug: Original code raised exception on first failure, never retrying.
        Fix: Now retries up to 5 times with exponential backoff."""
        from resources.lib.errlib.helpers import download_url

        # Fail twice, succeed on third attempt
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {'success': True}

        mock_get.side_effect = [
            requests.exceptions.Timeout('timeout'),
            requests.exceptions.ConnectionError('connection refused'),
            mock_response
        ]

        result = download_url('https://test.err.ee/api/test')
        assert result.json() == {'success': True}
        assert mock_get.call_count == 3

    @patch('time.sleep')
    @patch('requests.get')
    def test_exponential_backoff_timing(self, mock_get, mock_sleep):
        """Verify backoff: 0.5s, 1s, 2s, 4s between retries."""
        from resources.lib.errlib.helpers import download_url

        mock_get.side_effect = requests.exceptions.Timeout('timeout')

        with pytest.raises(RuntimeError):
            download_url('https://test.err.ee/api/test')

        # Should sleep 4 times (not on last attempt)
        assert mock_sleep.call_count == 4
        calls = [c[0][0] for c in mock_sleep.call_args_list]
        assert calls == [0.5, 1.0, 2.0, 4.0]

    @patch('time.sleep')
    @patch('requests.get')
    def test_runtime_error_only_after_all_attempts(self, mock_get, mock_sleep):
        """RuntimeError should only be raised after all 5 attempts fail."""
        from resources.lib.errlib.helpers import download_url

        mock_get.side_effect = requests.exceptions.Timeout('timeout')

        with pytest.raises(RuntimeError, match='Could not open URL after 5 attempts'):
            download_url('https://test.err.ee/api/test')

        assert mock_get.call_count == 5


# ============================================================================
# Regression: Search None (search returning None crashed addon)
# ============================================================================

@pytest.mark.regression
class TestSearchNoneRegression:
    """Verify that Search handles missing/invalid data gracefully."""

    @patch('resources.lib.errlib.helpers.download_url')
    def test_get_response_returns_none_on_missing_keys(self, mock_dl):
        """Bug: Accessing search results on None caused crashes."""
        from resources.lib.errlib.search import Search

        mock_dl.return_value.json.return_value = {'unexpected': 'data'}
        search = Search(search_phrase='test')
        result = search.get_response()
        assert result is None

    @patch('resources.lib.errlib.helpers.download_url')
    def test_get_results_returns_none_on_missing_content_type(self, mock_dl):
        from resources.lib.errlib.search import Search

        mock_dl.return_value.json.return_value = {'video': {'totalFound': 0}}
        search = Search(search_phrase='test')
        result = search.get_results(content_type='audio')
        assert result is None

    @patch('resources.lib.errlib.helpers.download_url')
    def test_get_response_with_empty_response(self, mock_dl):
        from resources.lib.errlib.search import Search

        mock_dl.return_value.json.return_value = {}
        search = Search(search_phrase='test')
        result = search.get_response()
        assert result is None

    @patch('resources.lib.errlib.helpers.download_url')
    def test_get_results_returns_none_on_missing_contents(self, mock_dl):
        from resources.lib.errlib.search import Search

        mock_dl.return_value.json.return_value = {'video': {'totalFound': 5}}
        search = Search(search_phrase='test')
        # 'contents' key missing from video
        result = search.get_results(content_type='video')
        assert result is None


# ============================================================================
# Regression: Episode Number None (caused TypeError in comparison)
# ============================================================================

@pytest.mark.regression
class TestEpisodeNumberNoneRegression:
    """Verify that None episode numbers don't cause crashes."""

    def test_monthly_episode_none_uses_heading(self):
        """Bug: `if data.get_item_episode(day) > 0` failed when episode was None."""
        from resources.lib.content_handlers import handle_monthly_seasons

        data = MagicMock()
        season = {'items': [{'name': 'January'}]}
        data.get_items.return_value = [{'name': 'January', 'firstContentId': 100}]
        data.get_item_name.return_value = 'January'
        data.get_item_primaryid.return_value = 100
        data.get_item_contents.return_value = [{
            'id': 1, 'heading': 'Test Episode', 'scheduleStart': 1700000000
        }]
        data.get_item_episode.return_value = None
        data.get_item_heading.return_value = 'Test Episode'
        data.get_item_photo.return_value = None
        data.get_item_schedule_start.return_value = 1700000000
        data.get_item_id.return_value = 1

        settings = MagicMock()
        settings.colour_category = 'blue'
        settings.enable_images = False

        items = handle_monthly_seasons(season, data, settings, 'plugin://test/')
        # Should not crash - and should use heading as title
        episode_items = [i for i in items if 'COLOR' not in i[1].label]
        assert len(episode_items) > 0
        assert 'Test Episode' in episode_items[0][1].label

    def test_monthly_episode_zero_uses_heading(self):
        """Episode number 0 should be treated as 'no episode number'."""
        from resources.lib.content_handlers import handle_monthly_seasons

        data = MagicMock()
        data.get_items.return_value = [{'name': 'Feb', 'firstContentId': 200}]
        data.get_item_name.return_value = 'Feb'
        data.get_item_primaryid.return_value = 200
        data.get_item_contents.return_value = [{
            'id': 2, 'heading': 'Zero Episode', 'scheduleStart': 1700000000
        }]
        data.get_item_episode.return_value = 0
        data.get_item_heading.return_value = 'Zero Episode'
        data.get_item_photo.return_value = None
        data.get_item_schedule_start.return_value = 1700000000
        data.get_item_id.return_value = 2

        settings = MagicMock()
        settings.colour_category = 'blue'
        settings.enable_images = False

        items = handle_monthly_seasons({'items': []}, data, settings, 'plugin://test/')
        episode_items = [i for i in items if 'COLOR' not in i[1].label]
        assert len(episode_items) > 0
        # Should use heading only, not "heading 0"
        assert 'Zero Episode' in episode_items[0][1].label
        assert '0' not in episode_items[0][1].label

    def test_seasonal_none_episode_none_heading_none_subheading(self):
        """All title sources None - should fall back to 'Episode' string."""
        from resources.lib.content_handlers import handle_seasonal_content

        data = MagicMock()
        episode = {'id': 99}
        data.get_item_contents.return_value = [episode]
        data.get_item_subheading.return_value = None
        data.get_item_heading.return_value = None
        data.get_item_episode.return_value = None
        data.get_item_photo.return_value = None

        settings = MagicMock()
        settings.enable_images = False

        items = handle_seasonal_content({'id': 1}, data, settings, 'plugin://test/')
        assert items[0][1].label == 'Episode'


# ============================================================================
# Regression: Photo Fallback (photo URL fallback chain issues)
# ============================================================================

@pytest.mark.regression
class TestPhotoFallbackRegression:
    """Verify photo URL fallback chain works correctly."""

    @patch('resources.lib.errlib.helpers.download_url')
    def test_horizontal_photo_preferred(self, mock_dl):
        """get_item_photo should try horizontal first."""
        from resources.lib.errlib.content import Content

        mock_dl.return_value.json.return_value = {'data': {'pageType': 'episode', 'mainContent': {}}}
        content = Content('123')

        item = {
            'horizontalPhotos': [{'photoUrlOriginal': 'https://horizontal.jpg'}],
            'photos': [{'photoUrlOriginal': 'https://original.jpg'}]
        }
        assert content.get_item_photo(item) == 'https://horizontal.jpg'

    @patch('resources.lib.errlib.helpers.download_url')
    def test_falls_back_to_original_photo(self, mock_dl):
        """When no horizontal, should use original photo."""
        from resources.lib.errlib.content import Content

        mock_dl.return_value.json.return_value = {'data': {'pageType': 'episode', 'mainContent': {}}}
        content = Content('123')

        item = {
            'photos': [{'photoUrlOriginal': 'https://original.jpg'}]
        }
        assert content.get_item_photo(item) == 'https://original.jpg'

    @patch('resources.lib.errlib.helpers.download_url')
    def test_all_photos_missing_returns_none(self, mock_dl):
        """When all photo sources missing, should return None (not crash)."""
        from resources.lib.errlib.content import Content

        mock_dl.return_value.json.return_value = {'data': {'pageType': 'episode', 'mainContent': {}}}
        content = Content('123')

        item = {}
        result = content.get_item_photo(item)
        assert result is None

    @patch('resources.lib.errlib.helpers.download_url')
    def test_empty_photo_arrays_returns_none(self, mock_dl):
        """Empty photo arrays should return None (not IndexError)."""
        from resources.lib.errlib.content import Content

        mock_dl.return_value.json.return_value = {'data': {'pageType': 'episode', 'mainContent': {}}}
        content = Content('123')

        item = {'horizontalPhotos': [], 'photos': []}
        result = content.get_item_photo(item)
        assert result is None

    @patch('resources.lib.errlib.helpers.download_url')
    def test_horizontal_none_falls_through(self, mock_dl):
        """horizontal returns None -> should try original."""
        from resources.lib.errlib.content import Content

        mock_dl.return_value.json.return_value = {'data': {'pageType': 'episode', 'mainContent': {}}}
        content = Content('123')

        # horizontalPhotos exists but has no photoUrlOriginal
        item = {
            'horizontalPhotos': [{'someOtherField': 'value'}],
            'photos': [{'photoUrlOriginal': 'https://fallback.jpg'}]
        }
        result = content.get_item_photo(item)
        assert result == 'https://fallback.jpg'
