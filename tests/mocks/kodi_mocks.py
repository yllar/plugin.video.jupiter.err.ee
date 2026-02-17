"""Mock Kodi modules for testing.

This module provides mock implementations of Kodi modules (xbmc, xbmcgui, xbmcaddon, xbmcplugin)
that allow testing plugin code without requiring Kodi to be installed.
"""
from unittest.mock import MagicMock, Mock


class MockListItem:
    """Mock xbmcgui.ListItem for testing."""

    def __init__(self, label='', label2='', path=''):
        self.label = label
        self.label2 = label2
        self.path = path
        self.properties = {}
        self.art = {}
        self.info = {}
        self.subtitles = []
        self.content_lookup = None
        self.mime_type = None

    def setLabel(self, label):
        self.label = label

    def setLabel2(self, label2):
        self.label2 = label2

    def setPath(self, path):
        self.path = path

    def setProperty(self, key, value):
        self.properties[key] = value

    def getProperty(self, key):
        return self.properties.get(key, '')

    def setArt(self, art_dict):
        self.art.update(art_dict)

    def setInfo(self, type, infoLabels):
        if type not in self.info:
            self.info[type] = {}
        self.info[type].update(infoLabels)

    def setSubtitles(self, subtitles):
        self.subtitles = subtitles

    def setContentLookup(self, enable):
        self.content_lookup = enable

    def setMimeType(self, mime_type):
        self.mime_type = mime_type


class MockKeyboard:
    """Mock xbmc.Keyboard for testing."""

    def __init__(self, default='', heading=''):
        self.default = default
        self.heading = heading
        self.text = default
        self.confirmed = False

    def doModal(self):
        """Simulate showing keyboard - does nothing in tests."""
        pass

    def isConfirmed(self):
        return self.confirmed

    def getText(self):
        return self.text

    def setConfirmed(self, confirmed):
        """Test helper to set confirmation state."""
        self.confirmed = confirmed

    def setText(self, text):
        """Test helper to set entered text."""
        self.text = text


class MockAddon:
    """Mock xbmcaddon.Addon for testing."""

    def __init__(self, id='plugin.video.jupiter.err.ee'):
        self.id = id
        self.settings = {}
        self.strings = {}

    def getSetting(self, id):
        return self.settings.get(id, '')

    def setSetting(self, id, value):
        self.settings[id] = value

    def getLocalizedString(self, id):
        return self.strings.get(id, f'String_{id}')

    def setLocalizedString(self, id, value):
        """Test helper to set localized strings."""
        self.strings[id] = value

    def getAddonInfo(self, id):
        info = {
            'id': self.id,
            'name': 'Jupiter',
            'version': '0.0.9',
            'path': 'd:/dev/plugin.video.jupiter.err.ee',
            'profile': 'd:/dev/plugin.video.jupiter.err.ee/profile',
            'type': 'xbmc.python.pluginsource'
        }
        return info.get(id, '')


class MockXBMC:
    """Mock xbmc module."""

    # Log levels
    LOGDEBUG = 0
    LOGINFO = 1
    LOGWARNING = 2
    LOGERROR = 3
    LOGFATAL = 4

    def __init__(self):
        self.logs = []
        self.info_labels = {
            'System.BuildVersion': '19.5.0'
        }

    def log(self, msg, level=LOGDEBUG):
        self.logs.append({'msg': msg, 'level': level})

    def getInfoLabel(self, label):
        return self.info_labels.get(label, '')

    def Keyboard(self, default='', heading=''):
        return MockKeyboard(default, heading)


class MockXBMCGUI:
    """Mock xbmcgui module."""

    def __init__(self):
        pass

    def ListItem(self, label='', label2='', path=''):
        return MockListItem(label, label2, path)


class MockXBMCAddon:
    """Mock xbmcaddon module."""

    def __init__(self):
        pass

    def Addon(self, id='plugin.video.jupiter.err.ee'):
        return MockAddon(id)


class MockXBMCPlugin:
    """Mock xbmcplugin module."""

    # Content types
    CONTENT_NONE = 'none'
    CONTENT_MOVIES = 'movies'
    CONTENT_EPISODES = 'episodes'
    CONTENT_VIDEOS = 'videos'

    def __init__(self):
        self.directory_items = []
        self.ended_directories = []
        self.succeeded_directories = []
        self.content_type = {}

    def addDirectoryItem(self, handle, url, listitem, isFolder=True):
        self.directory_items.append({
            'handle': handle,
            'url': url,
            'listitem': listitem,
            'isFolder': isFolder
        })

    def addDirectoryItems(self, handle, items, totalItems=0):
        for item in items:
            url, listitem, isFolder = item
            self.addDirectoryItem(handle, url, listitem, isFolder)

    def endOfDirectory(self, handle, succeeded=True, updateListing=False, cacheToDisc=True):
        self.ended_directories.append({
            'handle': handle,
            'succeeded': succeeded,
            'updateListing': updateListing,
            'cacheToDisc': cacheToDisc
        })
        if succeeded:
            self.succeeded_directories.append(handle)

    def setContent(self, handle, content):
        self.content_type[handle] = content

    def reset(self):
        """Test helper to reset state."""
        self.directory_items = []
        self.ended_directories = []
        self.succeeded_directories = []
        self.content_type = {}


class MockInputstreamHelper:
    """Mock inputstreamhelper.Helper for testing."""

    def __init__(self, protocol, drm=''):
        self.protocol = protocol
        self.drm = drm
        self.inputstream_addon = 'inputstream.adaptive'

    def check_inputstream(self):
        return True


def setup_kodi_mocks():
    """Setup all Kodi mocks for testing.

    This function should be called in conftest.py to inject mocks
    before any plugin code is imported.

    Returns:
        tuple: (xbmc_mock, xbmcgui_mock, xbmcaddon_mock, xbmcplugin_mock, inputstreamhelper_mock)
    """
    import sys

    # Create mock instances
    xbmc_mock = MockXBMC()
    xbmcgui_mock = MockXBMCGUI()
    xbmcaddon_mock = MockXBMCAddon()
    xbmcplugin_mock = MockXBMCPlugin()

    # Inject into sys.modules
    sys.modules['xbmc'] = xbmc_mock
    sys.modules['xbmcgui'] = xbmcgui_mock
    sys.modules['xbmcaddon'] = xbmcaddon_mock
    sys.modules['xbmcplugin'] = xbmcplugin_mock

    # Mock inputstreamhelper
    inputstreamhelper_module = MagicMock()
    inputstreamhelper_module.Helper = MockInputstreamHelper
    sys.modules['inputstreamhelper'] = inputstreamhelper_module

    return xbmc_mock, xbmcgui_mock, xbmcaddon_mock, xbmcplugin_mock, inputstreamhelper_module
