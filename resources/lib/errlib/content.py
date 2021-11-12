# coding: utf-8
import json

from .helpers import download_url
from .constants import (
    ERR_API_BASEURL,
    ERR_API_VERSION
)


class Content:
    def __init__(self, contentid):
        self.url = '{}{}/vodContent/getContentPageData?contentId={}'.format(ERR_API_BASEURL,
                                                                            ERR_API_VERSION, contentid)
        self.content = download_url(self.url).json()

    def get_page_type(self):
        try:
            return self.content['data']['pageType']
        except (KeyError, TypeError, IndexError):
            return None

    def get_id(self, type='main'):
        try:
            return self.content['data'][type + 'Content']['id']
        except (KeyError, TypeError, IndexError):
            return None

    def get_heading(self, type='main'):
        try:
            return self.content['data'][type + 'Content']['heading']
        except (KeyError, TypeError, IndexError):
            return None

    def get_subheading(self, type='main'):
        try:
            return self.content['data'][type + 'Content']['subHeading']
        except (KeyError, TypeError, IndexError):
            return None

    def get_lead(self, type='main'):
        try:
            return self.content['data'][type + 'Content']['lead']
        except (KeyError, TypeError, IndexError):
            return None

    def get_body(self, type='main'):
        try:
            return self.content['data'][type + 'Content']['body']
        except (KeyError, TypeError, IndexError):
            return None

    def has_next(self):
        try:
            if self.content['data']['nextContent']:
                return True
        except (KeyError, TypeError, IndexError):
            return None

    def get_primary_category_id(self, type='main'):
        try:
            return self.content['data'][type + 'Content']['primaryCategoryId']
        except (KeyError, TypeError, IndexError):
            return None

    def get_seasonlist_type(self):
        try:
            return self.content['data']['seasonList']['type']
        except (KeyError, TypeError, IndexError):
            return None

    def get_media_type(self):
        try:
            return self.content['data']['mainContent']['medias'][0]['type']
        except (KeyError, TypeError, IndexError):
            return None

    def get_hls(self):
        try:
            return 'https:' + self.content['data']['mainContent']['medias'][0]['src']['hls']
        except (KeyError, TypeError, IndexError):
            return None

    def get_dash(self):
        try:
            return 'https:' + self.content['data']['mainContent']['medias'][0]['src']['dash']
        except (KeyError, TypeError, IndexError):
            return None

    def get_file(self):
        try:
            return 'https:' + self.content['data']['mainContent']['medias'][0]['src']['file']
        except (KeyError, TypeError, IndexError):
            return None

    def get_subtitles(self, lang='ET'):
        try:
            for subtitle in self.content['data']['mainContent']['medias'][0]['subtitles']:
                if lang == subtitle['srclang']:
                    return subtitle['src']
        except (KeyError, TypeError, IndexError):
            return None

    def get_drm(self):
        try:
            return self.content['data']['mainContent']['medias'][0]['restrictions']['drm']
        except (KeyError, TypeError, IndexError):
            return False

    def get_token(self):
        try:
            return self.content['data']['mainContent']['medias'][0]['jwt']
        except (KeyError, TypeError, IndexError):
            return False

    def get_license_server(self, type='widevine'):
        try:
            return self.content['data']['mainContent']['medias'][0]['licenseServerUrl'][type]
        except (KeyError, TypeError, IndexError):
            return False

    def get_photo(self, type='main', size='original'):
        try:
            return self.content['data'][type + 'Content']['photos'][0]['photoUrlOriginal']
        except (KeyError, TypeError, IndexError):
            return None

    def get_photo_vertical(self, type='main', size='original'):
        try:
            if size == 'original':
                return self.content['data'][type + 'Content']['verticalPhotos'][0]['photoUrlOriginal']
            else:
                return self.content['data'][type + 'Content']['verticalPhotos'][0]['photoTypes'][size]['url']
        except (KeyError, TypeError, IndexError):
            return None

    def get_photo_horizontal(self, type='main', size='original'):
        try:
            if size == 'original':
                return self.content['data'][type + 'Content']['horizontalPhotos'][0]['photoUrlOriginal']
            else:
                return self.content['data'][type + 'Content']['horizontalPhotos'][0]['photoTypes'][size]['url']
        except (KeyError, TypeError, IndexError):
            return None

    def get_season(self):
        try:
            return self.content['data']['seasonList']['items']
        except (KeyError, TypeError, IndexError):
            return None

    def get_item_id(self, item_index):
        try:
            return item_index['id']
        except (KeyError, TypeError, IndexError):
            return None

    def get_primaryid(self, item_index):
        try:
            return item_index['firstContentId']
        except (KeyError, TypeError, IndexError):
            return None

    def get_items(self, item_index):
        try:
            return item_index['items']
        except (KeyError, TypeError, IndexError):
            return None

    def get_item_name(self, item_index):
        try:
            return item_index['name']
        except (KeyError, TypeError, IndexError):
            return None

    def get_item_primaryid(self, item_index):
        try:
            return item_index['firstContentId']
        except (KeyError, TypeError, IndexError):
            return None

    def get_item_contents(self, item_index):
        try:
            return item_index['contents']
        except (KeyError, TypeError, IndexError):
            return None

    def get_item_heading(self, item_index):
        try:
            return item_index['heading']
        except (KeyError, TypeError, IndexError):
            return None

    def get_item_subheading(self, item_index):
        try:
            return item_index['subHeading']
        except (KeyError, TypeError, IndexError):
            return None

    def get_item_episode(self, item_index):
        try:
            return item_index['episode']
        except (KeyError, TypeError, IndexError):
            return None

    def get_item_photo(self, item_index):
        try:
            if self.get_item_photo_horizontal(item_index) is not None:
                return self.get_item_photo_horizontal(item_index)
            else:
                return self.get_item_photo_original(item_index)
        except (KeyError, TypeError, IndexError):
            return None

    def get_item_photo_original(self, item_index):
        try:
            return item_index['photos'][0]['photoUrlOriginal']
        except (KeyError, TypeError, IndexError):
            return None

    def get_item_photo_horizontal(self, item_index):
        try:
            return item_index['horizontalPhotos'][0]['photoUrlOriginal']
        except (KeyError, TypeError, IndexError):
            return None

    def get_item_public_start(self, item_index):
        try:
            return item_index['publicStart']
        except (KeyError, TypeError, IndexError):
            return None

    def get_item_schedule_start(self, item_index):
        try:
            return item_index['scheduleStart']
        except (KeyError, TypeError, IndexError):
            return None
