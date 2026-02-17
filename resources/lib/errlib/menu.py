"""Menu module for retrieving ERR menu structure."""
import json
from .helpers import download_url
from .constants import (
    ERR_API_BASEURL,
    ERR_API_VERSION,
    DEFAULT_MENU_ID
)


class Menu:
    """Handles fetching and parsing of ERR menu structure."""

    def __init__(self, menuid=DEFAULT_MENU_ID):
        """Initialize menu with given menu ID.

        Args:
            menuid: Menu ID to fetch (default: 555 for main Jupiter menu)
        """
        self.url = f'{ERR_API_BASEURL}{ERR_API_VERSION}/menu/getMenuById?menuId={menuid}'
        self.content = download_url(self.url).json()

    def get_menu_items(self):
        """Get list of menu items from API response.

        Returns:
            List of menu item dictionaries
        """
        return self.content['data']['items']
