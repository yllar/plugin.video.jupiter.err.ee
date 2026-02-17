"""UI helper functions for consistent ListItem creation and URL building."""
from urllib.parse import quote

import xbmcgui
import xbmcplugin


def build_url(base_path, action, **params):
    """Build a properly encoded plugin URL.

    Args:
        base_path: Base plugin path (e.g., 'plugin://plugin.video.jupiter.err.ee/')
        action: Action name (category, section, listing, search)
        **params: Additional URL parameters

    Returns:
        Properly encoded URL string
    """
    params['action'] = action
    # URL encode all parameters
    encoded_params = {k: quote(str(v), safe='') for k, v in params.items()}
    query_string = '&'.join(f'{k}={v}' for k, v in encoded_params.items())
    return f'{base_path}?{query_string}'


def create_list_item(title, url=None, is_folder=True, fanart=None, info_labels=None):
    """Create a Kodi ListItem with consistent configuration.

    Args:
        title: Item title
        url: Item URL (optional for non-clickable items)
        is_folder: Whether item is a folder (default: True)
        fanart: Fanart/poster/icon URL (optional)
        info_labels: Dictionary of video info labels (optional)

    Returns:
        Tuple of (url, ListItem, is_folder)
 """
    if url is not None:
        item = xbmcgui.ListItem(title, path=url)
    else:
        item = xbmcgui.ListItem(title)

    if fanart:
        item.setArt({'fanart': fanart, 'poster': fanart, 'icon': fanart})

    if info_labels:
        item.setInfo(type="Video", infoLabels=info_labels)

    if url is None:
        url = ''

    return (url, item, is_folder)


def create_colored_item(title, color, url='', is_folder=False, fanart=None):
    """Create a colored ListItem (typically for headers/categories).

    Args:
        title: Item title
        color: Color name (e.g., 'blue', 'red')        url: Item URL (default: empty string for non-clickable)
        is_folder: Whether item is a folder (default: False for headers)
        fanart: Fanart URL (optional)

    Returns:
        Tuple of (url, ListItem, is_folder)
    """
    colored_title = f'[COLOR {color}]{title}[/COLOR]'
    return create_list_item(colored_title, url, is_folder, fanart)


def set_item_art(item, fanart, enable_images):
    """Set artwork on a ListItem if images are enabled.

    Args:
        item: xbmcgui.ListItem instance
        fanart: Fanart URL
        enable_images: Boolean indicating if images should be loaded
    """
    if enable_images and fanart:
        item.setArt({'fanart': fanart, 'poster': fanart, 'icon': fanart})


def add_items_and_close(handle, items):
    """Add items to directory and close it.

    Args:
        handle: Kodi plugin handle
        items: List of tuples (url, ListItem, is_folder)
    """
    xbmcplugin.addDirectoryItems(handle, items)
    xbmcplugin.endOfDirectory(handle)


def create_playable_item(title, video_url, fanart=None, info_labels=None, subtitles=None,
                        drm_config=None, license_server=None, token=None):
    """Create a playable video ListItem.

    Args:
        title: Video title
        video_url: Video stream URL
        fanart: Fanart URL (optional)
        info_labels: Dictionary of video info labels (optional)
        subtitles: List of subtitle URLs (optional)
        drm_config: Dictionary with DRM configuration (optional)
        license_server: License server URL (required if drm_config is set)
        token: DRM token (required if drm_config is set)

    Returns:
        Tuple of (video_url, ListItem)
    """
    item = xbmcgui.ListItem(title, path=video_url)

    if fanart:
        item.setArt({'fanart': fanart, 'poster': fanart, 'icon': fanart})

    if info_labels:
        item.setInfo(type="Video", infoLabels=info_labels)

    item.setProperty('IsPlayable', 'True')
    item.setProperty('isFolder', 'False')

    if drm_config and license_server and token:
        setup_drm_properties(item, license_server, token, drm_config)

    if subtitles:
        item.setSubtitles(subtitles)

    return (video_url, item)


def setup_drm_properties(item, license_server, token, drm_config):
    """Setup DRM properties on a ListItem.

    Args:
        item: xbmcgui.ListItem instance
        license_server: License server URL
        token: DRM token
        drm_config: Dictionary with keys:
            - is_helper: inputstreamhelper.Helper instance
            - kodi_version: Kodi major version
            - protocol: Stream protocol (e.g., 'mpd')
            - drm: DRM type (e.g., 'com.widevine.alpha')
            - mime_type: MIME type (e.g., 'application/dash+xml')
    """
    is_helper = drm_config['is_helper']
    kodi_version = drm_config['kodi_version']
    protocol = drm_config['protocol']
    drm = drm_config['drm']
    mime_type = drm_config['mime_type']

    if is_helper.check_inputstream():
        item.setContentLookup(False)
        item.setMimeType(mime_type)

        if kodi_version >= 19:
            item.setProperty('inputstream', is_helper.inputstream_addon)
        else:
            item.setProperty('inputstreamaddon', is_helper.inputstream_addon)

        item.setProperty('inputstream.adaptive.manifest_type', protocol)
        item.setProperty('inputstream.adaptive.license_type', drm)
        item.setProperty('inputstream.adaptive.license_key',
                        f'{license_server}|X-AxDRM-Message={token}|R{{SSM}}|')
