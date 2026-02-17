"""Search module for querying ERR content."""
import json
import xbmc

from .helpers import download_url
from .constants import (
    ERR_API_BASEURL,
    SEARCH_CATEGORY_ID,
    SEARCH_PAGE_LIMIT
)


class Search:
    """Handles search queries against ERR API."""

    def __init__(self, search_type='', search_phrase=''):
        """Initialize search with given parameters.

        Args:
            search_type: Type of search (currently unused by API)
            search_phrase: Search query string
        """
        self.options = json.dumps({
            "total": 0,
            "page": 1,
            "limit": SEARCH_PAGE_LIMIT,
            "offset": 0,
            "category": SEARCH_CATEGORY_ID,
            "phrase": search_phrase,
            "publicStart": "",
            "publicEnd": "",
            "timeFromSchedule": False,
            "types": ["media"],
            "viewTypes": ["episode", "movie"]
        }, separators=(',', ':'))
        self.url = f'{ERR_API_BASEURL}search/getVodContents/?type={search_type}&options={self.options}'

        xbmc.log(f'Jupiter Search URL: {self.url}', xbmc.LOGDEBUG)
        self.content = download_url(self.url).json()

    def get_response(self):
        """Get search result counts.

        Returns:
            Tuple of (video_count, audio_count) or None if error
        """
        try:
            return self.content['video']['totalFound'], self.content['audio']['totalFound']
        except (KeyError, TypeError):
            return None

    def get_results(self, content_type='video'):
        """Get search results for a specific content type.

        Args:
            content_type: Type of content to retrieve ('video' or 'audio')

        Returns:
            List of content dictionaries or None if error
        """
        try:
            return self.content[content_type]['contents']
        except (KeyError, TypeError):
            return None
