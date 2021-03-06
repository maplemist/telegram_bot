'''
event.py - .py file to gather event information.

Written by Alex Wong
Github: https://github.com/maplemist
Telegram: @maplemist
'''

from bs4 import BeautifulSoup
from collections import namedtuple
from datetime import datetime, timedelta
import json
import logging
import pytz
import requests

from . import happening

'''
Definitions
'''

URL = {
    'KIRARA': 'https://starlight.kirara.ca/api/v1/happening/now?extended_time_period_for_events=yes',
    '346LAB': 'http://starlight.346lab.org/api/v1/happening/now?extended_time_period_for_events=yes',
    'EVENT': 'https://aidoru.info/event/border/{0}/501/2001/10001/20001/60001/120001',
    # 'EVENT': 'https://deresute.mon.moe/d?type=0&rank=501+2001+10001+20001+60001+120001+200001&event={0}',
    # 'TOP10': 'https://deresute.mon.moe/d?type=0&rank=1+2+3+4+5+6+7+8+9+10&event={0}',
    # '1120': 'https://deresute.mon.moe/d?type=0&rank=11+12+13+14+15+16+17+18+19+20&event={0}',
    # '2130': 'https://deresute.mon.moe/d?type=0&rank=21+22+23+24+25+26+27+28+29+30&event={0}',
    # '100': 'https://deresute.mon.moe/d?type=0&rank=50+60+70+80+90+100+110&event={0}',
    # '500': 'https://deresute.mon.moe/d?type=0&rank=201+301+401+501+601+701+801&event={0}',
    # 'PARAM': 'https://deresute.mon.moe/d?type=0&rank={1}&event={0}',
    # 'TROPHY': 'https://deresute.mon.moe/d?type=1&rank=5001+10001+{0}&event={1}',
    'TEASER': 'https://games.starlight-stage.jp/image/event/teaser/event_teaser_{0}.png',
    'BANNER': 'https://apis.game.starlight-stage.jp/image/announce/header/header_event_{0:04d}.png',
    'BANNER_ID': 'https://deresute.mon.moe/event',
    'NEWS': 'https://apis.game.starlight-stage.jp/information/index/0/1/10/1'
}

JST = pytz.timezone('Asia/Tokyo')

BRONZE = {
    '1': '40001',   # token
    '3': '50001',   # groove
    '5': '50001'    # parade
}

JA_MAGNITUDE = {
    '百': 100,
    '千': 1000,
    '万': 10000,
    '億': 100000000
}

cutoff_t = namedtuple('cutoff_t', ('name', 'collected', 'tiers'))
tier_t = namedtuple('tier_t', ('position', 'points', 'delta'))


'''
Exceptions
'''

class NoDataCurrentlyAvailableError(Exception):
    pass

class NoCurrentEventError(Exception):
    pass

class CurrentEventNotValidError(Exception):
    pass

class CurrentEventNotRankingError(Exception):
    pass


'''
Private Functions
'''

def _is_token(id):
    '''
    Check whether event is Token.
    :type id: int
    :rtype: bool
    '''
    return 999 < id < 2000


def _is_groove(id):
    '''
    Check whether event is Groove.
    :type id: int
    :rtype: bool
    '''
    return 2999 < id < 4000


def _is_parade(id):
    '''
    Check whether event is Parade.
    :type id: int
    :rtype: bool
    '''
    return 4999 < id < 6000


def _is_ranking(id):
    '''
    Check whether event is ranking.
    :type id: int
    :rtype: bool
    '''
    return _is_token(id) or _is_groove(id)


def _has_highscore(id):
    '''
    Check whether event has highscore.
    :type id: int
    :rtype: bool
    '''
    return _is_token(id) or _is_groove(id) or _is_parade(id)


def _get_banner_id():
    '''
    Get banner ID.
    '''
    # TODO: use cache
    resp = requests.get(URL['BANNER_ID'])
    soup = BeautifulSoup(resp.text, 'html.parser')
    entries = soup.find('table', {'class': 'columns'}).findAll('tr')
    return len(entries)


def _get_banner_url():
    '''
    Get banner URL.
    '''
    # read posts
    resp = requests.get(URL['NEWS'])
    soup = BeautifulSoup(resp.text, 'html.parser')
    posts = soup.findAll('a', {'class': 'none'})
    events = [post['href'] for post in posts if 'イベント' in post.text and '開催' in post.text]
    if not events:
        return URL['BANNER'].format(_get_banner_id())

    # read event post
    resp = requests.get(events[0])
    soup = BeautifulSoup(resp.text, 'html.parser')
    imgs = [img['src'] for img in soup.findAll('img') if 'header_event' in img['src']]
    return imgs[0] if imgs else URL['BANNER'].format(_get_banner_id())


def _get_timeleft(timestamp):
    '''
    Get time remaining from timestamp.
    :type timestamp: str
    :rtype: str
    '''
    now = pytz.utc.localize(datetime.utcnow())
    end_dt = pytz.utc.localize(datetime.utcfromtimestamp(timestamp)).astimezone(JST)
    return end_dt - now


def _get_remaining_time(timestamp):
    '''
    Get time remaining from timestamp.
    :type timestamp: str
    :rtype: datetime.timedelta
    '''
    # Get time
    timeleft = _get_timeleft(timestamp)
    hours = timeleft.seconds // (60 * 60)
    minutes = (timeleft.seconds // 60) % 60

    # Time remaining
    time_remaining = '\nあと'
    if timeleft.days > 0:
        time_remaining += ' {0} 日 '.format(timeleft.days)
    if hours > 0:
        time_remaining += ' {0} 時間 '.format(hours)
    time_remaining += ' {0} 分'.format(minutes)
    return time_remaining


'''
Public Functions
'''

def get_cutoffs(event_id, url_type, rank=None):
    '''
    Get the cutoff information of the event.
    '''
    if not _has_highscore(event_id):
        raise CurrentEventNotValidError()

    if not _is_ranking(event_id) and url_type != 'TROPHY':
        raise CurrentEventNotRankingError()

    result = None
    # TODO: cache

    # Fetch cutoff data
    headers = {'content-type': 'text/plain; charset=utf-8'}
    if url_type == 'TROPHY':
        url = URL[url_type].format(BRONZE[str(event_id)[:1]], str(event_id))
    # elif url_type == 'PARAM' and rank != None:
    #     url = URL[url_type].format(str(event_id), rank)
    else:
        url = URL[url_type].format(str(event_id))

    with requests.get(url, headers=headers, stream=True) as resp:
        if resp.status_code != 200:
            return result

        # Read the data from script in the html
        soup = BeautifulSoup(resp.text, 'html.parser')
        text = soup.findAll('script', {"type": "text/javascript"})[3].text
        text = text.split('d3.select(\'#chart_div\').append(\'svg\')\n\t\t\t\t.datum(function() {\n\t\t\t\t\treturn ')[1]
        text = text.split('\n\t\t\t\t})\n\t\t\t\t.call(chart);')[0]
        text = text.replace('area:', '"area":')
        text = text.replace('key:', '"key":')
        text = text.replace('values:', '"values":')
        border_data = json.loads(text)

        # Obtain the latest information
        headers, cutoffs, deltas = [], [], []
        for data in border_data:
            headers.append(data['key'].split(' ')[0])
            cutoffs.append(data['values'][-1][1])

            # Find data with 1 timedelta from latest data
            deltas.append(data['values'][-2][1] if len(data['values']) > 2 else 0)

        # For some reason the timestamp is not unix epoch time and it is 9 hours ahead of it
        lastUpdate = int(data['values'][-1][0]) / 1000
        lastUpdate = lastUpdate - 60 * 60 * 9

        # Generate data
        tiers = tuple(tier_t(x, y, y - z) for x, y, z in zip(headers, cutoffs, deltas))
        result = cutoff_t('Event Name', pytz.utc.localize(datetime.utcfromtimestamp(lastUpdate)).astimezone(JST), tiers)
        return result


def event_output(event):
    '''
    Parse event information into output string.
    :type event: dict
    :rtype: str
    '''
    # Event time string
    s_dt = pytz.utc.localize(datetime.utcfromtimestamp(event['start_date'])).astimezone(JST)
    e_dt = pytz.utc.localize(datetime.utcfromtimestamp(event['end_date'])).astimezone(JST)
    event_time = '\n{0} - {1}'.format(s_dt.strftime('%m/%d %H:%M'), e_dt.strftime('%m/%d %H:%M %Z'))

    # Get Banner URL
    # TODO: Need to fix
    # banner = '\n' + _get_banner_url()
    banner = ''

    # Event status
    timeleft = _get_timeleft(event['end_date'])
    ended = timeleft < timedelta(seconds=0)
    event_status = '\n*** イベント終了 ***' if ended else _get_remaining_time(event['end_date'])
    return (event['name'] + event_time + event_status + banner, ended)


def cutoff_output(cutoff, unit, ended):
    '''
    Parse cutoff data into the output string.
         Input: cutoff Data
        Output: string
    '''
    if not cutoff:
        raise NoDataCurrentlyAvailableError()

    # Get time
    now = pytz.utc.localize(datetime.utcnow())
    collect_date = cutoff.collected.astimezone(JST)

    # Output string
    header = 'イベントpt 順位\n' if unit == 'pts' else 'ハイスコアランキング 順位\n'
    last_update = '\n最後更新: {0} JST'.format(collect_date.strftime('%m/%d %H:%M'))

    # Event ended already
    if ended:
        cutoff_content = '\n'.join(['#{0.position}: {0.points:,} {1}'.format(tier, unit) for tier in cutoff.tiers])
        return header + cutoff_content + last_update

    # Event still ongoing
    cutoff_content = '\n'.join([
        '#{0.position}: {0.points:,} {1} ({2}{0.delta:})'.format(tier, unit, '+' if tier.delta >= 0 else '')
        for tier in cutoff.tiers])

    next_update = '\n(次の更新: {0} JST)'.format((collect_date + timedelta(minutes=15)).strftime('%H:%M'))
    return header + cutoff_content + last_update + next_update
