# coding: utf-8
"""Comprehensive tests for resources.lib.errlib.content.Content class."""
import json
import os

import pytest
from unittest.mock import Mock, patch


# Fixtures directory path
FIXTURES_DIR = os.path.join(
    os.path.dirname(__file__), '..', '..', 'fixtures', 'api_responses'
)


def _load_fixture(filename):
    """Load a JSON fixture file and return parsed data."""
    filepath = os.path.join(FIXTURES_DIR, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def _create_content_with_fixture(fixture_filename):
    """Create a Content instance with mocked download_url returning fixture data."""
    fixture_data = _load_fixture(fixture_filename)
    mock_response = Mock()
    mock_response.json.return_value = fixture_data
    with patch('resources.lib.errlib.content.download_url', return_value=mock_response):
        from resources.lib.errlib.content import Content
        return Content('12345'), fixture_data


def _create_content_with_data(data):
    """Create a Content instance with mocked download_url returning given data."""
    mock_response = Mock()
    mock_response.json.return_value = data
    with patch('resources.lib.errlib.content.download_url', return_value=mock_response):
        from resources.lib.errlib.content import Content
        return Content('12345')


# ---------------------------------------------------------------------------
# Initialization tests
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestContentInit:
    """Tests for Content.__init__."""

    def test_url_construction(self):
        """Verify the API URL is built from base URL, version, and content ID."""
        mock_response = Mock()
        mock_response.json.return_value = {}
        with patch('resources.lib.errlib.content.download_url', return_value=mock_response) as mock_dl:
            from resources.lib.errlib.content import Content
            content = Content('1609926226')
            expected_url = 'https://services.err.ee/api/v2/vodContent/getContentPageData?contentId=1609926226'
            assert content.url == expected_url
            mock_dl.assert_called_once_with(expected_url)

    def test_content_stores_json_response(self):
        """Verify the JSON response is stored on the instance."""
        fixture_data = _load_fixture('content_episode.json')
        mock_response = Mock()
        mock_response.json.return_value = fixture_data
        with patch('resources.lib.errlib.content.download_url', return_value=mock_response):
            from resources.lib.errlib.content import Content
            content = Content('1609926226')
            assert content.content == fixture_data


# ---------------------------------------------------------------------------
# get_page_type tests
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestGetPageType:
    """Tests for Content.get_page_type."""

    @pytest.mark.parametrize('fixture_file,expected_page_type', [
        ('content_episode.json', 'episode'),
        ('content_series.json', 'series'),
        ('content_movie.json', 'movie'),
    ])
    def test_returns_correct_page_type(self, fixture_file, expected_page_type):
        content, _ = _create_content_with_fixture(fixture_file)
        assert content.get_page_type() == expected_page_type

    def test_returns_none_when_missing(self):
        content = _create_content_with_data({})
        assert content.get_page_type() is None

    def test_returns_none_when_data_is_none(self):
        content = _create_content_with_data({'data': None})
        assert content.get_page_type() is None


# ---------------------------------------------------------------------------
# get_id tests
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestGetId:
    """Tests for Content.get_id."""

    def test_returns_main_content_id(self):
        content, _ = _create_content_with_fixture('content_episode.json')
        assert content.get_id() == 1609926226

    def test_returns_main_content_id_explicit_type(self):
        content, _ = _create_content_with_fixture('content_episode.json')
        assert content.get_id(type='main') == 1609926226

    def test_returns_none_for_invalid_type(self):
        content, _ = _create_content_with_fixture('content_episode.json')
        assert content.get_id(type='nonexistent') is None

    def test_returns_none_when_data_missing(self):
        content = _create_content_with_data({})
        assert content.get_id() is None


# ---------------------------------------------------------------------------
# get_heading tests
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestGetHeading:
    """Tests for Content.get_heading."""

    @pytest.mark.parametrize('fixture_file,expected_heading', [
        ('content_episode.json', 'Eesti lood'),
        ('content_series.json', 'Eesti lood'),
        ('content_movie.json', 'Kahtluste v\u00f5rk'),
    ])
    def test_returns_heading(self, fixture_file, expected_heading):
        content, _ = _create_content_with_fixture(fixture_file)
        assert content.get_heading() == expected_heading

    def test_returns_none_when_missing(self):
        content = _create_content_with_data({})
        assert content.get_heading() is None


# ---------------------------------------------------------------------------
# get_subheading tests
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestGetSubHeading:
    """Tests for Content.get_subheading."""

    def test_returns_subheading_episode(self):
        content, _ = _create_content_with_fixture('content_episode.json')
        assert content.get_subheading() == 'Igavene v\u00f5itlus'

    def test_returns_empty_string_movie(self):
        content, _ = _create_content_with_fixture('content_movie.json')
        assert content.get_subheading() == ''

    def test_returns_none_when_missing(self):
        content = _create_content_with_data({})
        assert content.get_subheading() is None


# ---------------------------------------------------------------------------
# get_lead tests
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestGetLead:
    """Tests for Content.get_lead."""

    def test_returns_lead_html(self):
        content, _ = _create_content_with_fixture('content_episode.json')
        lead = content.get_lead()
        assert lead is not None
        assert '<p>' in lead
        assert 'Vene perekonnast' in lead

    def test_returns_none_when_missing(self):
        content = _create_content_with_data({})
        assert content.get_lead() is None


# ---------------------------------------------------------------------------
# get_body tests
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestGetBody:
    """Tests for Content.get_body."""

    def test_returns_body_html(self):
        content, _ = _create_content_with_fixture('content_episode.json')
        body = content.get_body()
        assert body is not None
        assert '<p>' in body

    def test_returns_none_when_missing(self):
        content = _create_content_with_data({})
        assert content.get_body() is None


# ---------------------------------------------------------------------------
# has_next tests
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestHasNext:
    """Tests for Content.has_next."""

    def test_returns_true_when_next_content_exists(self):
        """Episode fixture has a populated nextContent dict."""
        content, _ = _create_content_with_fixture('content_episode.json')
        assert content.has_next() is True

    def test_returns_none_when_next_content_empty_list(self):
        """Series fixture has nextContent as empty list (falsy)."""
        content, _ = _create_content_with_fixture('content_series.json')
        assert content.has_next() is None

    def test_returns_none_when_next_content_missing(self):
        content = _create_content_with_data({'data': {}})
        assert content.has_next() is None

    def test_returns_none_when_data_missing(self):
        content = _create_content_with_data({})
        assert content.has_next() is None


# ---------------------------------------------------------------------------
# get_primary_category_id tests
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestGetPrimaryCategoryId:
    """Tests for Content.get_primary_category_id."""

    @pytest.mark.parametrize('fixture_file,expected_id', [
        ('content_episode.json', 4135),
        ('content_series.json', 4135),
        ('content_movie.json', 4432),
    ])
    def test_returns_primary_category_id(self, fixture_file, expected_id):
        content, _ = _create_content_with_fixture(fixture_file)
        assert content.get_primary_category_id() == expected_id

    def test_returns_none_when_missing(self):
        content = _create_content_with_data({})
        assert content.get_primary_category_id() is None


# ---------------------------------------------------------------------------
# get_seasonlist_type tests
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestGetSeasonListType:
    """Tests for Content.get_seasonlist_type."""

    def test_returns_seasonal_for_episode(self):
        content, _ = _create_content_with_fixture('content_episode.json')
        assert content.get_seasonlist_type() == 'seasonal'

    def test_returns_seasonal_for_series(self):
        content, _ = _create_content_with_fixture('content_series.json')
        assert content.get_seasonlist_type() == 'seasonal'

    def test_returns_none_for_movie(self):
        """Movie fixture has seasonList as empty list, not a dict."""
        content, _ = _create_content_with_fixture('content_movie.json')
        assert content.get_seasonlist_type() is None

    def test_returns_none_when_missing(self):
        content = _create_content_with_data({})
        assert content.get_seasonlist_type() is None


# ---------------------------------------------------------------------------
# get_media_type tests
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestGetMediaType:
    """Tests for Content.get_media_type."""

    @pytest.mark.parametrize('fixture_file', [
        'content_episode.json',
        'content_series.json',
        'content_movie.json',
    ])
    def test_returns_video(self, fixture_file):
        content, _ = _create_content_with_fixture(fixture_file)
        assert content.get_media_type() == 'video'

    def test_returns_none_when_no_medias(self):
        content = _create_content_with_data({'data': {'mainContent': {'medias': []}}})
        assert content.get_media_type() is None

    def test_returns_none_when_missing(self):
        content = _create_content_with_data({})
        assert content.get_media_type() is None


# ---------------------------------------------------------------------------
# Stream URL tests (get_hls, get_dash, get_file)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestStreamUrls:
    """Tests for Content.get_hls, get_dash, and get_file."""

    def test_get_hls_prepends_https(self):
        content, _ = _create_content_with_fixture('content_episode.json')
        hls = content.get_hls()
        assert hls.startswith('https:')
        assert '//vod.err.ee/hls/' in hls
        assert hls == 'https://vod.err.ee/hls/vod/297c264a78908372b68551bf1fb08a53/5/v/master.m3u8'

    def test_get_dash_prepends_https(self):
        content, _ = _create_content_with_fixture('content_episode.json')
        dash = content.get_dash()
        assert dash.startswith('https:')
        assert '//vod.err.ee/dash/' in dash
        assert dash == 'https://vod.err.ee/dash/vod/297c264a78908372b68551bf1fb08a53/5/v/manifest.mpd'

    def test_get_file_prepends_https(self):
        content, _ = _create_content_with_fixture('content_episode.json')
        file_url = content.get_file()
        assert file_url.startswith('https:')
        assert '//vod.err.ee/file/' in file_url
        assert file_url == 'https://vod.err.ee/file/vod/297c264a78908372b68551bf1fb08a53.mp4'

    def test_get_hls_returns_none_when_missing(self):
        content = _create_content_with_data({})
        assert content.get_hls() is None

    def test_get_dash_returns_none_when_missing(self):
        content = _create_content_with_data({})
        assert content.get_dash() is None

    def test_get_file_returns_none_when_missing(self):
        content = _create_content_with_data({})
        assert content.get_file() is None

    def test_get_hls_movie_fixture(self):
        """Movie fixture has a different media hash path."""
        content, _ = _create_content_with_fixture('content_movie.json')
        hls = content.get_hls()
        assert hls is not None
        assert hls.startswith('https:')


# ---------------------------------------------------------------------------
# get_subtitles tests
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestGetSubtitles:
    """Tests for Content.get_subtitles."""

    def test_returns_et_subtitle_url(self):
        """Episode fixture has ET subtitles."""
        content, _ = _create_content_with_fixture('content_episode.json')
        sub = content.get_subtitles(lang='ET')
        assert sub == 'https://services.err.ee/subtitles/file/413078/413078_ET.vtt'

    def test_returns_va_subtitle_url(self):
        """Episode fixture has VA subtitles."""
        content, _ = _create_content_with_fixture('content_episode.json')
        sub = content.get_subtitles(lang='VA')
        assert sub == 'https://services.err.ee/subtitles/file/412979/412979_VA.vtt'

    def test_default_lang_is_et(self):
        content, _ = _create_content_with_fixture('content_episode.json')
        sub = content.get_subtitles()
        assert sub == 'https://services.err.ee/subtitles/file/413078/413078_ET.vtt'

    def test_returns_none_for_nonexistent_lang(self):
        content, _ = _create_content_with_fixture('content_episode.json')
        sub = content.get_subtitles(lang='FR')
        assert sub is None

    def test_returns_none_when_no_subtitles(self):
        content = _create_content_with_data({})
        sub = content.get_subtitles()
        assert sub is None

    def test_movie_et_subtitle(self):
        """Movie fixture has only ET subtitles."""
        content, _ = _create_content_with_fixture('content_movie.json')
        sub = content.get_subtitles(lang='ET')
        assert sub == 'https://services.err.ee/subtitles/file/352664/352664_ET.vtt'

    def test_series_only_va_subtitle(self):
        """Series fixture has only VA subtitle, no ET."""
        content, _ = _create_content_with_fixture('content_series.json')
        sub = content.get_subtitles(lang='ET')
        assert sub is None

    def test_series_va_subtitle(self):
        content, _ = _create_content_with_fixture('content_series.json')
        sub = content.get_subtitles(lang='VA')
        assert sub == 'https://services.err.ee/subtitles/file/411205/411205_VA.vtt'


# ---------------------------------------------------------------------------
# get_drm tests
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestGetDrm:
    """Tests for Content.get_drm."""

    @pytest.mark.parametrize('fixture_file', [
        'content_episode.json',
        'content_series.json',
        'content_movie.json',
    ])
    def test_returns_false_for_non_drm_content(self, fixture_file):
        content, _ = _create_content_with_fixture(fixture_file)
        assert content.get_drm() is False

    def test_returns_false_when_missing(self):
        content = _create_content_with_data({})
        assert content.get_drm() is False

    def test_returns_true_when_drm_enabled(self):
        data = {
            'data': {
                'mainContent': {
                    'medias': [{
                        'restrictions': {'drm': True}
                    }]
                }
            }
        }
        content = _create_content_with_data(data)
        assert content.get_drm() is True


# ---------------------------------------------------------------------------
# get_token tests
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestGetToken:
    """Tests for Content.get_token."""

    def test_returns_empty_string_episode(self):
        """Episode fixture has jwt as empty string."""
        content, _ = _create_content_with_fixture('content_episode.json')
        assert content.get_token() == ''

    def test_returns_none_series(self):
        """Series fixture has jwt as null."""
        content, _ = _create_content_with_fixture('content_series.json')
        assert content.get_token() is None

    def test_returns_false_when_missing(self):
        content = _create_content_with_data({})
        assert content.get_token() is False

    def test_returns_jwt_string_when_present(self):
        data = {
            'data': {
                'mainContent': {
                    'medias': [{'jwt': 'some.jwt.token'}]
                }
            }
        }
        content = _create_content_with_data(data)
        assert content.get_token() == 'some.jwt.token'


# ---------------------------------------------------------------------------
# get_license_server tests
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestGetLicenseServer:
    """Tests for Content.get_license_server."""

    def test_returns_widevine_url_default(self):
        content, _ = _create_content_with_fixture('content_episode.json')
        url = content.get_license_server()
        assert url == 'https://drm-widevine-licensing.axprod.net/AcquireLicense'

    def test_returns_playready_url(self):
        content, _ = _create_content_with_fixture('content_episode.json')
        url = content.get_license_server(type='playReady')
        assert url == 'https://drm-playready-licensing.axprod.net/AcquireLicense'

    def test_returns_fairplay_url(self):
        content, _ = _create_content_with_fixture('content_episode.json')
        url = content.get_license_server(type='fairPlay')
        assert url == 'https://drm-fairplay-licensing.axprod.net/AcquireLicense'

    def test_returns_false_for_unknown_type(self):
        content, _ = _create_content_with_fixture('content_episode.json')
        url = content.get_license_server(type='unknown')
        assert url is False

    def test_returns_false_when_missing(self):
        content = _create_content_with_data({})
        assert content.get_license_server() is False


# ---------------------------------------------------------------------------
# Photo getter tests (get_photo, get_photo_vertical, get_photo_horizontal)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestPhotos:
    """Tests for Content.get_photo, get_photo_vertical, get_photo_horizontal."""

    def test_get_photo_episode(self):
        content, _ = _create_content_with_fixture('content_episode.json')
        photo = content.get_photo()
        assert photo == 'https://s.err.ee/photo/orig/2026/02/02/3176303h3572.jpg'

    def test_get_photo_movie(self):
        content, _ = _create_content_with_fixture('content_movie.json')
        photo = content.get_photo()
        assert photo == 'https://s.err.ee/photo/orig/2025/04/07/2816234hf85e.jpg'

    def test_get_photo_returns_none_when_missing(self):
        content = _create_content_with_data({})
        assert content.get_photo() is None

    def test_get_photo_vertical_original(self):
        content, _ = _create_content_with_fixture('content_episode.json')
        photo = content.get_photo_vertical()
        assert photo == 'https://s.err.ee/photo/orig/2026/02/09/3193718h8e92.jpg'

    def test_get_photo_vertical_specific_size(self):
        content, _ = _create_content_with_fixture('content_episode.json')
        photo = content.get_photo_vertical(size='80')
        assert photo is not None
        assert 't80.' in photo

    def test_get_photo_vertical_returns_none_when_missing(self):
        content = _create_content_with_data({})
        assert content.get_photo_vertical() is None

    def test_get_photo_horizontal_original(self):
        content, _ = _create_content_with_fixture('content_episode.json')
        photo = content.get_photo_horizontal()
        assert photo == 'https://s.err.ee/photo/orig/2026/02/02/3176303h3572.jpg'

    def test_get_photo_horizontal_specific_size(self):
        content, _ = _create_content_with_fixture('content_episode.json')
        photo = content.get_photo_horizontal(size='2')
        assert photo is not None
        assert 't2.' in photo

    def test_get_photo_horizontal_returns_none_when_missing(self):
        content = _create_content_with_data({})
        assert content.get_photo_horizontal() is None

    def test_get_photo_horizontal_returns_none_movie_empty_array(self):
        """Movie fixture has empty horizontalPhotos array."""
        content, _ = _create_content_with_fixture('content_movie.json')
        photo = content.get_photo_horizontal()
        assert photo is None

    def test_get_photo_vertical_invalid_size(self):
        """Requesting a non-existent size key returns None."""
        content, _ = _create_content_with_fixture('content_episode.json')
        photo = content.get_photo_vertical(size='99999')
        assert photo is None


# ---------------------------------------------------------------------------
# get_season tests
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestGetSeason:
    """Tests for Content.get_season."""

    def test_returns_season_items_episode(self):
        content, _ = _create_content_with_fixture('content_episode.json')
        seasons = content.get_season()
        assert isinstance(seasons, list)
        assert len(seasons) == 23

    def test_returns_season_items_series(self):
        content, _ = _create_content_with_fixture('content_series.json')
        seasons = content.get_season()
        assert isinstance(seasons, list)
        assert len(seasons) == 23

    def test_returns_none_for_movie(self):
        """Movie fixture has seasonList as empty list, so ['items'] raises TypeError."""
        content, _ = _create_content_with_fixture('content_movie.json')
        assert content.get_season() is None

    def test_returns_none_when_missing(self):
        content = _create_content_with_data({})
        assert content.get_season() is None

    def test_first_season_structure(self):
        content, _ = _create_content_with_fixture('content_episode.json')
        seasons = content.get_season()
        first = seasons[0]
        assert first['id'] == 23
        assert first['name'] == '23'
        assert first['firstContentId'] == 1609911839
        assert 'contents' in first


# ---------------------------------------------------------------------------
# Item getter tests (get_item_id, get_primaryid, get_items, etc.)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestItemGetters:
    """Tests for all get_item_* methods that accept item_index dict."""

    @pytest.fixture
    def content_and_season(self):
        """Provide a Content instance and the first season item."""
        content, fixture = _create_content_with_fixture('content_episode.json')
        seasons = content.get_season()
        return content, seasons[0]

    @pytest.fixture
    def content_and_episode_item(self, content_and_season):
        """Provide a Content instance and the first episode in the first season."""
        content, season = content_and_season
        episodes = season['contents']
        return content, episodes[0]

    def test_get_item_id(self, content_and_season):
        content, season = content_and_season
        assert content.get_item_id(season) == 23

    def test_get_primaryid(self, content_and_season):
        content, season = content_and_season
        assert content.get_primaryid(season) == 1609911839

    def test_get_items(self, content_and_season):
        """Seasons without 'items' key return None; season 22 has no items."""
        content, _ = content_and_season
        seasons = content.get_season()
        # Season 22 (index 1) has no 'items' key
        assert content.get_items(seasons[1]) is None

    def test_get_item_name(self, content_and_season):
        content, season = content_and_season
        assert content.get_item_name(season) == '23'

    def test_get_item_primaryid(self, content_and_season):
        content, season = content_and_season
        assert content.get_item_primaryid(season) == 1609911839

    def test_get_item_contents(self, content_and_season):
        content, season = content_and_season
        contents = content.get_item_contents(season)
        assert isinstance(contents, list)
        assert len(contents) > 0

    def test_get_item_heading(self, content_and_episode_item):
        content, episode = content_and_episode_item
        assert content.get_item_heading(episode) == 'Eesti lood'

    def test_get_item_subheading(self, content_and_episode_item):
        content, episode = content_and_episode_item
        sub = content.get_item_subheading(episode)
        assert sub is not None
        assert isinstance(sub, str)

    def test_get_item_episode(self, content_and_episode_item):
        content, episode = content_and_episode_item
        assert content.get_item_episode(episode) == 8

    def test_get_item_public_start(self, content_and_episode_item):
        content, episode = content_and_episode_item
        assert content.get_item_public_start(episode) == 1768491000

    def test_get_item_schedule_start(self, content_and_episode_item):
        content, episode = content_and_episode_item
        assert content.get_item_schedule_start(episode) == 1769970600

    # --- Tests with None/missing data ---

    @pytest.mark.parametrize('method_name', [
        'get_item_id', 'get_primaryid', 'get_items',
        'get_item_name', 'get_item_primaryid', 'get_item_contents',
        'get_item_heading', 'get_item_subheading', 'get_item_episode',
        'get_item_public_start', 'get_item_schedule_start',
    ])
    def test_returns_none_for_empty_dict(self, method_name):
        content = _create_content_with_data({})
        method = getattr(content, method_name)
        assert method({}) is None

    @pytest.mark.parametrize('method_name', [
        'get_item_id', 'get_primaryid', 'get_items',
        'get_item_name', 'get_item_primaryid', 'get_item_contents',
        'get_item_heading', 'get_item_subheading', 'get_item_episode',
        'get_item_public_start', 'get_item_schedule_start',
    ])
    def test_returns_none_for_none_input(self, method_name):
        content = _create_content_with_data({})
        method = getattr(content, method_name)
        assert method(None) is None


# ---------------------------------------------------------------------------
# Item photo getter tests (get_item_photo, get_item_photo_original, etc.)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestItemPhotos:
    """Tests for Content.get_item_photo*, including fallback logic."""

    @pytest.fixture
    def content_and_episode_item(self):
        """Provide a Content instance and an episode item with both photo types."""
        content, fixture = _create_content_with_fixture('content_episode.json')
        seasons = content.get_season()
        episode = seasons[0]['contents'][0]
        return content, episode

    def test_get_item_photo_original(self, content_and_episode_item):
        content, episode = content_and_episode_item
        photo = content.get_item_photo_original(episode)
        assert photo is not None
        assert photo.startswith('https://s.err.ee/photo/orig/')

    def test_get_item_photo_horizontal(self, content_and_episode_item):
        content, episode = content_and_episode_item
        photo = content.get_item_photo_horizontal(episode)
        assert photo is not None
        assert photo.startswith('https://s.err.ee/photo/orig/')

    def test_get_item_photo_prefers_horizontal(self, content_and_episode_item):
        """get_item_photo should return horizontal photo when available."""
        content, episode = content_and_episode_item
        photo = content.get_item_photo(episode)
        horizontal = content.get_item_photo_horizontal(episode)
        assert photo == horizontal

    def test_get_item_photo_falls_back_to_original(self):
        """When horizontalPhotos is missing, get_item_photo falls back to photos."""
        content = _create_content_with_data({})
        item = {
            'photos': [{'photoUrlOriginal': 'https://example.com/fallback.jpg'}]
            # no 'horizontalPhotos' key
        }
        photo = content.get_item_photo(item)
        assert photo == 'https://example.com/fallback.jpg'

    def test_get_item_photo_falls_back_when_horizontal_empty(self):
        """When horizontalPhotos is empty list, falls back to original."""
        content = _create_content_with_data({})
        item = {
            'horizontalPhotos': [],
            'photos': [{'photoUrlOriginal': 'https://example.com/fallback.jpg'}]
        }
        photo = content.get_item_photo(item)
        assert photo == 'https://example.com/fallback.jpg'

    def test_get_item_photo_returns_none_when_both_missing(self):
        content = _create_content_with_data({})
        item = {}
        photo = content.get_item_photo(item)
        assert photo is None

    def test_get_item_photo_original_returns_none_for_empty_dict(self):
        content = _create_content_with_data({})
        assert content.get_item_photo_original({}) is None

    def test_get_item_photo_horizontal_returns_none_for_empty_dict(self):
        content = _create_content_with_data({})
        assert content.get_item_photo_horizontal({}) is None

    def test_get_item_photo_original_returns_none_for_none(self):
        content = _create_content_with_data({})
        assert content.get_item_photo_original(None) is None

    def test_get_item_photo_horizontal_returns_none_for_none(self):
        content = _create_content_with_data({})
        assert content.get_item_photo_horizontal(None) is None

    def test_get_item_photo_returns_none_for_none(self):
        content = _create_content_with_data({})
        assert content.get_item_photo(None) is None


# ---------------------------------------------------------------------------
# Parametrized type='main' vs type='next' for typed getters
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestTypedGetters:
    """Tests for getters that accept a type parameter (main vs next, etc.)."""

    @pytest.fixture
    def episode_content(self):
        content, _ = _create_content_with_fixture('content_episode.json')
        return content

    @pytest.mark.parametrize('method_name', [
        'get_id', 'get_heading', 'get_subheading', 'get_lead',
        'get_body', 'get_primary_category_id',
    ])
    def test_returns_none_for_next_type(self, episode_content, method_name):
        """nextContent is not keyed as 'nextContent' for these getters.
        They look for data[type + 'Content'], so type='next' looks for 'nextContent'
        which does exist in the episode fixture."""
        method = getattr(episode_content, method_name)
        result = method(type='next')
        # nextContent exists in episode fixture as a dict, so some keys may exist
        # but most fields like 'lead', 'body' do not exist on nextContent
        if method_name in ('get_heading', 'get_subheading', 'get_id', 'get_primary_category_id'):
            assert result is not None
        else:
            assert result is None

    def test_get_id_next_content(self, episode_content):
        """Episode fixture has nextContent.id = 1609891613."""
        assert episode_content.get_id(type='next') == 1609891613

    def test_get_heading_next_content(self, episode_content):
        assert episode_content.get_heading(type='next') == 'Eesti lood'

    def test_get_subheading_next_content(self, episode_content):
        assert episode_content.get_subheading(type='next') == 'Maarjamaa salatoimikud'


# ---------------------------------------------------------------------------
# Edge case and robustness tests
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestEdgeCases:
    """Edge cases for Content methods."""

    def test_all_getters_return_none_or_false_for_empty_content(self):
        """When content is an empty dict, all getters should return None or False."""
        content = _create_content_with_data({})
        assert content.get_page_type() is None
        assert content.get_id() is None
        assert content.get_heading() is None
        assert content.get_subheading() is None
        assert content.get_lead() is None
        assert content.get_body() is None
        assert content.has_next() is None
        assert content.get_primary_category_id() is None
        assert content.get_seasonlist_type() is None
        assert content.get_media_type() is None
        assert content.get_hls() is None
        assert content.get_dash() is None
        assert content.get_file() is None
        assert content.get_subtitles() is None
        assert content.get_drm() is False
        assert content.get_token() is False
        assert content.get_license_server() is False
        assert content.get_photo() is None
        assert content.get_photo_vertical() is None
        assert content.get_photo_horizontal() is None
        assert content.get_season() is None

    def test_all_getters_return_none_or_false_for_none_content(self):
        """When content is None, all getters should handle TypeError gracefully."""
        content = _create_content_with_data(None)
        assert content.get_page_type() is None
        assert content.get_id() is None
        assert content.get_heading() is None
        assert content.get_subheading() is None
        assert content.get_lead() is None
        assert content.get_body() is None
        assert content.has_next() is None
        assert content.get_primary_category_id() is None
        assert content.get_seasonlist_type() is None
        assert content.get_media_type() is None
        assert content.get_hls() is None
        assert content.get_dash() is None
        assert content.get_file() is None
        assert content.get_subtitles() is None
        assert content.get_drm() is False
        assert content.get_token() is False
        assert content.get_license_server() is False
        assert content.get_photo() is None
        assert content.get_photo_vertical() is None
        assert content.get_photo_horizontal() is None
        assert content.get_season() is None

    def test_content_with_no_medias_key(self):
        """mainContent exists but has no medias key."""
        data = {'data': {'mainContent': {}, 'pageType': 'test'}}
        content = _create_content_with_data(data)
        assert content.get_page_type() == 'test'
        assert content.get_media_type() is None
        assert content.get_hls() is None
        assert content.get_dash() is None
        assert content.get_file() is None
        assert content.get_subtitles() is None
        assert content.get_drm() is False
        assert content.get_token() is False

    def test_content_with_empty_medias_list(self):
        """mainContent has medias as empty list."""
        data = {'data': {'mainContent': {'medias': []}}}
        content = _create_content_with_data(data)
        assert content.get_media_type() is None
        assert content.get_hls() is None
        assert content.get_drm() is False

    def test_season_item_without_contents_key(self):
        """Season items beyond the active one lack the 'contents' key."""
        content, _ = _create_content_with_fixture('content_episode.json')
        seasons = content.get_season()
        # Season 22 (index 1) has no 'contents' key
        second_season = seasons[1]
        assert content.get_item_contents(second_season) is None
        # But other fields work
        assert content.get_item_id(second_season) == 22
        assert content.get_item_name(second_season) == '22'
        assert content.get_item_primaryid(second_season) == 1609578101


# ---------------------------------------------------------------------------
# Cross-fixture validation tests
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestCrossFixtureComparison:
    """Tests that validate differences across fixture types."""

    @pytest.mark.parametrize('fixture_file,expected', [
        ('content_episode.json', True),
        ('content_series.json', None),
        ('content_movie.json', None),
    ])
    def test_has_next_across_fixtures(self, fixture_file, expected):
        content, _ = _create_content_with_fixture(fixture_file)
        assert content.has_next() is expected

    @pytest.mark.parametrize('fixture_file,has_seasons', [
        ('content_episode.json', True),
        ('content_series.json', True),
        ('content_movie.json', False),
    ])
    def test_season_availability(self, fixture_file, has_seasons):
        content, _ = _create_content_with_fixture(fixture_file)
        seasons = content.get_season()
        if has_seasons:
            assert seasons is not None
            assert len(seasons) > 0
        else:
            assert seasons is None

    @pytest.mark.parametrize('fixture_file,has_horizontal', [
        ('content_episode.json', True),
        ('content_series.json', True),
        ('content_movie.json', False),
    ])
    def test_horizontal_photo_availability(self, fixture_file, has_horizontal):
        """Movie fixture has empty horizontalPhotos list."""
        content, _ = _create_content_with_fixture(fixture_file)
        photo = content.get_photo_horizontal()
        if has_horizontal:
            assert photo is not None
        else:
            assert photo is None
