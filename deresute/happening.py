'''
happening.py - .py file to gather information from various API endpoints.

Written by Alex Wong
Github: https://github.com/maplemist
Telegram: @maplemist
'''

import json
import logging
import requests


URL = {
    'KIRARA': 'https://starlight.kirara.ca/api/v1/happening/{0}?extended_time_period_for_events=yes',
    '346LAB': 'http://starlight.346lab.org/api/v1/happening/{0}?extended_time_period_for_events=yes'
}

'''
Public Functions
'''

def at(time):
    '''
    Get status at the specific time.
    :type time: 'now' or timestamp
    :rtype: dict
    '''
    logging.info('happening at: {0}'.format(time))
    status = None
    headers = {'content-type': 'application/json'}
    for url in URL:
        r = requests.get(URL[url].format(time), headers=headers)
        if r.status_code == 200:
            status = json.loads(r.text)
            break
    return status


def now():
    '''
    Get current information.
    :rtype: dict
    '''
    return at('now')
