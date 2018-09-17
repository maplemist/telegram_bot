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
FILENAME = 'birthdays.json'
URL = 'https://imas-db.jp/calendar/birthdays'
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
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)


def _get_from_db():
    '''
    Get data from online database.
    :rtype: dict
    '''
    data = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(list)))

    # Read from online database
    resp = requests.get(URL)
    soup = BeautifulSoup(resp.text, 'html.parser')
    months = soup.findAll('ul', {'class': 'birthdays-list'})
    for month in months:
        entities = month.findAll('li', {'data-series-ids': '4'}) # CG

        for entity in entities:
            if entity['data-kind'] == '1': # Character
                type = 'CHAR'
            elif entity['data-kind'] == '2': # CV
                type = 'CV'
            else:
                continue

            name = entity.span.text.split('(')[0]
            mm, dd = entity.text.split(' ')[0].split('/')
            data[type][int(mm)][int(dd)].append(name)
    return data


def _get_all():
    '''
    Get all CG related birthday information.
    :rtype: dict
    '''
    # Check file existence
    filepath = os.path.join(DIR, FILENAME)
    if os.path.isfile(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)

    data = _get_from_db()
    _write_file(data, DIR, FILENAME)
    return data


'''
Public Functions
'''

def get_date(datetime):
    '''
    Get birthday information for date.
    :type datetime: datetime
    :rtype: list
    '''
    data = _get_all()
    return data['CHAR'][str(datetime.month)].get(str(datetime.day), []) + \
           data['CV'][str(datetime.month)].get(str(datetime.day), [])


def get_today():
    '''
    Get today's birthday information.
    :rtype: list
    '''
    return get_date(pytz.utc.localize(datetime.utcnow()).astimezone(JST))
