"""Jupiter ERR.ee Kodi Plugin - Main addon module."""
import os
import sys
from urllib.parse import parse_qsl, quote
import inputstreamhelper

import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin

from resources.lib.errlib.menu import Menu
import resources.lib.errlib.helpers as helpers
from resources.lib.errlib.category import Category
from resources.lib.errlib.content import Content
from resources.lib.errlib.search import Search
from resources.lib.settings import SettingsCache
from resources.lib import kodi_helpers
from resources.lib import content_handlers

from resources.lib.errlib.constants import (
    ERR_API_BASEURL,
    ERR_API_VERSION,
    AUDIO_SUBMENU_KIDS_COUNT
)

# Get the plugin url in plugin:// notation.
PATH = sys.argv[0]
# Get the plugin _handle as an integer number.
_handle = int(sys.argv[1])

FANART = 'https://s.err.ee/photo/crop/2020/03/30/765343had90t16.png'

ADDON = xbmcaddon.Addon(id='plugin.video.jupiter.err.ee')
KODI_VERSION_MAJOR = int(xbmc.getInfoLabel('System.BuildVersion').split('.')[0])
PROTOCOL = 'mpd'
DRM = 'com.widevine.alpha'
MIME_TYPE = 'application/dash+xml'
is_helper = inputstreamhelper.Helper(PROTOCOL, drm=DRM)

# DRM configuration dictionary for content handlers
DRM_CONFIG = {
    'is_helper': is_helper,
    'kodi_version': KODI_VERSION_MAJOR,
    'protocol': PROTOCOL,
    'drm': DRM,
    'mime_type': MIME_TYPE
}


def list_category():
    """Display the main category menu."""
    settings = SettingsCache(ADDON)
    menu = Menu()
    menuitems = menu.get_menu_items()
    search_icon = os.path.join(ADDON.getAddonInfo('path'), 'resources', 'search.png')
    items = []

    # Add search item
    url, item, is_folder = kodi_helpers.create_list_item(
        ADDON.getLocalizedString(30012),
        kodi_helpers.build_url(PATH, 'search'),
        True,
        search_icon
    )
    items.append((url, item, is_folder))

    for menuitem in menuitems:
        if menuitem['kids_count'] > 0:
            # Add main category header
            url, item, is_folder = kodi_helpers.create_colored_item(
                menuitem['name'],
                settings.colour_category,
                kodi_helpers.build_url(PATH, 'category', category=menuitem['link'].replace('/', '')),
                False,
                FANART
            )
            items.append((url, item, is_folder))

            # Add sub-items
            for sub_item in menuitem['kids']:
                if sub_item['kids_count'] < AUDIO_SUBMENU_KIDS_COUNT:
                    url, item, is_folder = kodi_helpers.create_list_item(
                        f' {sub_item["name"]}',
                        kodi_helpers.build_url(PATH, 'category', category=sub_item['link'].replace('/', '')),
                        True,
                        FANART
                    )
                    items.append((url, item, is_folder))

            # Add "All Shows A-Z" item
            url, item, is_folder = kodi_helpers.create_list_item(
                ' Saated A-Ü',
                kodi_helpers.build_url(PATH, 'listing', category=menuitem['name'].lower()),
                True,
                FANART
            )
            items.append((url, item, is_folder))

    kodi_helpers.add_items_and_close(_handle, items)


def get_search_string():
    """Get search query from user via keyboard.

    Returns:
        Search string or None if cancelled
    """
    kb = xbmc.Keyboard('', ADDON.getLocalizedString(30013))
    kb.doModal()
    if not kb.isConfirmed():
        return None
    query = kb.getText()
    return query


def do_search():
    """Perform content search and display results."""
    search_phrase = get_search_string()
    if search_phrase is None:
        # User cancelled search
        xbmcplugin.endOfDirectory(_handle)
        return

    settings = SettingsCache(ADDON)
    search = Search(search_phrase=search_phrase)
    items = []

    available_types = ["video", "audio"]
    for index, content_type in enumerate(available_types):
        # Add result count header
        url, item, is_folder = kodi_helpers.create_colored_item(
            f'{content_type.capitalize()} {ADDON.getLocalizedString(30014)}: {search.get_response()[index]}',
            settings.colour_category,
            '',
            False,
            FANART
        )
        items.append((url, item, is_folder))

        # Add search results
        for result in search.get_results(content_type=content_type):
            url, item, is_folder = kodi_helpers.create_list_item(
                result['heading'],
                kodi_helpers.build_url(PATH, 'section', section=str(result['id']), sub='false'),
                True,
                FANART
            )
            items.append((url, item, is_folder))

    kodi_helpers.add_items_and_close(_handle, items)


def get_category(categorykey):
    """Display items in a specific category.

    Args:
        categorykey: Category identifier from URL
    """
    settings = SettingsCache(ADDON)
    categories = Category(categorykey)
    items = []

    for category in categories.get_categories():
        # Add category header
        url, item, is_folder = kodi_helpers.create_colored_item(
            category,
            settings.colour_category,
            '',
            False
        )
        items.append((url, item, is_folder))

        # Add category items
        for category_item in categories.get_category_items(category):
            item_id, heading, image_url, plot = category_item[0], category_item[1], category_item[2], category_item[3]
            info_labels = {'title': heading, 'plot': plot}

            url_path = kodi_helpers.build_url(PATH, 'section', section=str(item_id), sub='false')
            url, item, is_folder = kodi_helpers.create_list_item(
                heading,
                url_path,
                True,
                image_url if settings.enable_images else None,
                info_labels
            )
            items.append((url, item, is_folder))

    kodi_helpers.add_items_and_close(_handle, items)


def get_section(section, sub=''):
    """Display content details or series structure.

    Args:
        section: Content/section identifier
        sub: Subsection flag ('marine' for recursive calls, 'false' otherwise)
    """
    settings = SettingsCache(ADDON)
    data = Content(section)
    content_type = data.get_page_type()

    # Handle series content
    if content_type == 'series' or sub == 'marine':
        items = content_handlers.handle_series_content(data, settings, PATH, sub)
        kodi_helpers.add_items_and_close(_handle, items)

    # Handle playable content (movies and episodes)
    elif content_type in ('movie', 'episode'):
        items = content_handlers.handle_playable_content(data, settings, DRM_CONFIG)
        kodi_helpers.add_items_and_close(_handle, items)

    # Unknown content type
    else:
        xbmc.log(f'Jupiter: Unknown content type: {content_type}', xbmc.LOGWARNING)
        xbmcplugin.endOfDirectory(_handle)


def get_all_shows(type):
    """Display all shows of a given type, sorted alphabetically.

    Args:
        type: Show type identifier
    """
    settings = SettingsCache(ADDON)
    url = f'{ERR_API_BASEURL}{ERR_API_VERSION}/series/getSeriesData?type={type}'
    data = helpers.download_url(url).json()
    items = []

    for show in data['data']['items']:
        fanart = None
        photos = show.get('photos', [])
        if photos and 'photoUrlOriginal' in photos[0]:
            fanart = photos[0]['photoUrlOriginal']

        url_path = kodi_helpers.build_url(PATH, 'section', section=str(show['id']), sub='false')
        url, item, is_folder = kodi_helpers.create_list_item(
            show['heading'],
            url_path,
            True,
            fanart if settings.enable_images else None
        )
        items.append((url, item, is_folder))

    kodi_helpers.add_items_and_close(_handle, items)


def router(paramstring):
    """Route requests to appropriate handler functions.

    Args:
        paramstring: URL parameter string
    """
    params = dict(parse_qsl(paramstring))
    if params:
        action = params.get('action', '')

        # Whitelist allowed actions for security
        allowed_actions = ['category', 'section', 'listing', 'search']
        if action not in allowed_actions:
            xbmc.log(f'Jupiter: Invalid action: {action}', xbmc.LOGERROR)
            raise ValueError(f'Invalid action: {action}')

        if action == 'category':
            get_category(params['category'])
        elif action == 'section':
            get_section(params['section'], params['sub'])
        elif action == 'listing':
            get_all_shows(params['category'])
        elif action == 'search':
            do_search()
    else:
        list_category()


if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    router(sys.argv[2][1:])
