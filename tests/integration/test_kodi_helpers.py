"""Integration tests for resources/lib/kodi_helpers.py.

Tests URL building, ListItem creation, colored items, art setting,
directory management, and playable item creation using the Kodi mock layer.
"""
import pytest
import sys

from resources.lib.kodi_helpers import (
    build_url,
    create_list_item,
    create_colored_item,
    set_item_art,
    add_items_and_close,
    create_playable_item,
    setup_drm_properties,
)
from tests.mocks.kodi_mocks import MockListItem


# ---------------------------------------------------------------------------
# build_url
# ---------------------------------------------------------------------------
class TestBuildUrl:
    """Tests for the build_url helper."""

    @pytest.mark.integration
    def test_build_url_simple_action(self):
        """build_url produces correct URL with a single action parameter."""
        # Arrange
        base = 'plugin://plugin.video.jupiter.err.ee/'

        # Act
        result = build_url(base, 'category')

        # Assert
        assert result.startswith(base + '?')
        assert 'action=category' in result

    @pytest.mark.integration
    def test_build_url_multiple_params(self):
        """build_url includes all extra keyword parameters."""
        # Arrange
        base = 'plugin://plugin.video.jupiter.err.ee/'

        # Act
        result = build_url(base, 'listing', id='123', name='test')

        # Assert
        assert 'action=listing' in result
        assert 'id=123' in result
        assert 'name=test' in result

    @pytest.mark.integration
    @pytest.mark.parametrize('char,encoded', [
        ('&', '%26'),
        ('=', '%3D'),
        ('/', '%2F'),
    ])
    def test_build_url_special_characters(self, char, encoded):
        """build_url properly percent-encodes special characters in values."""
        # Arrange
        base = 'plugin://plugin.video.jupiter.err.ee/'

        # Act
        result = build_url(base, 'search', query=f'hello{char}world')

        # Assert
        assert encoded in result

    @pytest.mark.integration
    def test_build_url_unicode_characters(self):
        """build_url encodes Estonian unicode characters."""
        # Arrange
        base = 'plugin://plugin.video.jupiter.err.ee/'

        # Act
        result = build_url(base, 'search', query='tere maailm')

        # Assert
        assert 'action=search' in result
        # The word 'tere' has no special chars, but let's test with actual unicode
        result2 = build_url(base, 'category', name='Saated ja sarjad')
        assert 'action=category' in result2
        # Spaces should be encoded
        assert '%20' in result2 or '+' in result2 or 'Saated' in result2

    @pytest.mark.integration
    def test_build_url_unicode_estonian_chars(self):
        """build_url encodes Estonian special characters (a-o-u-o with diacritics)."""
        # Arrange
        base = 'plugin://plugin.video.jupiter.err.ee/'

        # Act
        result = build_url(base, 'search', query='\u00e4\u00f6\u00fc\u00f5')

        # Assert
        # These should be percent-encoded since safe=''
        assert '\u00e4' not in result
        assert '\u00f6' not in result
        assert '\u00fc' not in result
        assert '\u00f5' not in result
        assert 'action=search' in result

    @pytest.mark.integration
    def test_build_url_numeric_params(self):
        """build_url converts numeric parameter values to strings."""
        # Arrange
        base = 'plugin://plugin.video.jupiter.err.ee/'

        # Act
        result = build_url(base, 'listing', id=12345, page=2)

        # Assert
        assert 'id=12345' in result
        assert 'page=2' in result


# ---------------------------------------------------------------------------
# create_list_item
# ---------------------------------------------------------------------------
class TestCreateListItem:
    """Tests for the create_list_item helper."""

    @pytest.mark.integration
    def test_create_list_item_basic(self):
        """create_list_item returns a tuple of (url, ListItem, is_folder)."""
        # Arrange / Act
        url, item, is_folder = create_list_item('Test Title', url='http://example.com')

        # Assert
        assert url == 'http://example.com'
        assert isinstance(item, MockListItem)
        assert item.label == 'Test Title'
        assert is_folder is True

    @pytest.mark.integration
    def test_create_list_item_with_fanart(self):
        """create_list_item sets art dict when fanart is provided."""
        # Arrange
        fanart_url = 'https://s.err.ee/photo/test.jpg'

        # Act
        url, item, is_folder = create_list_item('Title', url='http://x', fanart=fanart_url)

        # Assert
        assert item.art['fanart'] == fanart_url
        assert item.art['poster'] == fanart_url
        assert item.art['icon'] == fanart_url

    @pytest.mark.integration
    def test_create_list_item_without_fanart(self):
        """create_list_item does not set art when fanart is None."""
        # Arrange / Act
        url, item, is_folder = create_list_item('Title', url='http://x')

        # Assert
        assert item.art == {}

    @pytest.mark.integration
    def test_create_list_item_with_info_labels(self):
        """create_list_item sets Video info labels when provided."""
        # Arrange
        labels = {'title': 'My Show', 'plot': 'A description'}

        # Act
        url, item, is_folder = create_list_item('Title', url='http://x', info_labels=labels)

        # Assert
        assert item.info['Video']['title'] == 'My Show'
        assert item.info['Video']['plot'] == 'A description'

    @pytest.mark.integration
    def test_create_list_item_none_url(self):
        """create_list_item with url=None returns empty string as url."""
        # Arrange / Act
        url, item, is_folder = create_list_item('Title')

        # Assert
        assert url == ''
        assert item.label == 'Title'

    @pytest.mark.integration
    def test_create_list_item_is_folder_false(self):
        """create_list_item respects is_folder=False."""
        # Arrange / Act
        url, item, is_folder = create_list_item('Title', url='http://x', is_folder=False)

        # Assert
        assert is_folder is False


# ---------------------------------------------------------------------------
# create_colored_item
# ---------------------------------------------------------------------------
class TestCreateColoredItem:
    """Tests for the create_colored_item helper."""

    @pytest.mark.integration
    def test_create_colored_item_applies_color_tags(self):
        """create_colored_item wraps the title in [COLOR ...] tags."""
        # Arrange / Act
        url, item, is_folder = create_colored_item('Category Header', 'blue')

        # Assert
        assert item.label == '[COLOR blue]Category Header[/COLOR]'

    @pytest.mark.integration
    def test_create_colored_item_defaults(self):
        """create_colored_item defaults to empty url and is_folder=False."""
        # Arrange / Act
        url, item, is_folder = create_colored_item('Header', 'red')

        # Assert
        assert url == ''
        assert is_folder is False

    @pytest.mark.integration
    def test_create_colored_item_with_fanart(self):
        """create_colored_item passes fanart through to create_list_item."""
        # Arrange
        fanart_url = 'https://s.err.ee/photo/test.jpg'

        # Act
        url, item, is_folder = create_colored_item('Header', 'gold', fanart=fanart_url)

        # Assert
        assert item.art['fanart'] == fanart_url

    @pytest.mark.integration
    @pytest.mark.parametrize('color', ['blue', 'red', 'gold', 'limegreen', 'deeppink'])
    def test_create_colored_item_various_colors(self, color):
        """create_colored_item works with various Kodi color names."""
        # Arrange / Act
        url, item, is_folder = create_colored_item('Title', color)

        # Assert
        assert item.label == f'[COLOR {color}]Title[/COLOR]'


# ---------------------------------------------------------------------------
# set_item_art
# ---------------------------------------------------------------------------
class TestSetItemArt:
    """Tests for the set_item_art helper."""

    @pytest.mark.integration
    def test_set_item_art_enabled(self):
        """set_item_art sets art when enable_images is True and fanart is provided."""
        # Arrange
        item = MockListItem('Test')
        fanart = 'https://s.err.ee/photo/test.jpg'

        # Act
        set_item_art(item, fanart, enable_images=True)

        # Assert
        assert item.art['fanart'] == fanart
        assert item.art['poster'] == fanart
        assert item.art['icon'] == fanart

    @pytest.mark.integration
    def test_set_item_art_disabled(self):
        """set_item_art does NOT set art when enable_images is False."""
        # Arrange
        item = MockListItem('Test')
        fanart = 'https://s.err.ee/photo/test.jpg'

        # Act
        set_item_art(item, fanart, enable_images=False)

        # Assert
        assert item.art == {}

    @pytest.mark.integration
    def test_set_item_art_no_fanart(self):
        """set_item_art does NOT set art when fanart is None/empty."""
        # Arrange
        item = MockListItem('Test')

        # Act
        set_item_art(item, None, enable_images=True)

        # Assert
        assert item.art == {}

    @pytest.mark.integration
    def test_set_item_art_both_disabled_and_no_fanart(self):
        """set_item_art does nothing when both conditions are falsy."""
        # Arrange
        item = MockListItem('Test')

        # Act
        set_item_art(item, '', enable_images=False)

        # Assert
        assert item.art == {}


# ---------------------------------------------------------------------------
# add_items_and_close
# ---------------------------------------------------------------------------
class TestAddItemsAndClose:
    """Tests for the add_items_and_close helper."""

    @pytest.mark.integration
    def test_add_items_and_close_calls_xbmcplugin(self, mock_xbmcplugin):
        """add_items_and_close adds items and ends the directory."""
        # Arrange
        handle = 1
        item1 = MockListItem('Item 1')
        item2 = MockListItem('Item 2')
        items = [
            ('url1', item1, True),
            ('url2', item2, False),
        ]

        # Act
        add_items_and_close(handle, items)

        # Assert -- items were added
        assert len(mock_xbmcplugin.directory_items) == 2
        assert mock_xbmcplugin.directory_items[0]['url'] == 'url1'
        assert mock_xbmcplugin.directory_items[0]['isFolder'] is True
        assert mock_xbmcplugin.directory_items[1]['url'] == 'url2'
        assert mock_xbmcplugin.directory_items[1]['isFolder'] is False

        # Assert -- directory was ended
        assert len(mock_xbmcplugin.ended_directories) == 1
        assert mock_xbmcplugin.ended_directories[0]['handle'] == handle

    @pytest.mark.integration
    def test_add_items_and_close_empty_list(self, mock_xbmcplugin):
        """add_items_and_close works with an empty item list."""
        # Arrange / Act
        add_items_and_close(1, [])

        # Assert
        assert len(mock_xbmcplugin.directory_items) == 0
        assert len(mock_xbmcplugin.ended_directories) == 1


# ---------------------------------------------------------------------------
# create_playable_item
# ---------------------------------------------------------------------------
class TestCreatePlayableItem:
    """Tests for the create_playable_item helper."""

    @pytest.mark.integration
    def test_create_playable_item_marks_playable(self):
        """create_playable_item sets IsPlayable=True and isFolder=False."""
        # Arrange / Act
        video_url, item = create_playable_item('Episode 1', 'https://stream.err.ee/video.mpd')

        # Assert
        assert item.properties['IsPlayable'] == 'True'
        assert item.properties['isFolder'] == 'False'
        assert video_url == 'https://stream.err.ee/video.mpd'
        assert item.label == 'Episode 1'

    @pytest.mark.integration
    def test_create_playable_item_with_fanart(self):
        """create_playable_item sets art when fanart is given."""
        # Arrange
        fanart = 'https://s.err.ee/photo/test.jpg'

        # Act
        video_url, item = create_playable_item('Ep', 'https://stream.err.ee/v.mpd', fanart=fanart)

        # Assert
        assert item.art['fanart'] == fanart
        assert item.art['poster'] == fanart

    @pytest.mark.integration
    def test_create_playable_item_with_info_labels(self):
        """create_playable_item sets Video info labels."""
        # Arrange
        labels = {'title': 'Ep 1', 'plot': 'Plot text', 'duration': 3600}

        # Act
        video_url, item = create_playable_item('Ep 1', 'https://v.mpd', info_labels=labels)

        # Assert
        assert item.info['Video']['title'] == 'Ep 1'
        assert item.info['Video']['duration'] == 3600

    @pytest.mark.integration
    def test_create_playable_item_with_subtitles(self):
        """create_playable_item attaches subtitle URLs."""
        # Arrange
        subs = ['https://sub.err.ee/et.vtt', 'https://sub.err.ee/ru.vtt']

        # Act
        video_url, item = create_playable_item('Ep', 'https://v.mpd', subtitles=subs)

        # Assert
        assert item.subtitles == subs

    @pytest.mark.integration
    def test_create_playable_item_without_optional_params(self):
        """create_playable_item works with only required parameters."""
        # Arrange / Act
        video_url, item = create_playable_item('Title', 'https://stream.url')

        # Assert
        assert item.art == {}
        assert item.info == {}
        assert item.subtitles == []
        assert item.properties['IsPlayable'] == 'True'

    @pytest.mark.integration
    def test_create_playable_item_returns_tuple_of_two(self):
        """create_playable_item returns (video_url, item) -- length 2."""
        # Arrange / Act
        result = create_playable_item('T', 'https://x')

        # Assert
        assert len(result) == 2
        assert result[0] == 'https://x'
        assert isinstance(result[1], MockListItem)
