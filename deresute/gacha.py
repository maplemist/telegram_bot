'''
gacha.py - .py file to gather gacha information.

Written by Alex Wong
Github: https://github.com/maplemist
Telegram: @maplemist
'''

from datetime import datetime, timedelta
import pytz

from . import happening

'''
Definitions
'''

JST = pytz.timezone('Asia/Tokyo')
BANNER = {
    # 'gacha': 'http://game.starlight-stage.jp/image/announce/header/header_gacha_{0}.png',
    'gacha': 'http://apis.game.starlight-stage.jp/image/announce/header/header_gacha_{0}.png',
    'rerun': 'http://game.starlight-stage.jp/image/announce/image/header_gacha_{0}.png'
}
TYPE = {
    'rerun': '復刻',
    'select': 'タイプセレクト'
}


'''
Private Functions
'''

def _prev_timestamp(timestamp):
    '''
    Get the previous timestamp.
    :type timestamp: str
    :rtype: str
    '''
    return str(int(timestamp) - 1000)


def _get_banner(gacha):
    '''
    Get the banner of the gacha.
    :type gacha: dict
    :rtype: str
    '''
    # Reruns
    if TYPE['rerun'] in gacha['name']:
        return BANNER['rerun'].format(str(gacha['id'])[1:])

    # Type Select
    elif TYPE['select'] in gacha['name']:
        offset = 0
        prev = happening.at(_prev_timestamp(gacha['start_date']))
        prev = prev['gachas'][0]
        while TYPE['select'] in prev['name']:
            offset -= 1
            prev = happening.at(_prev_timestamp(prev['start_date']))
            prev = prev['gachas'][0]
        gacha['name'] += ' (Cute)' if offset == 0 else ' (Cool)' if offset == -1 else ' (Passion)'
        return BANNER['gacha'].format(str(gacha['id'] + offset)[1:])

    # General
    return BANNER['gacha'].format(str(gacha['id'])[1:])


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
        time_remaining += ' {0} 日'.format(timeleft.days)
    if hours > 0:
        time_remaining += ' {0} 時間'.format(hours)
    time_remaining += ' {0} 分'.format(minutes)
    return time_remaining


'''
Public Functions
'''

def get_curr(gachas):
    '''
    Parse the gacha data into the output string.
    :type gachas: list
    :rtype: list
    '''
    # Get remaining time string
    time_remaining = _get_remaining_time(gachas[0]['end_date'])

    # Put gachas into list
    results = []
    for gacha in gachas:
        banner = _get_banner(gacha)
        gacha_content = '{0[name]}\n{1}'.format(gacha, banner)
        results.append(gacha_content + time_remaining)
    return results


def get_next(gachas):
    '''
    Try to get the next gacha data into the output string.
    :type gachas: list
    :rtype: list
    '''
    # Get timeleft
    timeleft = _get_timeleft(gachas[0]['end_date'])

    # Return None if gacha pool is not going to change soon
    if timeleft >= timedelta(minutes=9):
        return None

    minutes = (timeleft.seconds // 60) % 60
    results = ["次のガチャまであと {0} 分\nプロデューサーさん、準備はいいですか？".format(minutes)]

    # Try to get previous gacha
    gacha = gachas[0]
    prev = happening.at(_prev_timestamp(gacha['start_date']))
    prev = prev['gachas'][0]

    # Current is Type Select
    if TYPE['select'] in gacha['name']:
        # Check the offset
        offset = 0
        while TYPE['select'] in prev['name']:
            offset -= 1
            prev = happening.at(_prev_timestamp(prev['start_date']))
            prev = prev['gachas'][0]

        # Current is Cute or Cool
        if offset in [0, -1]:
            # Adding next type to gacha name
            next_type = ' (Cool)' if offset == 0 else ' (Passion)'
            results[0] += '\n次の' + gacha['name'].split('ガチャ')[0] + next_type

        # Current is Passion
        else:
            next_id = gacha['id'] + 1
            results[0] += '\n' + BANNER['gacha'].format(str(next_id)[1:])

        return results

    next_id = gacha['id'] + 1
    # 3rd general pool of the month (Current is general, and previous is type select)
    if TYPE['select'] in prev['name']:
        results[0] += '\n' + BANNER['gacha'].format(str(next_id)[1:])
        return results

    # Rerun next (current is general, 2nd previous is type select)
    prev = happening.at(_prev_timestamp(prev['start_date']))
    prev = prev['gachas'][0]
    if TYPE['select'] in prev['name']:
        results.append(BANNER['rerun'].format(str(next_id)[1:]))
        results.append(BANNER['rerun'].format(str(next_id + 1)[1:]))
        if next_id != 296: # TODO: Hot Spring
            results.append(BANNER['rerun'].format(str(next_id + 2)[1:]))

    # General
    else:
        results[0] += '\n' + BANNER['gacha'].format(str(next_id)[1:])
    return results
