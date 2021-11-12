# coding: utf-8
import json
from .helpers import download_url
from .constants import (
    ERR_API_BASEURL,
    ERR_API_VERSION
)


class Menu:
    def __init__(self, menuid=555):
        self.url = '{}{}/menu/getMenuById?menuId={}'.format(ERR_API_BASEURL,
                                                            ERR_API_VERSION, menuid)
        self.content = download_url(self.url).json()

    def get_menu_items(self):
        return self.content['data']['items']
