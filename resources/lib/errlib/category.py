# coding: utf-8
from __future__ import unicode_literals
import json

from . import helpers
from .constants import (
    ERR_API_BASEURL,
    ERR_API_VERSION,
    EMPTYSTRING,
    DEFAULT_VERTICAL_PHOTO
)


class Category:
    def __init__(self, categoryid):
        self.domain = 'jupiter.err.ee'
        self.url = '{}{}/category/getByUrl?url={}&domain={}'.format(ERR_API_BASEURL, ERR_API_VERSION, categoryid,
                                                                    self.domain)
        self.content = helpers.download_url(self.url).json()

    def get_categories(self):
        categories = []
        for category in self.content['data']['category']['frontPage']:
            if 'Jätka' not in category['header']:  # filter it out for now as we don't have session support
                categories.append(category['header'])

        return categories

    def get_gategory_items(self, category=''):
        category_items = []

        for category_list in self.content['data']['category']['frontPage']:
            if category_list['header'] == category:
                for category_list_items in category_list['data']:
                    category_item = []
                    category_item.append(category_list_items['id']),
                    category_item.append(category_list_items['heading'])
                    try:
                        category_item.append(category_list_items['photos'][0]['photoTypes']['17']['url'])
                    except (KeyError, IndexError):
                        try:
                            category_item.append(category_list_items['verticalPhotos'][0]['photoUrlOriginal'])
                        except (KeyError, IndexError):
                            category_item.append(DEFAULT_VERTICAL_PHOTO)
                    try:
                        category_item.append(helpers.strip_tags(category_list_items['lead']))
                    except (KeyError, IndexError):
                        category_item.append(EMPTYSTRING)
                    category_items.append(category_item)

        return category_items
