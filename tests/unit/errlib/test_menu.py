"""Unit tests for resources/lib/errlib/menu.py.

Tests Menu initialization with default and custom IDs,
get_menu_items return value, and menu item structure.
"""
import json
import os
import pytest
from unittest.mock import patch, Mock

from resources.lib.errlib.constants import DEFAULT_MENU_ID

# Path to the real fixture file
FIXTURE_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'fixtures', 'api_responses')


def _load_fixture(filename):
    """Load a JSON fixture file and return parsed data."""
    filepath = os.path.join(FIXTURE_DIR, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def _make_menu(fixture_data, menuid=None):
    """Create a Menu instance with mocked download_url returning fixture_data.

    Args:
        fixture_data: Parsed JSON to return from mock download_url
        menuid: Optional menu ID; when None, use default ID
    """
    mock_response = Mock()
    mock_response.json.return_value = fixture_data
    with patch('resources.lib.errlib.menu.download_url', return_value=mock_response):
        from resources.lib.errlib.menu import Menu
        if menuid is not None:
            return Menu(menuid=menuid)
        return Menu()


# ---------------------------------------------------------------------------
# Menu.__init__
# ---------------------------------------------------------------------------
class TestMenuInit:
    """Tests for Menu initialization."""

    @pytest.mark.unit
    def test_menu_init_uses_default_id(self):
        """Menu() without arguments uses DEFAULT_MENU_ID (555)."""
        # Arrange
        fixture = _load_fixture('menu_main.json')
        mock_response = Mock()
        mock_response.json.return_value = fixture

        with patch('resources.lib.errlib.menu.download_url', return_value=mock_response) as mock_dl:
            from resources.lib.errlib.menu import Menu

            # Act
            menu = Menu()

            # Assert
            called_url = mock_dl.call_args[0][0]
            assert f'menuId={DEFAULT_MENU_ID}' in called_url

    @pytest.mark.unit
    def test_menu_init_uses_custom_id(self):
        """Menu(menuid=999) builds URL with the custom ID."""
        # Arrange
        fixture = {'data': {'items': []}}
        mock_response = Mock()
        mock_response.json.return_value = fixture

        with patch('resources.lib.errlib.menu.download_url', return_value=mock_response) as mock_dl:
            from resources.lib.errlib.menu import Menu

            # Act
            menu = Menu(menuid=999)

            # Assert
            called_url = mock_dl.call_args[0][0]
            assert 'menuId=999' in called_url

    @pytest.mark.unit
    def test_menu_url_format(self):
        """Menu URL follows the expected API pattern."""
        # Arrange
        fixture = {'data': {'items': []}}
        mock_response = Mock()
        mock_response.json.return_value = fixture

        with patch('resources.lib.errlib.menu.download_url', return_value=mock_response) as mock_dl:
            from resources.lib.errlib.menu import Menu

            # Act
            menu = Menu()

            # Assert
            called_url = mock_dl.call_args[0][0]
            assert 'https://services.err.ee/api/' in called_url
            assert 'menu/getMenuById' in called_url

    @pytest.mark.unit
    def test_menu_stores_content(self):
        """Menu stores the parsed JSON response as self.content."""
        # Arrange
        fixture = _load_fixture('menu_main.json')
        menu = _make_menu(fixture)

        # Assert
        assert menu.content == fixture


# ---------------------------------------------------------------------------
# get_menu_items
# ---------------------------------------------------------------------------
class TestGetMenuItems:
    """Tests for Menu.get_menu_items()."""

    @pytest.mark.unit
    def test_get_menu_items_returns_items_list(self):
        """get_menu_items returns data.items from the fixture."""
        # Arrange
        fixture = _load_fixture('menu_main.json')
        menu = _make_menu(fixture)

        # Act
        items = menu.get_menu_items()

        # Assert
        assert isinstance(items, list)
        assert len(items) == 2  # Video and Audio in the fixture

    @pytest.mark.unit
    def test_get_menu_items_first_item_is_video(self):
        """The first menu item is 'Video' according to the fixture."""
        # Arrange
        fixture = _load_fixture('menu_main.json')
        menu = _make_menu(fixture)

        # Act
        items = menu.get_menu_items()

        # Assert
        assert items[0]['name'] == 'Video'

    @pytest.mark.unit
    def test_get_menu_items_second_item_is_audio(self):
        """The second menu item is 'Audio' according to the fixture."""
        # Arrange
        fixture = _load_fixture('menu_main.json')
        menu = _make_menu(fixture)

        # Act
        items = menu.get_menu_items()

        # Assert
        assert items[1]['name'] == 'Audio'

    @pytest.mark.unit
    @pytest.mark.parametrize('expected_key', ['id', 'name', 'link', 'kids_count', 'kids'])
    def test_get_menu_items_have_expected_keys(self, expected_key):
        """Each menu item contains the expected structural keys."""
        # Arrange
        fixture = _load_fixture('menu_main.json')
        menu = _make_menu(fixture)

        # Act
        items = menu.get_menu_items()

        # Assert
        for item in items:
            assert expected_key in item, f'Missing key: {expected_key}'

    @pytest.mark.unit
    def test_get_menu_items_video_has_kids(self):
        """Video menu item has children (kids) with correct count."""
        # Arrange
        fixture = _load_fixture('menu_main.json')
        menu = _make_menu(fixture)

        # Act
        items = menu.get_menu_items()
        video_item = items[0]

        # Assert
        assert video_item['kids_count'] == len(video_item['kids'])
        assert video_item['kids_count'] == 7

    @pytest.mark.unit
    def test_get_menu_items_kid_structure(self):
        """Each kid item has id, name, link, and kids_count."""
        # Arrange
        fixture = _load_fixture('menu_main.json')
        menu = _make_menu(fixture)

        # Act
        items = menu.get_menu_items()
        kids = items[0]['kids']

        # Assert
        for kid in kids:
            assert 'id' in kid
            assert 'name' in kid
            assert 'link' in kid
            assert 'kids_count' in kid

    @pytest.mark.unit
    def test_get_menu_items_parent_id_matches(self):
        """Parent ID of the first menu item matches DEFAULT_MENU_ID."""
        # Arrange
        fixture = _load_fixture('menu_main.json')
        menu = _make_menu(fixture)

        # Act
        items = menu.get_menu_items()

        # Assert
        assert items[0]['parentId'] == DEFAULT_MENU_ID

    @pytest.mark.unit
    def test_get_menu_items_empty(self):
        """get_menu_items returns empty list when no items exist."""
        # Arrange
        fixture = {'data': {'items': []}}
        menu = _make_menu(fixture)

        # Act
        items = menu.get_menu_items()

        # Assert
        assert items == []
