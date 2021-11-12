# coding: utf-8
import json

from .helpers import download_url
from .constants import (
    ERR_API_BASEURL
)


class Search:
    def __init__(self, search_type='', search_phrase=''):

        self.options = '{"total":0,"page":1,"limit":50,"offset":0,' \
                       '"category":3905,"phrase":"%s","publicStart":"",' \
                       '"publicEnd":"","timeFromSchedule":false,' \
                       '"types":["media"],"viewTypes":["episode","movie"]}' % search_phrase
        self.url = '%ssearch/getVodContents/?type=%s&options=%s' % (ERR_API_BASEURL, search_type, self.options)

        print(self.url)
        self.content = download_url(self.url).json()

    def get_response(self):
        try:
            return self.content['video']['totalFound'], self.content['audio']['totalFound']
        except (KeyError, TypeError):
            return None

    def get_results(self, content_type='video'):
        results = {}
        try:
            return self.content[content_type]['contents']
        except (KeyError, TypeError):
            return None
