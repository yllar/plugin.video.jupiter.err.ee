"""Settings cache for efficient access to addon settings."""
from resources.lib.errlib import helpers


class SettingsCache:
    """Cache addon settings to avoid repeated I/O operations.

    Reads all commonly accessed settings once and provides them as attributes.
    This significantly improves performance by eliminating redundant getSetting() calls
    that would otherwise occur in loops and repeated function calls.
    """

    def __init__(self, addon):
        """Initialize settings cache from addon instance.

        Args:
            addon: xbmcaddon.Addon instance
        """
        # Color settings for UI elements
        self.colour_category = helpers.get_colour(addon.getSetting('colourCategory'))
        self.colour_season = helpers.get_colour(addon.getSetting('colourSeason'))

        # Image loading preference
        self.enable_images = addon.getSetting('enableImages') == 'true'

        # Subtitle language preferences
        self.primary_language = helpers.get_subtitle_language(addon.getSetting('primaryLanguage'))
        self.secondary_language = helpers.get_subtitle_language(addon.getSetting('secondaryLanguage'))

    def get_subtitle_languages(self):
        """Get list of configured subtitle languages.

        Returns:
            List of language codes [primary, secondary]
        """
        return [self.primary_language, self.secondary_language]
