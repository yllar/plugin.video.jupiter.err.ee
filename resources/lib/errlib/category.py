"""Category module for browsing ERR content categories."""
from . import helpers
from .constants import (
    ERR_API_BASEURL,
    ERR_API_VERSION,
    EMPTYSTRING,
    DEFAULT_VERTICAL_PHOTO,
    PHOTO_TYPE_STANDARD
)


class Category:
    """Handles fetching and parsing of category content."""

    def __init__(self, categoryid):
        """Initialize category with given category ID.

        Args:
            categoryid: Category URL identifier
        """
        self.domain = 'jupiter.err.ee'
        self.url = f'{ERR_API_BASEURL}{ERR_API_VERSION}/category/getByUrl?url={categoryid}&domain={self.domain}'
        self.content = helpers.download_url(self.url).json()

    def get_categories(self):
        """Get list of category headers, excluding 'Jätka' items.

        Returns:
            List of category header strings
        """
        categories = []
        for category in self.content['data']['category']['frontPage']:
            # Filter out "Jätka" (Continue) items - no session support
            if 'Jätka' not in category['header']:
                categories.append(category['header'])

        return categories

    def get_category_items(self, category=''):
        """Get items for a specific category.

        Args:
            category: Category header name to filter by

        Returns:
            List of category items, each containing [id, heading, image_url, plot]
        """
        category_items = []

        for category_list in self.content['data']['category']['frontPage']:
            if category_list['header'] == category:
                for category_list_item in category_list['data']:
                    category_item = []
                    category_item.append(category_list_item['id'])
                    category_item.append(category_list_item['heading'])

                    # Get photo URL with multiple fallbacks using dict.get()
                    photo_url = (
                        category_list_item.get('photos', [{}])[0]
                        .get('photoTypes', {})
                        .get(PHOTO_TYPE_STANDARD, {})
                        .get('url')
                    )

                    if not photo_url:
                        # Fallback to vertical photo
                        vertical_photos = category_list_item.get('verticalPhotos', [])
                        photo_url = vertical_photos[0].get('photoUrlOriginal') if vertical_photos else DEFAULT_VERTICAL_PHOTO

                    category_item.append(photo_url)

                    # Get plot/lead text
                    lead = category_list_item.get('lead', EMPTYSTRING)
                    category_item.append(helpers.strip_tags(lead) if lead else EMPTYSTRING)

                    category_items.append(category_item)

        return category_items
