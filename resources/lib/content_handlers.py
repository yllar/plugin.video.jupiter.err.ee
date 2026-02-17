"""Content handlers for different content types (series, movies, episodes)."""
from resources.lib.errlib import helpers
from resources.lib.kodi_helpers import (
    build_url,
    create_list_item,
    create_colored_item,
    create_playable_item,
    setup_drm_properties,
)


def handle_series_content(data, settings, path, sub=''):
    """Handle series content with seasons and episodes.

    Args:
        data: Content instance with series data
        settings: SettingsCache instance
        path: Plugin path for URL building
        sub: Subsection flag ('marine' for recursive calls)

    Returns:
        List of (url, ListItem, is_folder) tuples
    """
    items = []
    season_type = data.get_seasonlist_type()

    for season in data.get_season():
        # Add season header if it has an ID
        if data.get_item_id(season) is not None:
            season_title = f"Hooaeg: {str(data.get_item_id(season))}"
            url, item, is_folder = create_colored_item(
                season_title,
                settings.colour_season,
                build_url(path, 'section', section=str(data.get_primaryid(season)), sub='marine'),
                True
            )
            items.append((url, item, is_folder))

        # Handle monthly seasons
        if season_type == 'monthly':
            items.extend(handle_monthly_seasons(season, data, settings, path))
        # Handle seasonal/shortSeriesList seasons
        elif season_type in ('seasonal', 'shortSeriesList') and data.get_item_contents(season) is not None:
            items.extend(handle_seasonal_content(season, data, settings, path))

    return items


def handle_monthly_seasons(season, data, settings, path):
    """Handle monthly season structure.

    Args:
        season: Season data dictionary
        data: Content instance
        settings: SettingsCache instance
        path: Plugin path for URL building

    Returns:
        List of (url, ListItem, is_folder) tuples
    """
    items = []

    for month in data.get_items(season):
        # Add month header
        month_name = data.get_item_name(month)
        url, item, is_folder = create_colored_item(
            f" {month_name}",
            settings.colour_category,
            build_url(path, 'section', section=str(data.get_item_primaryid(month)), sub='marine'),
            True
        )
        items.append((url, item, is_folder))

        # Add episodes within the month
        if data.get_item_contents(month) is not None:
            for day in data.get_item_contents(month):
                episode_num = data.get_item_episode(day)
                heading = data.get_item_heading(day)

                # Build title with episode number if available
                if episode_num is not None and episode_num > 0:
                    title = f"{heading} {str(episode_num)}"
                elif heading:
                    title = heading
                else:
                    title = "Episode"

                # Use on-air date as plot
                plot = helpers.convert_timestamp(data.get_item_schedule_start(day))
                info_labels = {'title': title, 'plot': plot}

                # Create list item
                fanart = data.get_item_photo(day) if settings.enable_images else None
                ep_url = build_url(path, 'section', section=str(data.get_item_id(day)), sub='false')
                url, item, is_folder = create_list_item(f"  {title}", ep_url, True, fanart, info_labels)
                items.append((url, item, is_folder))

    return items


def handle_seasonal_content(season, data, settings, path):
    """Handle seasonal/shortSeriesList content structure.

    Args:
        season: Season data dictionary
        data: Content instance
        settings: SettingsCache instance
        path: Plugin path for URL building

    Returns:
        List of (url, ListItem, is_folder) tuples
    """
    items = []

    for episode in data.get_item_contents(season):
        subheading = data.get_item_subheading(episode)
        heading = data.get_item_heading(episode)
        fanart = data.get_item_photo(episode)

        # Determine title with null checks and whitespace handling
        if subheading and len(subheading.strip()) > 2:
            title = subheading
        elif heading and len(heading.strip()) > 0:
            title = heading
        else:
            episode_num = data.get_item_episode(episode)
            title = str(episode_num) if episode_num else "Episode"

        # Create list item
        fanart_img = fanart if settings.enable_images else None
        ep_url = build_url(path, 'section', section=str(episode['id']), sub='false')
        url, item, is_folder = create_list_item(title, ep_url, True, fanart_img)
        items.append((url, item, is_folder))

    return items


def handle_playable_content(data, settings, drm_config):
    """Handle playable content (movies and episodes).

    Args:
        data: Content instance with playable content
        settings: SettingsCache instance
        drm_config: Dictionary with DRM configuration

    Returns:
        List containing single (url, ListItem) tuple
    """
    title = data.get_heading()
    video = data.get_hls()
    plot = helpers.strip_tags(data.get_body())
    drm = data.get_drm()

    # Get DRM content if protected
    license_server = None
    token = None
    if drm:
        token = data.get_token()
        license_server = data.get_license_server()
        video = data.get_dash()

    # Gather subtitles
    subtitles = []
    for language in settings.get_subtitle_languages():
        subtitle_url = data.get_subtitles(language)
        if subtitle_url is not None:
            subtitles.append(subtitle_url)

    # Create playable item
    info_labels = {'title': title, 'plot': plot}
    fanart = data.get_photo() if settings.enable_images else None

    video_url, item = create_playable_item(
        title, video, fanart=fanart, info_labels=info_labels,
        subtitles=subtitles if subtitles else None,
        drm_config=drm_config if drm else None,
        license_server=license_server,
        token=token
    )

    return [(video_url, item)]
