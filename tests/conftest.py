"""Pytest configuration and shared fixtures for Jupiter Kodi Plugin tests."""
import json
import os
import sys
import pytest
from unittest.mock import Mock, patch, MagicMock

# Setup Kodi mocks BEFORE importing any plugin code
from tests.mocks.kodi_mocks import setup_kodi_mocks

# Setup mocks at module load time
xbmc_mock, xbmcgui_mock, xbmcaddon_mock, xbmcplugin_mock, inputstreamhelper_mock = setup_kodi_mocks()


@pytest.fixture
def mock_xbmc():
    """Provide xbmc mock instance."""
    return xbmc_mock


@pytest.fixture
def mock_xbmcgui():
    """Provide xbmcgui mock instance."""
    return xbmcgui_mock


@pytest.fixture
def mock_xbmcaddon():
    """Provide xbmcaddon mock instance."""
    return xbmcaddon_mock


@pytest.fixture
def mock_xbmcplugin():
    """Provide xbmcplugin mock instance."""
    # Reset state before each test
    xbmcplugin_mock.reset()
    return xbmcplugin_mock


@pytest.fixture
def mock_addon():
    """Provide a configured MockAddon instance."""
    addon = xbmcaddon_mock.Addon()
    # Set default settings
    addon.setSetting('colourCategory', '0')  # blue
    addon.setSetting('colourSeason', '1')    # red
    addon.setSetting('enableImages', 'true')
    addon.setSetting('primaryLanguage', '0')  # ET
    addon.setSetting('secondaryLanguage', '2')  # RU
    # Set default localized strings
    addon.setLocalizedString(30012, 'Search')
    addon.setLocalizedString(30013, 'Search')
    addon.setLocalizedString(30014, 'Results')
    return addon


@pytest.fixture
def mock_requests(monkeypatch):
    """Provide a mock for requests.get.

    Returns a mock object that can be configured to return specific responses.

    Example:
        def test_something(mock_requests):
            mock_requests.return_value.json.return_value = {'test': 'data'}
            # Your test code here
    """
    mock = Mock()
    mock.return_value.raise_for_status = Mock()
    monkeypatch.setattr('requests.get', mock)
    return mock


@pytest.fixture
def mock_time_sleep(monkeypatch):
    """Mock time.sleep to speed up retry tests."""
    mock = Mock()
    monkeypatch.setattr('time.sleep', mock)
    return mock


@pytest.fixture
def fixture_path():
    """Return the path to test fixtures directory."""
    return os.path.join(os.path.dirname(__file__), 'fixtures', 'api_responses')


@pytest.fixture
def load_fixture(fixture_path):
    """Provide a function to load JSON fixtures.

    Example:
        def test_something(load_fixture):
            data = load_fixture('content_movie.json')
    """
    def _load(filename):
        filepath = os.path.join(fixture_path, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return _load


@pytest.fixture
def mock_download_url(monkeypatch):
    """Mock the download_url function from helpers.

    Returns a mock that can be configured with response data.

    Example:
        def test_something(mock_download_url):
            mock_download_url.return_value.json.return_value = {'data': 'test'}
    """
    mock = Mock()
    mock.return_value.json = Mock()
    # Need to patch after module is imported
    return mock


@pytest.fixture
def settings_cache_instance(mock_addon):
    """Provide a pre-configured SettingsCache instance."""
    # Import after mocks are set up
    from resources.lib.settings import SettingsCache
    return SettingsCache(mock_addon)


@pytest.fixture
def drm_config():
    """Provide a DRM configuration dictionary for testing."""
    return {
        'is_helper': inputstreamhelper_mock.Helper('mpd', drm='com.widevine.alpha'),
        'kodi_version': 19,
        'protocol': 'mpd',
        'drm': 'com.widevine.alpha',
        'mime_type': 'application/dash+xml'
    }


@pytest.fixture(autouse=True)
def reset_mocks():
    """Automatically reset all mocks before each test."""
    xbmc_mock.logs.clear()
    xbmcplugin_mock.reset()
    yield
    # Cleanup after test
    xbmc_mock.logs.clear()
    xbmcplugin_mock.reset()


# Configure pytest to show full diff for assertion errors
def pytest_configure(config):
    """Pytest configuration hook."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "regression: mark test as a regression test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow (> 1 second)"
    )
