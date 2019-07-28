'''
chihiro.py - main .py file for the Chihiro telegram bot

Telegram bot to publish information related to 'The iDOLM@STER Cinderella Girls Starlight Stage'
- built-on python-telegram-bot
- inspired by summertriangle-dev/discordbot
- customized for Hong Kong users ;)

Written by Alex Wong
Github: https://github.com/maplemist
Telegram: @maplemist
'''

from datetime import datetime, time, timedelta

import ast
import configparser
import json
import logging
import pytz
import os
import re
import telegram.ext as tg

import deresute


'''
Definitions
'''

CFG_FILE = '.config'
JST = pytz.timezone('Asia/Tokyo')


'''
Config Related Private Helper Functions
'''

def _read_config(section, key):
    '''
    Get the val of key in section from config file.
    :type section: str
    :type key: str
    :rtype: str
    '''
    cfg = configparser.ConfigParser()
    cfg.readfp(open(CFG_FILE))
    return cfg.get(section, key)


def _get_token():
    '''
    Get token from config file.
    :rtype: str
    '''
    return _read_config('Token', 'Chihiro')


def _get_chat_id(chat='Testing'):
    '''
    Get chat_id from config file.
    :rtype: int
    '''
    return int(_read_config('Chat', chat))


def _get_forward(chat):
    '''
    Get forward chat_id from config file.
    :rtype: int
    '''
    return int(_read_config('Forward', chat))


def _get_username(username='owner'):
    '''
    Get username from config file.
    :rtype: str
    '''
    return _read_config('Username', username)


def _has_tag(text):
    '''
    Check if the text has tag or not.
    :rtype: bool
    '''
    tags = ast.literal_eval(_read_config('Tags', 'Chihiro'))
    return any(tag in text for tag in tags)


'''
Private Helper Functions
'''

def _get_patterns(json):
    '''
    Create patterns object from json.
    :type json: dict
    :rtype: dict
    '''
    patterns = {}
    for key, val in json.items():
        patterns[key] = re.compile(val, re.I)
    return patterns


def _get_tmr():
    '''
    Get datetime object of next 12am (JST).
    :rtype: datetime object
    '''
    d = datetime.today()
    offset = 1 if d.hour >= 8 else 0
    d = d.replace(hour=8, minute=0, second=3, microsecond=0) + timedelta(days=offset)
    logger.info('JobQueue first running time: {0}'.format(d))
    return d


def _event_helper(type, unit, rank=None):
    '''
    Helper function for event related commands.
    :type type: str
    :type unit: str
    :type rank: str or None
    :rtype: str
    '''
    # Check what is happening
    resp = deresute.happening.now()
    if not resp or not resp['events']:
        return canned['No_Event']

    # Parse event information into output
    resp = resp['events'][0]
    result, ended = deresute.event.event_output(resp)

    # Get cutoff data
    try:
        cutoff = deresute.event.get_cutoffs(resp['id'], type, rank=rank)
        result += '\n' + deresute.event.cutoff_output(cutoff, unit, ended)
    except (deresute.event.CurrentEventNotValidError, deresute.event.CurrentEventNotRankingError) as e:
        return result + canned['Not_Ranking']
    except (deresute.event.NoDataCurrentlyAvailableError, TypeError) as e:
        return result + canned['No_Data']
    return result


def _gacha_roll_helper(total, index):
    '''
    Gacha roll helper function.
    :type total: int
    :type index: int
    :rtype: dict
    '''
    resp = deresute.happening.now()
    if not resp or not resp['gachas']:
        return {}

    # Try to get the dict info for gacha
    resp = resp['gachas']
    try:
        gacha = resp[index - 1]
    except IndexError:
        gacha = resp[0]

    return deresute.roller.output(gacha, total)


def _error(bot, update, error):
    '''Log Errors caused by Updates.'''
    logger.warning('Update "{0}" caused error "{1}"'.format(update, error))


'''
Command Functions - Event Information Related
'''

def event(bot, update):
    '''Send messages when command /event is issued.'''
    logger.info('{0} @ {1}: {2}'.format(update.message.from_user.username, update.message.chat.title, update.message.text))
    update.message.reply_text(_event_helper('EVENT', 'pts'))


def trophy(bot, update):
    '''Send messages when command /trophy is issued.'''
    logger.info('{0} @ {1}: {2}'.format(update.message.from_user.username, update.message.chat.title, update.message.text))
    update.message.reply_text(_event_helper('TROPHY', '分'))


def top(bot, update):
    '''Send messages when command /top<number> is issued.'''
    logger.info('{0} @ {1}: {2}'.format(update.message.from_user.username, update.message.chat.title, update.message.text))
    key = patterns['top'].match(update.message.text).group(1)
    update.message.reply_text(_event_helper(key if key != '10' else 'TOP10', 'pts'))


'''
Command Functions - Gacha Information Related
'''

def gacha(bot, update):
    '''Send messages when command /gacha is issued.'''
    logger.info('{0} @ {1}: {2}'.format(update.message.from_user.username, update.message.chat.title, update.message.text))
    # Check what is happening
    resp = deresute.happening.now()
    if not resp:
        update.message.reply_text(canned['No_Data'])

    # Get gacha outputs
    gachas = {}
    gachas['curr'] = deresute.gacha.get_curr(resp['gachas'])
    gachas['next'] = deresute.gacha.get_next(resp['gachas'])

    # Output messages
    for gacha in gachas['curr']:
        update.message.reply_text(gacha, quote=False)
    if gachas['next']:
        for gacha in gachas['next']:
            update.message.reply_text(gacha, quote=False)
        update.message.reply_animation(canned['Chihiro_Money'], quote=False)


def next_gacha(bot, update):
    '''Send messages when command /nextgacha is issued.'''
    logger.info('{0} @ {1}: {2}'.format(update.message.from_user.username, update.message.chat.title, update.message.text))
    # Check what is happening
    resp = deresute.happening.now()
    if not resp:
        update.message.reply_text(canned['No_Data'])

    # Get gacha outputs
    gachas = deresute.gacha.get_next(resp['gachas'])

    # Output messages
    if gachas:
        for gacha in gachas:
            update.message.reply_text(gacha, quote=False)
        update.message.reply_animation(canned['Chihiro_Money'], quote=False)
    else:
        update.message.reply_text(canned['Calmdown'])


def roll(bot, update):
    '''Send messages when command /(number)roll is issued.'''
    logger.info('{0} @ {1}: {2}'.format(update.message.from_user.username, update.message.chat.title, update.message.text))

    # Get parameters from input message
    params = patterns['roll'].match(update.message.text).groups(0)
    count = int(params[0]) if params[0] != '' and 0 < int(params[0]) <= 300 else 1
    index = int(params[1]) if params != 0 else 0

    # Gacha roll simulations
    output = _gacha_roll_helper(count, index)
    if not output:
        update.message.reply_text(canned['No_Data'])
        return

    update.message.reply_text(output['results'])

    # Send stickers for single roll
    if count == 1:
        if not output['card']['lim'] and output['card']['rarity'] != 'SSR':
            update.message.reply_sticker(canned['Chihiro_R'])
        else:
            update.message.reply_sticker(canned['Chihiro_SSR'])


'''
Command Functions - Others
'''

def help(bot, update):
    '''Send a message when the command /help is issued.'''
    logger.info('{0} @ {1}: {2}'.format(update.message.from_user.username, update.message.chat.title, update.message.text))
    output = output = 'CGSS相關指令列表:' + \
             '\n/event - イベント資訊' + \
             '\n/trophy - 飛機盃資訊' + \
             '\n/gacha - ガチャ資訊' + \
             '\n/roll - 單抽' + \
             '\n/10roll - 十連' + \
             '\n/300roll - 300連/井'
    update.message.reply_text(output)


def calmdown(bot, update):
    '''Send a message when the command /calmdown is issued.'''
    logger.info('{0} @ {1}: {2}'.format(update.message.from_user.username, update.message.chat.title, update.message.text))
    update.message.reply_text(canned['Calmdown'])


def ken(bot, update):
    '''Send a message when the command /ken is issued.'''
    logger.info('{0} @ {1}: {2}'.format(update.message.from_user.username, update.message.chat.title, update.message.text))
    update.message.reply_animation(canned['Ken'], caption=canned['Ken_caption'])


def epluslomo(bot, update):
    '''Send a message when the command /epluslomo is issued.'''
    logger.info('{0} @ {1}: {2}'.format(update.message.from_user.username, update.message.chat.title, update.message.text))
    update.message.reply_animation(canned['Eplus'])


'''
Twitter Forwarding Functions
'''

def forward(bot, update):
    '''Forward message when target user sends a message in the specific channel.'''
    logger.info('@ {0} : {1}'.format(update.channel_post.chat.title, update.channel_post.text.split('\n')[1]))
    if _has_tag(update.channel_post.text):
        bot.send_message(chat_id=_get_chat_id(chat='Chihiro'), text=update.channel_post.text)
        # bot.send_message(chat_id=_get_chat_id(), text=update.channel_post.text) # Debug


'''
JobQueue Functions
'''

def callback_birthday(bot, job):
    '''Job to do birthday callbacks.'''
    logger.info('birthday callback')
    idols = deresute.birthday.get_today()
    for idol in idols:
        congrats = canned['HBD'].format(idol)
        bot.send_message(chat_id=_get_chat_id(), text=congrats) # Debug
        bot.send_message(chat_id=_get_chat_id(chat='Chihiro'), text=congrats)


'''
Debug
'''

def debug(bot, update):
    '''Echo the user message.'''
    logger.info('{0} @ {1}'.format(update.message.from_user.username, update.message.chat.id))
    if not update.message.chat.title:
        update.message.reply_text(str(update))


'''
Main
'''

def main():
    '''
    Main function to run the bot.
    '''
    # set up updater and dispatcher
    updater = tg.Updater(_get_token())
    dp = updater.dispatcher
    jq = updater.job_queue

    # JobQueue functions
    job_bday = jq.run_repeating(callback_birthday, interval=timedelta(days=1), first=_get_tmr())

    # Event related
    dp.add_handler(tg.CommandHandler('event', event))
    # dp.add_handler(tg.CommandHandler('trophy', trophy))
    # dp.add_handler(tg.RegexHandler(patterns['top'], top))

    # Gacha related
    dp.add_handler(tg.CommandHandler('gacha', gacha))
    # dp.add_handler(tg.CommandHandler('nextgacha', next_gacha))
    # dp.add_handler(tg.RegexHandler(patterns['roll'], roll))

    # Others
    dp.add_handler(tg.RegexHandler(patterns['help'], help))
    dp.add_handler(tg.RegexHandler(patterns['calmdown'], calmdown))
    dp.add_handler(tg.RegexHandler(patterns['ken'], ken))
    dp.add_handler(tg.RegexHandler(patterns['epluslomo'], epluslomo))

    # Twitter forwarding
    dp.add_handler(tg.MessageHandler(tg.Filters.chat(chat_id=_get_forward('Chihiro')), forward))

    # Debug
    dp.add_handler(tg.MessageHandler(tg.Filters.user(username=_get_username()), debug))

    # log errors
    dp.add_error_handler(_error)

    # start the bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    # Enable logging
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Get canned response from json file.
    with open(os.path.join(os.getcwd(), 'data', 'deresute', 'canned.json'), 'r') as f:
        canned = json.load(f)

    with open(os.path.join(os.getcwd(), 'data', 'deresute', 'patterns.json'), 'r') as f:
        patterns = _get_patterns(json.load(f))

    logger.info('Chihiro starting...')
    main()
