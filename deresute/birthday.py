'''
birthday.py - .py file to do birthday related functions

Written by Alex Wong
Github: https://github.com/maplemist
Telegram: @maplemist
'''

from bs4 import BeautifulSoup
from datetime import datetime
import collections
import json
import os
import pytz
import regex
import requests


'''
Definitions
'''

DIR = os.path.join(os.getcwd(), 'data', 'deresute')
FILENAME = {'CHAR': 'birthday.json', 'CV': 'birthday-cv.json'}
URL = 'https://imascg-slstage.boom-app.wiki/entry/idol-birthday'
JST = pytz.timezone('Asia/Tokyo')


'''
Private Function
'''

def _write_file(data, dir, filename):
    '''
    Write data to the file.
    :type data: dict
    :type dir: str
    :type filename: str
    '''
    # Check directory
    if not os.path.exists(dir):
        os.makedirs(dir)

    # Write birthday data to json file
    filepath = os.path.join(dir, filename)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _get_from_db():
    '''
    Get data from online database.
    :rtype: dict
    '''
    data = collections.defaultdict(lambda: collections.defaultdict(list))
    pattern = regex.compile('(\d*)月(\d*)日')

    # Read from online database
    resp = requests.get(URL)
    soup = BeautifulSoup(resp.text, 'html.parser')
    months = soup.findAll('div', {'class': 'basic'})[2:-2]
    for month in months:
        entities = month.table.findAll('tr')[1:]

        for entity in entities:
            name = entity.td.a.text
            bday = entity.findAll('td')[1].text
            mm, dd = pattern.match(bday).groups()
            data[mm][dd].append(name)
    return data


def _get_all():
    '''
    Get all characters' birthday information.
    :rtype: dict
    '''
    # check file existence
    filepath = os.path.join(DIR, FILENAME['CHAR'])
    if os.path.isfile(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)

    data = _get_from_db()
    _write_file(data, DIR, FILENAME['CHAR'])
    return data


def _get_all_cv():
    '''
    Get all CVs' birthday information.
    :rtype: dict
    '''
    filepath = os.path.join(DIR, FILENAME['CV'])
    if os.path.isfile(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    # TODO: read from https://imas-db.jp/calendar/birthdays
    return {}


'''
Public Functions
'''

def get_date(datetime):
    '''
    Get birthday information for date.
    :type datetime: datetime
    :rtype: list
    '''
    ch_data = _get_all()
    cv_data = _get_all_cv()
    return ch_data[str(datetime.month)].get(str(datetime.day), []) + \
           cv_data[str(datetime.month)].get(str(datetime.day), [])


def get_today():
    '''
    Get today's birthday information.
    :rtype: list
    '''
    return get_date(pytz.utc.localize(datetime.utcnow()).astimezone(JST))
