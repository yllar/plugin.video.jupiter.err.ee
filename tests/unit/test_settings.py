"""Tests for SettingsCache in resources/lib/settings.py."""
import pytest
from tests.mocks.kodi_mocks import MockAddon


@pytest.mark.unit
class TestSettingsCache:
    """Tests for settings caching functionality."""

    def _make_addon(self, **overrides):
        """Create a MockAddon with default settings."""
        addon = MockAddon()
        defaults = {
            'colourCategory': '0',   # white
            'colourSeason': '14',    # red
            'enableImages': 'true',
            'primaryLanguage': '0',  # ET
            'secondaryLanguage': '2' # RU
        }
        defaults.update(overrides)
        for k, v in defaults.items():
            addon.setSetting(k, v)
        return addon

    def test_colour_category_mapping(self):
        addon = self._make_addon(colourCategory='7')
        from resources.lib.settings import SettingsCache
        cache = SettingsCache(addon)
        assert cache.colour_category == 'blue'

    def test_colour_season_mapping(self):
        addon = self._make_addon(colourSeason='14')
        from resources.lib.settings import SettingsCache
        cache = SettingsCache(addon)
        assert cache.colour_season == 'red'

    def test_enable_images_true(self):
        addon = self._make_addon(enableImages='true')
        from resources.lib.settings import SettingsCache
        cache = SettingsCache(addon)
        assert cache.enable_images is True

    def test_enable_images_false(self):
        addon = self._make_addon(enableImages='false')
        from resources.lib.settings import SettingsCache
        cache = SettingsCache(addon)
        assert cache.enable_images is False

    def test_enable_images_empty_string(self):
        addon = self._make_addon(enableImages='')
        from resources.lib.settings import SettingsCache
        cache = SettingsCache(addon)
        assert cache.enable_images is False

    def test_primary_language_estonian(self):
        addon = self._make_addon(primaryLanguage='0')
        from resources.lib.settings import SettingsCache
        cache = SettingsCache(addon)
        assert cache.primary_language == 'ET'

    def test_primary_language_voiceover(self):
        addon = self._make_addon(primaryLanguage='1')
        from resources.lib.settings import SettingsCache
        cache = SettingsCache(addon)
        assert cache.primary_language == 'VA'

    def test_secondary_language_russian(self):
        addon = self._make_addon(secondaryLanguage='2')
        from resources.lib.settings import SettingsCache
        cache = SettingsCache(addon)
        assert cache.secondary_language == 'RU'

    def test_get_subtitle_languages_returns_list(self):
        addon = self._make_addon(primaryLanguage='0', secondaryLanguage='2')
        from resources.lib.settings import SettingsCache
        cache = SettingsCache(addon)
        langs = cache.get_subtitle_languages()
        assert isinstance(langs, list)
        assert len(langs) == 2
        assert langs[0] == 'ET'
        assert langs[1] == 'RU'

    def test_all_colour_values(self):
        """Test that all 15 colour settings map correctly."""
        from resources.lib.settings import SettingsCache
        expected = {
            '0': 'white', '1': 'ivory', '2': 'silver', '3': 'gray',
            '4': 'limegreen', '5': 'green', '6': 'lightblue', '7': 'blue',
            '8': 'deeppink', '9': 'turquoise', '10': 'gold', '11': 'yellow',
            '12': 'brown', '13': 'orange', '14': 'red'
        }
        for setting, expected_colour in expected.items():
            addon = self._make_addon(colourCategory=setting)
            cache = SettingsCache(addon)
            assert cache.colour_category == expected_colour, f"Setting {setting} should map to {expected_colour}"
