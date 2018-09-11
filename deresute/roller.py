'''
roll.py - .py file to do gacha roll simulations

Written by Alex Wong
Github: https://github.com/maplemist
Telegram: @maplemist
'''

from bs4 import BeautifulSoup
import collections
import csv
import json
import logging
import os
import random
import requests


'''
Definitions
'''

DIR = os.path.join(os.getcwd(), 'data', 'deresute', 'gacha')
URL = {
    'KIRARA': 'https://starlight.kirara.ca/gacha/{0}',
    '346LAB': 'http://starlight.346lab.org/gacha/{0}'
}


class hashabledict(dict):
    def __hash__(self):
        return hash(tuple(sorted(self.items())))


'''
Private Functions
'''

def _translator():
    '''
    Translated Romaji names into Kanji names.
    :rtype: function
    '''
    dic = hashabledict()
    filepath = os.path.join(os.getcwd(), 'data', 'deresute', 'names.csv')
    with open(filepath, newline='\n') as f:
        # ['Sagisawa Fumika', '鷺沢文香']
        reader = csv.DictReader(f, delimiter=',')
        for row in reader:
            dic[row['Romaji']] = row['Name']
    return lambda entity: dic.get(entity, entity)


def _compute_special_rate(pool, pickupSR):
    '''
    Compute the special rate and put it into the pool.
    :type pool: dict
    :type count: int
    :rtype: dict
    '''
    regSR = sum(1 for card in pool if not card['lim'] and card['rarity'] == 'SR')
    for card in pool:
        if card['rarity'] == 'SSR':
            card['sp_rate'] = card['rate']
        elif card['rarity'] == 'SR':
            card['sp_rate'] = 0.2 / pickupSR if 'pickup' in card else 0.77 / regSR
        elif card['rarity'] == 'R':
            card['sp_rate'] = 0


def _gather_helper(id, db):
    '''
    Gather pool information from online database.
    :type id: int
    :type db: str
    :rtype: dict
    '''
    pool = list()
    pickup, pickupSR = True, 0

    # Translator
    translate = _translator()

    # Find the table
    resp = requests.get(URL[db].format(id))
    soup = BeautifulSoup(resp.text, 'html.parser')
    table = soup.find('div', {'class': 'contains_large_table'}).table.tbody.findAll('tr')
    for row in table:
        tds = row.findAll('td')

        # Card
        card = hashabledict()

        if db == 'KIRARA':
            # kirara attributes
            card['lim'] = False if tds[0].text.strip() == 'No' else True
            card['rarity'] = row['class'][1].split('_')[0].upper()
            card['name'] = translate(tds[3].a.string)
            card['tag'] = '[' + tds[3].small.span.contents[0] + ']' if tds[3].small and tds[3].small.span else None

        elif db == '346LAB':
            # 346lab attributes
            card['lim'] = False if tds[0]['class'][0].split('_')[1] == 'false' else True
            card['rarity'] = row['class'][3].split('_')[0].upper()
            card['name'] = translate(tds[3].a.string)
            card['tag'] = '[' + tds[3].small.span.contents[0] + ']' if tds[3].small and tds[3].small.span else None

        # Rate
        card['rate'] = float(tds[1].text.strip('%')) / 100

        # TODO: (new) regular pickup ssr/sr check
        if pickup:
            if card['rarity'] in ['SSR', 'SR']:
                card['pickup'] = pickup
            elif card['rarity'] == 'R':
                pickup = False

        # Add card to the pool
        pool.append(card)

        # New cards (SSR, SR) are always on top, followed by regular (old) Rs
        # TODO: not sure about rerun limited SRs
        pickupSR += 1 if 'pickup' in card or (card['lim'] and card['rarity'] == 'SR') else 0

    # Compute special rate
    _compute_special_rate(pool, pickupSR)
    return pool


def _gather_info(id):
    '''
    Gather pool information from online database.
    :type id: int
    :rtype: list
    '''
    pool = None
    for db in URL:
        try:
            pool = _gather_helper(id, db)
            break
        except:
            continue
    return pool


def _write_pool(id, pool):
    '''
    Write the pool data into local json file.
    :type id: int
    :type pool: dict
    '''
    # Check directory existence
    if not os.path.exists(DIR):
        os.makedirs(DIR)

    # Write pool data to json file
    filepath = os.path.join(DIR, '{0}.json'.format(id))
    with open(filepath, 'w') as f:
        json.dump(pool, f, indent=2, ensure_ascii=False)


def _create_pool(id):
    '''
    Create pool based on id.
    :type id: int
    :rtype: list
    '''
    # Gather info
    pool = _gather_info(id)

    # Write json
    _write_pool(id, pool)
    return pool


def _get_pool(id):
    '''
    Get the pool information.
    :type id: int
    :rtype: dict
    '''
    # Check json existence
    filepath = os.path.join(DIR, '{0}.json'.format(id))
    if os.path.isfile(filepath):
        with open(filepath, 'r') as f:
            return json.load(f, object_hook=hashabledict)
    return _create_pool(id)


def _roll(id, amount, rate='rate'):
    '''
    Do 'amount' of rolls on the gacha pool with id.
    :type: id: int
    :type amount: int
    :rtype: lst
    '''
    # Get pool
    pool = _get_pool(id)

    # Use normal rate
    rates = [card[rate] for card in pool]
    return random.choices(pool, rates, k=amount)


def _get_results(gacha, rolls):
    '''
    Create output string based on the rolls.
    :type gacha: dict
    :type rolls: list
    :rtype: str
    '''
    # Build dict
    dic = collections.defaultdict(collections.Counter)
    for card in rolls:
        key = (card['rarity'], card['lim'])
        dic[key][card] += 1

    results = ''
    # Limited SSR
    lim_ssr = sum(dic[('SSR', True)].values())
    if lim_ssr > 0:
        results += '\n限定SSR: {0}\n'.format(lim_ssr) + \
                   '\n'.join('{0[tag]} {0[name]} {1}'.format(card, 'x{0}'.format(count) if count > 1 else '')
                   for card, count in dic[('SSR', True)].items())

    # Regular SSR
    reg_ssr = sum(dic[('SSR', False)].values())
    if reg_ssr > 0:
        results += '\nSSR: {0}\n'.format(reg_ssr) + \
                   ', '.join('{0[name]} {1}'.format(card, 'x{0}'.format(count) if count > 1 else '')
                   for card, count in dic[('SSR', False)].items())

    # Limited SR
    lim_sr = sum(dic[('SR', True)].values())
    if lim_sr > 0:
        results += '\n限定SR: {0}\n'.format(lim_sr) + \
                   '\n'.join('{0[tag]} {0[name]} {1}'.format(card, 'x{0}'.format(count) if count > 1 else '')
                   for card, count in dic[('SR', True)].items())

    # Regular SR & R
    footer = '\nSR: {0} \t R: {1}'.format(sum(dic[('SR', False)].values()), sum(dic[('R', False)].values()))
    return gacha['name'] + results + footer


def _output1(gacha):
    '''
    Roll the gacha pool, and get the result message from rolling the gacha pool id once.
    :type gacha: dict
    :rtype: dict
    '''
    card = _roll(gacha['id'], 1)[0]

    # Get parameters
    lim = '限' if card['lim'] else ''
    tag = card['tag'] if card['tag'] else ''
    return {'results': '{0[name]}\n{2}{1[rarity]}: {3} {1[name]}'.format(gacha, card, lim, tag), 'card': card}


'''
Public Functions
'''

def output(gacha, total):
    '''
    Roll the gacha pool, and get the result message from rolling the gacha pool id with k amount.
    :type gacha: dict
    :type total: int
    :rtype: dict
    '''
    if total == 1:
        return _output1(gacha)

    k = total // 10
    rolls = _roll(gacha['id'], total - k)
    tenth = _roll(gacha['id'], k, rate='sp_rate')
    return {'results': _get_results(gacha, rolls + tenth)}
