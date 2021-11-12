# coding: utf-8
import re
from datetime import datetime
import requests

from .constants import (
    USER_AGENT
)


def download_url(url, header=None):
    for retries in range(0, 5):
        try:
            headers = {}
            if header:
                headers = {k: v for k, v in header}
            headers['User-Agent'] = USER_AGENT
            contents = requests.get(url, headers=headers)
            return contents
        except:
            raise RuntimeError('Could not open URL: {}'.format(url))


def strip_tags(string):
    # simple, unsafe stripper
    return re.sub('<[^<]+?>', '', string)


def convert_timestamp(input):
    return datetime.fromtimestamp(int(input)).strftime('%Y-%m-%d %H:%M:%S')


def get_subtitle_language(lang):
    # helper function to map human readable settings to required abbreviation
    if int(lang) == 0:
        return "ET"
    elif int(lang) == 1:
        return "VA"
    elif int(lang) == 2:
        return "RU"
    else:
        pass


def get_colour(color):
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
