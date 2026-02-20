# coding: utf-8
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
import os
import sys
import inputstreamhelper

try:
    from urllib.parse import parse_qsl
except ImportError:
    from urlparse import parse_qsl

import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin

from resources.lib.errlib.menu import Menu
import resources.lib.errlib.helpers as helpers
from resources.lib.errlib.category import Category
from resources.lib.errlib.content import Content
from resources.lib.errlib.search import Search
from resources.lib.errlib.search_history import SearchHistory

from resources.lib.errlib.constants import (
    ERR_API_BASEURL,
    ERR_API_VERSION
)

# import web_pdb

# Get the plugin url in plugin:// notation.
PATH = sys.argv[0]
# Get the plugin _handle as an integer number.
_handle = int(sys.argv[1])

FANART = 'https://s.err.ee/photo/crop/2020/03/30/765343had90t16.png'

__settings__ = xbmcaddon.Addon(id='plugin.video.jupiter.err.ee')
ADDON = xbmcaddon.Addon()
KODI_VERSION_MAJOR = int(xbmc.getInfoLabel('System.BuildVersion').split('.')[0])
PROTOCOL = 'mpd'
DRM = 'com.widevine.alpha'
MIME_TYPE = 'application/dash+xml'
is_helper = inputstreamhelper.Helper(PROTOCOL, drm=DRM)


def list_category():
    items = list()
    menu = Menu()
    menuitems = menu.get_menu_items()
    search_icon = os.path.join(ADDON.getAddonInfo('path'), 'resources', 'search.png')

    item = xbmcgui.ListItem(ADDON.getLocalizedString(30012))
    item.setArt({'fanart': search_icon, 'poster': search_icon, 'icon': search_icon})
    items.append((PATH + '?action=search_menu', item, True))

    for menuitem in menuitems:
        if menuitem['kids_count'] > 0:
            item = xbmcgui.ListItem(
                '[COLOR {}]{}[/COLOR]'.format(helpers.get_colour(__settings__.getSetting('colourCategory')),
                                              menuitem['name']))
            item.setArt({'fanart': FANART, 'poster': FANART, 'icon': FANART})
            items.append((PATH + '?action=category&category={}'.format(menuitem['link'].replace('/', '')), item, False))
            for sub_item in menuitem['kids']:
                if sub_item['kids_count'] < 2:  # Audio submenu has Järjejutud as kid
                    item = xbmcgui.ListItem(' {}'.format(sub_item['name']))
                    item.setArt({'fanart': FANART})
                    items.append(
                        (PATH + '?action=category&category={}'.format(sub_item['link'].replace('/', '')), item, True))
            # Inject extra items
            item = xbmcgui.ListItem(' Saated A-Ü')
            item.setArt({'fanart': FANART})
            items.append((PATH + '?action=listing&category={}'.format(menuitem['name'].lower()), item, True))
    # make menu
    xbmcplugin.addDirectoryItems(_handle, items)
    xbmcplugin.endOfDirectory(_handle)


def search_menu():
    """Display search menu with history entries and new search option"""
    items = list()
    search_history = SearchHistory()
    history = search_history.get_history()
    
    # Add "New Search" option at the top
    search_icon = os.path.join(ADDON.getAddonInfo('path'), 'resources', 'search.png')
    item = xbmcgui.ListItem(ADDON.getLocalizedString(30019))  # "New Search"
    item.setArt({'fanart': search_icon, 'poster': search_icon, 'icon': search_icon})
    items.append((PATH + '?action=search', item, True))
    
    # Add history entries
    for entry in history:
        query = entry['query']
        item = xbmcgui.ListItem(query)
        item.setArt({'fanart': FANART})
        
        # Add context menu for deleting individual entry
        try:
            from urllib.parse import quote_plus
        except ImportError:
            from urllib import quote_plus
        
        context_menu = [
            (ADDON.getLocalizedString(30015),  # "Delete from history"
             'RunPlugin({0}?action=delete_history&query={1})'.format(PATH, quote_plus(query.encode('utf-8'))))
        ]
        item.addContextMenuItems(context_menu)
        
        items.append((PATH + '?action=search&query={}'.format(quote_plus(query.encode('utf-8'))), item, True))
    
    # Add "Clear History" option at the bottom (only if history exists)
    if history:
        clear_text = ADDON.getLocalizedString(30020) or "Clear History"
        item = xbmcgui.ListItem('[COLOR red]{}[/COLOR]'.format(clear_text))
        item.setArt({'fanart': FANART})
        items.append((PATH + '?action=clear_history', item, True))
    
    xbmcplugin.addDirectoryItems(_handle, items)
    xbmcplugin.endOfDirectory(_handle)


def get_search_string():
    kb = xbmc.Keyboard('', ADDON.getLocalizedString(30013))
    kb.doModal()
    if not kb.isConfirmed():
        return
    query = kb.getText()
    return query


def do_search(query=None):
    # Get query from user input if not provided
    if query is None:
        query = get_search_string()
    
    # If user cancelled the search dialog, return early
    if not query:
        return
    
    # Add query to search history
    search_history = SearchHistory()
    search_history.add_entry(query)
    
    # Execute search with the query
    search = Search(search_phrase=query)
    items = list()
    available_types = ["video", "audio"]
    for index, content_type in enumerate(available_types):
        item = xbmcgui.ListItem(
            '[COLOR {}]{} {}: {}[/COLOR]'.format(helpers.get_colour(__settings__.getSetting('colourCategory')),
                                                 content_type.capitalize(),
                                                 ADDON.getLocalizedString(30014),
                                                 search.get_response()[index]))
        item.setArt({'fanart': FANART})
        items.append((PATH + '', item, False))
        for result in search.get_results(content_type=content_type):
            item = xbmcgui.ListItem(result['heading'])
            item.setArt({'fanart': FANART})
            items.append((PATH + '?action=section&section={}&sub=false'.format(result['id']), item, True))

    xbmcplugin.addDirectoryItems(_handle, items)
    xbmcplugin.endOfDirectory(_handle)


def clear_search_history():
    """Clear all search history with user confirmation"""
    dialog = xbmcgui.Dialog()
    
    # Get localized strings
    title = ADDON.getLocalizedString(30016)  # "Clear Search History"
    message = ADDON.getLocalizedString(30017)  # "Are you sure you want to clear all search history?"
    
    # Show confirmation dialog
    confirmed = dialog.yesno(title, message)
    
    if confirmed:
        # Clear the history
        search_history = SearchHistory()
        search_history.clear()
        
        # Get notification strings
        notif_title = ADDON.getLocalizedString(30016) or "Clear Search History"
        notif_message = ADDON.getLocalizedString(30018) or "Search history cleared"
        
        # Show success notification
        dialog.notification(
            notif_title,
            notif_message,
            xbmcgui.NOTIFICATION_INFO,
            3000
        )
    
    # Refresh the container to update the menu
    xbmc.executebuiltin('Container.Refresh')


def delete_history_entry(query):
    """Delete a specific search history entry"""
    search_history = SearchHistory()
    search_history.remove_entry(query)
    
    # Refresh the container to update the menu
    xbmc.executebuiltin('Container.Refresh')


def get_category(categorykey):
    # web_pdb.set_trace()
    categories = Category(categorykey)
    items = list()
    for category in categories.get_categories():
        item = xbmcgui.ListItem(
            "[COLOR {}]{}[/COLOR]".format(helpers.get_colour(__settings__.getSetting('colourCategory')), category))
        items.append((PATH, item))
        for category_item in categories.get_gategory_items(category):
            (item_id, heading, image_url, plot) = (
                category_item[0], category_item[1], category_item[2], category_item[3])
            info_labels = {'title': heading, 'plot': plot}
            item = xbmcgui.ListItem(heading)
            if 'true' in __settings__.getSetting('enableImages'):
                item.setArt({'fanart': image_url, 'poster': image_url, 'icon': image_url})
            item.setInfo(type="Video", infoLabels=info_labels)
            items.append((PATH + '?action=section&section={}&sub=false'.format(item_id), item, True))
    xbmcplugin.addDirectoryItems(_handle, items)
    xbmcplugin.endOfDirectory(_handle)


def get_section(section, sub=''):
    # web_pdb.set_trace()
    data = Content(section)
    items = list()
    # xbmc.log('DATA: %s' % data, xbmc.LOGINFO)

    content_type = data.get_page_type()
    season_type = data.get_seasonlist_type()
    if content_type in 'series' or sub == 'marine':
        for season in data.get_season():
            if data.get_item_id(season) is not None:
                # Season
                item = xbmcgui.ListItem("[COLOR {}]Hooaeg: {}[/COLOR]".format(
                    helpers.get_colour(__settings__.getSetting('colourSeason')),
                    str(data.get_item_id(season)))
                )

                items.append(
                    (PATH + '?action=section&section={}&sub=marine'.format(data.get_primaryid(season)),
                     item, True)
                )

            if season_type == 'monthly':
                for month in data.get_items(season):
                    item = xbmcgui.ListItem(
                        " [COLOR {}]{}[/COLOR]".format(
                            helpers.get_colour(__settings__.getSetting('colourCategory')),
                            data.get_item_name(month))
                    )
                    # item.setArt({'fanart': fanart, 'poster': fanart, 'icon': fanart})
                    items.append(
                        (PATH + '?action=section&section={}&sub=marine'.format(
                            data.get_item_primaryid(month)), item, True)
                    )

                    if data.get_item_contents(month) is not None:
                        for day in data.get_item_contents(month):
                            title = ''
                            if data.get_item_episode(day) > 0:
                                title = data.get_item_heading(day) + " " + str(data.get_item_episode(day))
                            else:
                                title = data.get_item_heading(day)
                            # no plot, use on-air date // TODO find something else instead
                            plot = helpers.convert_timestamp(data.get_item_schedule_start(day))

                            info_labels = {'title': title, 'plot': plot}
                            fanart = data.get_item_photo(day)

                            item = xbmcgui.ListItem("  {}".format(title))
                            if 'true' in __settings__.getSetting('enableImages'):
                                item.setArt({'fanart': fanart, 'poster': fanart, 'icon': fanart})
                            item.setInfo(type="Video", infoLabels=info_labels)
                            items.append((PATH + '?action=section&section={}&sub=false'.format(
                                data.get_item_id(day)), item, True))

            elif season_type in ('seasonal', 'shortSeriesList') and data.get_item_contents(
                    season) is not None:
                # xbmc.log(' Season: %s' % str(season_type), xbmc.LOGINFO)

                for episood in data.get_item_contents(season):
                    subheading = data.get_item_subheading(episood)
                    heading = data.get_item_heading(episood)
                    fanart = data.get_item_photo(episood)

                    if subheading is not None and len(subheading) > 2:
                        title = subheading
                    elif heading is not None:
                        title = heading
                    else:
                        title = str(data.get_item_episode(episood))

                    item = xbmcgui.ListItem(title)
                    if 'true' in __settings__.getSetting('enableImages'):
                        item.setArt({'fanart': fanart, 'poster': fanart, 'icon': fanart})
                    items.append((PATH + '?action=section&section={}&sub=false'.format(episood['id']), item, True))

    elif content_type in ('movie', 'episode'):
        sub = []
        languages = []
        languages.extend((
            helpers.get_subtitle_language(__settings__.getSetting('primaryLanguage')),
            helpers.get_subtitle_language(__settings__.getSetting('secondaryLanguage'))
        ))

        title = data.get_heading()
        video = data.get_hls()
        plot = helpers.strip_tags(data.get_body())
        drm = data.get_drm()

        # we can play DRM content
        if drm:
            token = data.get_token()
            license_server = data.get_license_server()
            video = data.get_dash()

        info_labels = {'title': title, 'plot': plot}

        for language in languages:
            if data.get_subtitles(language) is not None:
                sub.append(data.get_subtitles(language))

        # web_pdb.set_trace()
        fanart = data.get_photo()
        item = xbmcgui.ListItem(title, path=video)
        if 'true' in __settings__.getSetting('enableImages'):
            item.setArt({'fanart': fanart, 'poster': fanart, 'icon': fanart})
        item.setInfo(type="Video", infoLabels=info_labels)
        helper = inputstreamhelper.Helper('hls')
        if 'true' in __settings__.getSetting('isa') and helper.check_inputstream():
            if KODI_VERSION_MAJOR >= 19:
            	item.setProperty('inputstream','inputstream.adaptive')
            else:
            	item.setProperty('inputstreamaddon','inputstream.adaptive')
            item.setProperty('inputstream.adaptive.manifest_type', 'hls')
            item.setProperty('IsPlayable', 'True')
            item.setProperty('isFolder', 'False')
        if drm:
            if is_helper.check_inputstream():
                item.setContentLookup(False)
                item.setMimeType(MIME_TYPE)
                if KODI_VERSION_MAJOR >= 19:
                    item.setProperty('inputstream', is_helper.inputstream_addon)
                else:
                    item.setProperty('inputstreamaddon', is_helper.inputstream_addon)
                item.setProperty('inputstream.adaptive.manifest_type', PROTOCOL)
                item.setProperty('inputstream.adaptive.license_type', DRM)
                item.setProperty('inputstream.adaptive.license_key',
                                 license_server + '|X-AxDRM-Message=' + token + '|R{SSM}|')
        item.setSubtitles(sub)
        items.append((video, item))
    xbmcplugin.addDirectoryItems(_handle, items)
    xbmcplugin.endOfDirectory(_handle)


def get_all_shows(type):
    url = '{}{}/series/getSeriesData?type={}'.format(ERR_API_BASEURL, ERR_API_VERSION, type)
    # xbmc.log('url: %s' % url, xbmc.LOGNOTICE)
    items = list()
    data = helpers.download_url(url).json()
    for show in data['data']['items']:
        item = xbmcgui.ListItem("{}".format(show['heading']))
        if 'photoUrlOriginal' in show['photos'][0]:
            fanart = show['photos'][0]['photoUrlOriginal']
            if 'true' in __settings__.getSetting('enableImages'):
                item.setArt({'fanart': fanart, 'poster': fanart, 'icon': fanart})
        items.append((PATH + '?action=section&section={}&sub=false'.format(show['id']), item, True))
    xbmcplugin.addDirectoryItems(_handle, items)
    xbmcplugin.endOfDirectory(_handle)


def router(paramstring):
    params = dict(parse_qsl(paramstring))
    if params:
        if params['action'] == 'category':
            get_category(params['category'])
        elif params['action'] == 'section':
            get_section(params['section'], params['sub'])
        elif params['action'] == 'listing':
            get_all_shows(params['category'])
        elif params['action'] == 'search':
            # Handle optional query parameter
            query = params.get('query', None)
            if query:
                try:
                    from urllib.parse import unquote_plus
                except ImportError:
                    from urllib import unquote_plus
                query = unquote_plus(query)
            do_search(query)
        elif params['action'] == 'search_menu':
            search_menu()
        elif params['action'] == 'clear_history':
            clear_search_history()
        elif params['action'] == 'delete_history':
            # Decode the query parameter
            query = params.get('query', '')
            if query:
                try:
                    from urllib.parse import unquote_plus
                except ImportError:
                    from urllib import unquote_plus
                query = unquote_plus(query)
            delete_history_entry(query)
        else:
            raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
    else:
        list_category()


if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    router(sys.argv[2][1:])
