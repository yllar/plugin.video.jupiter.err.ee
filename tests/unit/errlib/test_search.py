"""Unit tests for resources/lib/errlib/search.py.

Tests Search URL construction, get_response tuple counts,
get_results content retrieval, and error handling for both methods.
"""
import json
import os
import pytest
from unittest.mock import patch, Mock

from resources.lib.errlib.constants import SEARCH_CATEGORY_ID, SEARCH_PAGE_LIMIT

# Path to the real fixture file
FIXTURE_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'fixtures', 'api_responses')


def _load_fixture(filename):
    """Load a JSON fixture file and return parsed data."""
    filepath = os.path.join(FIXTURE_DIR, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def _make_search(fixture_data, search_type='', search_phrase=''):
    """Create a Search instance with mocked download_url returning fixture_data."""
    mock_response = Mock()
    mock_response.json.return_value = fixture_data
    with patch('resources.lib.errlib.search.download_url', return_value=mock_response):
        from resources.lib.errlib.search import Search
        return Search(search_type=search_type, search_phrase=search_phrase)


# ---------------------------------------------------------------------------
# Search.__init__
# ---------------------------------------------------------------------------
class TestSearchInit:
    """Tests for Search initialization and URL construction."""

    @pytest.mark.unit
    def test_search_url_includes_phrase(self):
        """Search URL contains the search phrase."""
        # Arrange
        fixture = _load_fixture('search_results.json')
        mock_response = Mock()
        mock_response.json.return_value = fixture

        with patch('resources.lib.errlib.search.download_url', return_value=mock_response) as mock_dl:
            from resources.lib.errlib.search import Search

            # Act
            search = Search(search_phrase='osoon')

            # Assert
            called_url = mock_dl.call_args[0][0]
            assert 'osoon' in called_url

    @pytest.mark.unit
    def test_search_url_includes_search_type(self):
        """Search URL contains the search type parameter."""
        # Arrange
        fixture = _load_fixture('search_results.json')
        mock_response = Mock()
        mock_response.json.return_value = fixture

        with patch('resources.lib.errlib.search.download_url', return_value=mock_response) as mock_dl:
            from resources.lib.errlib.search import Search

            # Act
            search = Search(search_type='video', search_phrase='test')

            # Assert
            called_url = mock_dl.call_args[0][0]
            assert 'type=video' in called_url

    @pytest.mark.unit
    def test_search_url_includes_category_id(self):
        """Search URL includes the configured SEARCH_CATEGORY_ID."""
        # Arrange
        fixture = _load_fixture('search_results.json')
        mock_response = Mock()
        mock_response.json.return_value = fixture

        with patch('resources.lib.errlib.search.download_url', return_value=mock_response) as mock_dl:
            from resources.lib.errlib.search import Search

            # Act
            search = Search(search_phrase='test')

            # Assert
            called_url = mock_dl.call_args[0][0]
            assert str(SEARCH_CATEGORY_ID) in called_url

    @pytest.mark.unit
    def test_search_url_includes_page_limit(self):
        """Search URL includes the configured SEARCH_PAGE_LIMIT."""
        # Arrange
        fixture = _load_fixture('search_results.json')
        mock_response = Mock()
        mock_response.json.return_value = fixture

        with patch('resources.lib.errlib.search.download_url', return_value=mock_response) as mock_dl:
            from resources.lib.errlib.search import Search

            # Act
            search = Search(search_phrase='test')

            # Assert
            called_url = mock_dl.call_args[0][0]
            assert str(SEARCH_PAGE_LIMIT) in called_url

    @pytest.mark.unit
    def test_search_url_uses_api_base(self):
        """Search URL starts with the ERR API base URL."""
        # Arrange
        fixture = _load_fixture('search_results.json')
        mock_response = Mock()
        mock_response.json.return_value = fixture

        with patch('resources.lib.errlib.search.download_url', return_value=mock_response) as mock_dl:
            from resources.lib.errlib.search import Search

            # Act
            search = Search(search_phrase='test')

            # Assert
            called_url = mock_dl.call_args[0][0]
            assert 'https://services.err.ee/api/' in called_url
            assert 'search/getVodContents/' in called_url

    @pytest.mark.unit
    def test_search_stores_content(self):
        """Search stores the parsed JSON response."""
        # Arrange
        fixture = _load_fixture('search_results.json')
        search = _make_search(fixture, search_phrase='osoon')

        # Assert
        assert search.content == fixture


# ---------------------------------------------------------------------------
# get_response
# ---------------------------------------------------------------------------
class TestGetResponse:
    """Tests for Search.get_response()."""

    @pytest.mark.unit
    def test_get_response_returns_tuple_of_counts(self):
        """get_response returns (video_totalFound, audio_totalFound)."""
        # Arrange
        fixture = _load_fixture('search_results.json')
        search = _make_search(fixture, search_phrase='osoon')

        # Act
        result = search.get_response()

        # Assert
        assert isinstance(result, tuple)
        assert len(result) == 2

    @pytest.mark.unit
    def test_get_response_video_count_from_fixture(self):
        """get_response returns correct video totalFound from fixture."""
        # Arrange
        fixture = _load_fixture('search_results.json')
        search = _make_search(fixture, search_phrase='osoon')

        # Act
        video_count, audio_count = search.get_response()

        # Assert
        assert video_count == 13  # From search_results.json fixture

    @pytest.mark.unit
    def test_get_response_audio_count_from_fixture(self):
        """get_response returns correct audio totalFound from fixture."""
        # Arrange
        fixture = _load_fixture('search_results.json')
        search = _make_search(fixture, search_phrase='osoon')

        # Act
        video_count, audio_count = search.get_response()

        # Assert
        assert audio_count == 4  # From search_results.json fixture

    @pytest.mark.unit
    def test_get_response_returns_none_on_missing_video_key(self):
        """get_response returns None when 'video' key is missing."""
        # Arrange
        fixture = {'audio': {'totalFound': 5, 'contents': []}}
        search = _make_search(fixture, search_phrase='test')

        # Act
        result = search.get_response()

        # Assert
        assert result is None

    @pytest.mark.unit
    def test_get_response_returns_none_on_missing_audio_key(self):
        """get_response returns None when 'audio' key is missing."""
        # Arrange
        fixture = {'video': {'totalFound': 5, 'contents': []}}
        search = _make_search(fixture, search_phrase='test')

        # Act
        result = search.get_response()

        # Assert
        assert result is None

    @pytest.mark.unit
    def test_get_response_returns_none_on_none_content(self):
        """get_response returns None when content is None."""
        # Arrange
        search = _make_search({}, search_phrase='test')
        search.content = None

        # Act
        result = search.get_response()

        # Assert
        assert result is None

    @pytest.mark.unit
    def test_get_response_returns_none_on_empty_dict(self):
        """get_response returns None when content is an empty dict."""
        # Arrange
        search = _make_search({}, search_phrase='test')

        # Act
        result = search.get_response()

        # Assert
        assert result is None


# ---------------------------------------------------------------------------
# get_results
# ---------------------------------------------------------------------------
class TestGetResults:
    """Tests for Search.get_results()."""

    @pytest.mark.unit
    def test_get_results_video_contents(self):
        """get_results('video') returns the video contents list."""
        # Arrange
        fixture = _load_fixture('search_results.json')
        search = _make_search(fixture, search_phrase='osoon')

        # Act
        results = search.get_results(content_type='video')

        # Assert
        assert isinstance(results, list)
        assert len(results) > 0

    @pytest.mark.unit
    def test_get_results_audio_contents(self):
        """get_results('audio') returns the audio contents list."""
        # Arrange
        fixture = _load_fixture('search_results.json')
        search = _make_search(fixture, search_phrase='osoon')

        # Act
        results = search.get_results(content_type='audio')

        # Assert
        assert isinstance(results, list)
        assert len(results) > 0

    @pytest.mark.unit
    def test_get_results_video_has_expected_fields(self):
        """Video results contain expected fields like id, heading, type."""
        # Arrange
        fixture = _load_fixture('search_results.json')
        search = _make_search(fixture, search_phrase='osoon')

        # Act
        results = search.get_results(content_type='video')

        # Assert
        first = results[0]
        assert 'id' in first
        assert 'heading' in first
        assert 'type' in first

    @pytest.mark.unit
    def test_get_results_first_video_heading(self):
        """First video result has heading 'Osoon' from fixture."""
        # Arrange
        fixture = _load_fixture('search_results.json')
        search = _make_search(fixture, search_phrase='osoon')

        # Act
        results = search.get_results(content_type='video')

        # Assert
        assert results[0]['heading'] == 'Osoon'

    @pytest.mark.unit
    def test_get_results_default_content_type_is_video(self):
        """get_results() defaults to content_type='video'."""
        # Arrange
        fixture = _load_fixture('search_results.json')
        search = _make_search(fixture, search_phrase='osoon')

        # Act
        results_default = search.get_results()
        results_video = search.get_results(content_type='video')

        # Assert
        assert results_default == results_video

    @pytest.mark.unit
    def test_get_results_returns_none_on_missing_key(self):
        """get_results returns None when requested content_type key is missing."""
        # Arrange
        fixture = {'video': {'totalFound': 0, 'contents': []}}
        search = _make_search(fixture, search_phrase='test')

        # Act
        result = search.get_results(content_type='audio')

        # Assert
        assert result is None

    @pytest.mark.unit
    def test_get_results_returns_none_on_none_content(self):
        """get_results returns None when content is None."""
        # Arrange
        search = _make_search({}, search_phrase='test')
        search.content = None

        # Act
        result = search.get_results()

        # Assert
        assert result is None

    @pytest.mark.unit
    def test_get_results_returns_none_on_missing_contents_subkey(self):
        """get_results returns None when 'contents' sub-key is missing."""
        # Arrange
        fixture = {'video': {'totalFound': 5}}
        search = _make_search(fixture, search_phrase='test')

        # Act
        result = search.get_results(content_type='video')

        # Assert
        assert result is None

    @pytest.mark.unit
    @pytest.mark.parametrize('content_type,expected_count', [
        ('video', 5),  # 5 video results in the fixture
        ('audio', 4),  # 4 audio results in the fixture
    ])
    def test_get_results_counts_match_fixture(self, content_type, expected_count):
        """get_results returns the expected number of items from the fixture."""
        # Arrange
        fixture = _load_fixture('search_results.json')
        search = _make_search(fixture, search_phrase='osoon')

        # Act
        results = search.get_results(content_type=content_type)

        # Assert
        assert len(results) == expected_count
