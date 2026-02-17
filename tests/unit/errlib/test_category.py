"""Unit tests for resources/lib/errlib/category.py.

Tests category listing, item extraction, photo fallback chain,
lead-text stripping, and handling of empty/missing data.
"""
import json
import os
import pytest
from unittest.mock import patch, Mock

from resources.lib.errlib.constants import (
    DEFAULT_VERTICAL_PHOTO,
    PHOTO_TYPE_STANDARD,
)

# Path to the real fixture file
FIXTURE_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'fixtures', 'api_responses')
CATEGORY_FIXTURE = os.path.join(FIXTURE_DIR, 'category_video.json')


def _load_fixture(filename):
    """Load a JSON fixture file and return parsed data."""
    filepath = os.path.join(FIXTURE_DIR, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def _make_category(fixture_data):
    """Create a Category instance with mocked download_url returning fixture_data."""
    mock_response = Mock()
    mock_response.json.return_value = fixture_data
    with patch('resources.lib.errlib.helpers.download_url', return_value=mock_response):
        from resources.lib.errlib.category import Category
        return Category('v-saated')


# ---------------------------------------------------------------------------
# get_categories
# ---------------------------------------------------------------------------
class TestGetCategories:
    """Tests for Category.get_categories()."""

    @pytest.mark.unit
    def test_get_categories_returns_header_strings(self):
        """get_categories returns a list of category header strings."""
        # Arrange
        fixture = _load_fixture('category_video.json')
        cat = _make_category(fixture)

        # Act
        categories = cat.get_categories()

        # Assert
        assert isinstance(categories, list)
        assert len(categories) > 0
        for header in categories:
            assert isinstance(header, str)

    @pytest.mark.unit
    def test_get_categories_filters_out_jatka(self):
        """get_categories excludes items whose header contains 'Jatka'."""
        # Arrange
        fixture = _load_fixture('category_video.json')
        cat = _make_category(fixture)

        # Act
        categories = cat.get_categories()

        # Assert -- none of the returned headers should contain 'Jatka'
        for header in categories:
            assert 'J\u00e4tka' not in header

    @pytest.mark.unit
    def test_get_categories_includes_known_headers(self):
        """get_categories includes expected headers from the fixture."""
        # Arrange
        fixture = _load_fixture('category_video.json')
        cat = _make_category(fixture)

        # Act
        categories = cat.get_categories()

        # Assert -- these headers are present in the fixture
        assert 'Uued saated' in categories
        assert 'Uudised ja magasinid' in categories

    @pytest.mark.unit
    def test_get_categories_empty_front_page(self):
        """get_categories returns empty list when frontPage is empty."""
        # Arrange
        fixture = {
            'data': {
                'category': {
                    'frontPage': []
                }
            }
        }
        cat = _make_category(fixture)

        # Act
        categories = cat.get_categories()

        # Assert
        assert categories == []

    @pytest.mark.unit
    def test_get_categories_all_jatka_filtered(self):
        """get_categories returns empty list when every header is 'Jatka'."""
        # Arrange
        fixture = {
            'data': {
                'category': {
                    'frontPage': [
                        {'header': 'J\u00e4tka vaatamist', 'data': []},
                        {'header': 'J\u00e4tka kuulamist', 'data': []},
                    ]
                }
            }
        }
        cat = _make_category(fixture)

        # Act
        categories = cat.get_categories()

        # Assert
        assert categories == []


# ---------------------------------------------------------------------------
# get_category_items
# ---------------------------------------------------------------------------
class TestGetCategoryItems:
    """Tests for Category.get_category_items()."""

    @pytest.mark.unit
    def test_get_category_items_returns_correct_structure(self):
        """Each item is [id, heading, photo_url, plot]."""
        # Arrange
        fixture = _load_fixture('category_video.json')
        cat = _make_category(fixture)
        categories = cat.get_categories()
        # Pick the first non-empty category
        target_category = categories[0] if categories else None
        assert target_category is not None

        # Act
        items = cat.get_category_items(target_category)

        # Assert
        assert isinstance(items, list)
        assert len(items) > 0
        for item in items:
            assert len(item) == 4
            assert isinstance(item[0], int)       # id
            assert isinstance(item[1], str)       # heading
            assert isinstance(item[2], str)       # photo_url
            assert isinstance(item[3], str)       # plot

    @pytest.mark.unit
    def test_get_category_items_nonexistent_category(self):
        """get_category_items returns empty list for unknown category header."""
        # Arrange
        fixture = _load_fixture('category_video.json')
        cat = _make_category(fixture)

        # Act
        items = cat.get_category_items('This Category Does Not Exist')

        # Assert
        assert items == []

    @pytest.mark.unit
    def test_get_category_items_photo_type_17_preferred(self):
        """Photo URL should come from photoTypes['17'] when available."""
        # Arrange
        fixture = {
            'data': {
                'category': {
                    'frontPage': [
                        {
                            'header': 'Test',
                            'data': [
                                {
                                    'id': 1,
                                    'heading': 'Show',
                                    'photos': [{
                                        'photoTypes': {
                                            PHOTO_TYPE_STANDARD: {
                                                'url': 'https://photo17.jpg'
                                            }
                                        }
                                    }],
                                    'lead': '',
                                }
                            ]
                        }
                    ]
                }
            }
        }
        cat = _make_category(fixture)

        # Act
        items = cat.get_category_items('Test')

        # Assert
        assert items[0][2] == 'https://photo17.jpg'

    @pytest.mark.unit
    def test_get_category_items_photo_fallback_to_vertical(self):
        """When photoTypes['17'] is missing, fall back to verticalPhotos."""
        # Arrange
        fixture = {
            'data': {
                'category': {
                    'frontPage': [
                        {
                            'header': 'Test',
                            'data': [
                                {
                                    'id': 2,
                                    'heading': 'Show',
                                    'photos': [{}],  # No photoTypes
                                    'verticalPhotos': [{
                                        'photoUrlOriginal': 'https://vertical.jpg'
                                    }],
                                    'lead': '',
                                }
                            ]
                        }
                    ]
                }
            }
        }
        cat = _make_category(fixture)

        # Act
        items = cat.get_category_items('Test')

        # Assert
        assert items[0][2] == 'https://vertical.jpg'

    @pytest.mark.unit
    def test_get_category_items_photo_fallback_to_default(self):
        """When both photoTypes and verticalPhotos are missing, use DEFAULT_VERTICAL_PHOTO."""
        # Arrange
        fixture = {
            'data': {
                'category': {
                    'frontPage': [
                        {
                            'header': 'Test',
                            'data': [
                                {
                                    'id': 3,
                                    'heading': 'Show',
                                    'photos': [{}],
                                    'verticalPhotos': [],
                                    'lead': '',
                                }
                            ]
                        }
                    ]
                }
            }
        }
        cat = _make_category(fixture)

        # Act
        items = cat.get_category_items('Test')

        # Assert
        assert items[0][2] == DEFAULT_VERTICAL_PHOTO

    @pytest.mark.unit
    def test_get_category_items_lead_text_stripping(self):
        """HTML tags in lead text are stripped."""
        # Arrange
        fixture = {
            'data': {
                'category': {
                    'frontPage': [
                        {
                            'header': 'Test',
                            'data': [
                                {
                                    'id': 4,
                                    'heading': 'Show',
                                    'photos': [{
                                        'photoTypes': {
                                            PHOTO_TYPE_STANDARD: {'url': 'https://x.jpg'}
                                        }
                                    }],
                                    'lead': '<p>Hello <b>world</b></p>',
                                }
                            ]
                        }
                    ]
                }
            }
        }
        cat = _make_category(fixture)

        # Act
        items = cat.get_category_items('Test')

        # Assert
        assert '<p>' not in items[0][3]
        assert '<b>' not in items[0][3]
        assert 'Hello world' in items[0][3]

    @pytest.mark.unit
    def test_get_category_items_empty_lead(self):
        """Empty lead returns empty string for plot."""
        # Arrange
        fixture = {
            'data': {
                'category': {
                    'frontPage': [
                        {
                            'header': 'Test',
                            'data': [
                                {
                                    'id': 5,
                                    'heading': 'Show',
                                    'photos': [{
                                        'photoTypes': {
                                            PHOTO_TYPE_STANDARD: {'url': 'https://x.jpg'}
                                        }
                                    }],
                                    'lead': '',
                                }
                            ]
                        }
                    ]
                }
            }
        }
        cat = _make_category(fixture)

        # Act
        items = cat.get_category_items('Test')

        # Assert
        assert items[0][3] == ''

    @pytest.mark.unit
    def test_get_category_items_missing_lead_key(self):
        """Missing 'lead' key defaults to empty string."""
        # Arrange
        fixture = {
            'data': {
                'category': {
                    'frontPage': [
                        {
                            'header': 'Test',
                            'data': [
                                {
                                    'id': 6,
                                    'heading': 'Show',
                                    'photos': [{
                                        'photoTypes': {
                                            PHOTO_TYPE_STANDARD: {'url': 'https://x.jpg'}
                                        }
                                    }],
                                    # 'lead' key is missing entirely
                                }
                            ]
                        }
                    ]
                }
            }
        }
        cat = _make_category(fixture)

        # Act
        items = cat.get_category_items('Test')

        # Assert
        assert items[0][3] == ''

    @pytest.mark.unit
    def test_get_category_items_empty_data(self):
        """Category with empty data list returns no items."""
        # Arrange
        fixture = {
            'data': {
                'category': {
                    'frontPage': [
                        {
                            'header': 'Empty',
                            'data': []
                        }
                    ]
                }
            }
        }
        cat = _make_category(fixture)

        # Act
        items = cat.get_category_items('Empty')

        # Assert
        assert items == []


# ---------------------------------------------------------------------------
# Category.__init__
# ---------------------------------------------------------------------------
class TestCategoryInit:
    """Tests for Category initialization."""

    @pytest.mark.unit
    def test_category_url_contains_categoryid(self):
        """Category URL includes the provided category ID."""
        # Arrange
        fixture = {'data': {'category': {'frontPage': []}}}
        mock_response = Mock()
        mock_response.json.return_value = fixture

        with patch('resources.lib.errlib.helpers.download_url', return_value=mock_response) as mock_dl:
            from resources.lib.errlib.category import Category

            # Act
            cat = Category('v-saated')

            # Assert
            called_url = mock_dl.call_args[0][0]
            assert 'url=v-saated' in called_url
            assert 'domain=jupiter.err.ee' in called_url

    @pytest.mark.unit
    def test_category_stores_content(self):
        """Category stores the parsed JSON content."""
        # Arrange
        fixture = {'data': {'category': {'frontPage': []}}}
        cat = _make_category(fixture)

        # Assert
        assert cat.content == fixture
