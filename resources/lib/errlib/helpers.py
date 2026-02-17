import re
import time
from datetime import datetime, timezone
import requests

from .constants import (
    USER_AGENT
)


def download_url(url, header=None, timeout=10):
    """Download content from URL with retry logic and timeout.

    Args:
        url: URL to download from
        header: Optional dictionary of additional headers
        timeout: Request timeout in seconds (default: 10)

    Returns:
        requests.Response object

    Raises:
        RuntimeError: If all retry attempts fail
    """
    last_exception = None

    for retry_count in range(5):
        try:
            headers = {}
            if header:
                headers = {k: v for k, v in header}
            headers['User-Agent'] = USER_AGENT

            # Make request with timeout and explicit HTTPS verification
            contents = requests.get(url, headers=headers, timeout=timeout, verify=True)
            contents.raise_for_status()
            return contents

        except (requests.exceptions.RequestException, IOError) as e:
            last_exception = e
            if retry_count < 4:  # Don't sleep on last attempt
                # Exponential backoff: 0.5s, 1s, 2s, 4s
                time.sleep(0.5 * (2 ** retry_count))

    # All retries exhausted
    raise RuntimeError(f'Could not open URL after 5 attempts: {url}. Last error: {last_exception}')


def strip_tags(string):
    """Remove HTML tags from string.

    Args:
        string: String potentially containing HTML tags

    Returns:
        String with HTML tags removed
    """
    if not string:
        return ''
    return re.sub('<[^<]+?>', '', string)


def convert_timestamp(input):
    """Convert Unix timestamp to readable UTC format.

    Args:
        input: Unix timestamp (int or string)

    Returns:
        Formatted date string (YYYY-MM-DD HH:MM:SS UTC)
    """
    return datetime.fromtimestamp(int(input), tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')


def get_subtitle_language(lang):
    """Map subtitle language setting to abbreviation.

    Args:
        lang: Language setting (0=Estonian, 1=Voice-over, 2=Russian)

    Returns:
        Two-letter language code (ET, VA, RU), defaults to ET
    """
    language_map = {
        0: "ET",
        1: "VA",
        2: "RU"
    }
    return language_map.get(int(lang), "ET")


def get_colour(color):
    """Map color setting to color name.

    Args:
        color: Color setting (0-14)

    Returns:
        Color name string, defaults to 'blue'
    """
    colours = {
        0: 'white',
        1: 'ivory',
        2: 'silver',
        3: 'gray',
        4: 'limegreen',
        5: 'green',
        6: 'lightblue',
        7: 'blue',
        8: 'deeppink',
        9: 'turquoise',
        10: 'gold',
        11: 'yellow',
        12: 'brown',
        13: 'orange',
        14: 'red'
    }
    return colours.get(int(color), 'blue')
