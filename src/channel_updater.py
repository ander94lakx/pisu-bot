from dotenv import load_dotenv
import logging
import os
import schedule
import shelve
from shelve import Shelf
import telegram
from time import sleep

import constants
from scrap import scrap_fotocasa, scrap_idealista


# Configuration dict
config: Shelf = None


def update_channel():
    # Get channel and bot info
    token = os.getenv('TOKEN')
    channel_id = os.getenv('CHANNEL_ID')

    bot = telegram.Bot(token=token)

    # Remove previously sended messages
    messages = []
    if 'sent_messages' in config:
        messages = config['sent_messages']
        for message in messages:
            try:
                bot.delete_message(chat_id=channel_id, message_id=message)
            except Exception as e:
                logging.error(e)
        del config['sent_messages']
        config.sync()


    # Scrap all with the default top price
    flats_list = []
    if (constants.UPDATE_IDEALISTA):
        messages.append(bot.send_message(chat_id=channel_id, text=constants.SEARCHING_IDEALISTA_MESSAGE, disable_notification=True).message_id)
        flats_list.extend(scrap_idealista(config['top_price']))
    if (constants.UPDATE_FOTOCASA):
        messages.append(bot.send_message(chat_id=channel_id, text=constants.SEARCHING_FOTOCASA_MESSAGE, disable_notification=True).message_id)
        flats_list.extend(scrap_fotocasa(config['top_price']))

    old_flats, new_flats = get_old_and_new_flats(flats_list)

    # Send the messages with the info
    # Saves the message_id of the messages to be able to delete them on the next one

    if old_flats or new_flats:
        messages.append(bot.send_message(chat_id=channel_id, text=constants.INITIAL_AUTO_MESSAGE, disable_notification=True).message_id)

        if old_flats:
            messages.append(bot.send_message(chat_id=channel_id, text=constants.OLD_FLATS_MESSAGE, disable_notification=True).message_id)
            for flat in old_flats:
                messages.append(bot.send_photo(chat_id=channel_id, caption=flat.link, photo=flat.image, disable_notification=True).message_id)
                sleep(1)

        if new_flats:
            messages.append(bot.send_message(chat_id=channel_id, text=constants.NEW_FLATS_MESSAGE, disable_notification=True).message_id)
            for flat in new_flats:
                messages.append(bot.send_photo(chat_id=channel_id, caption=flat.link, photo=flat.image, disable_notification=True).message_id)
                sleep(1)

        messages.append(bot.send_message(chat_id=channel_id, text=constants.FINAL_MESSAGE, disable_notification=True).message_id)

    else:
        messages.append(bot.send_message(chat_id=channel_id, text=constants.NO_FLATS_MESSAGE, disable_notification=True).message_id)

    config['sent_messages'] = messages
    config.sync()


def get_old_and_new_flats(flat_list):

    old_flats = []
    new_flats = []
    saved_flats = config['previous_flats']

    for flat in flat_list:
        if flat.link in saved_flats:
            old_flats.append(flat)
        else:
            new_flats.append(flat)

    config['previous_flats'] = [flat.link for flat in flat_list]
    config.sync()

    return old_flats, new_flats


def init():

    load_dotenv()

    global config
    config = shelve.open('../config')

    schedule.every(13).to(19).minutes.do(update_channel)

    update_channel()

    while True:
        schedule.run_pending()
        sleep(10)

if __name__=='__main__':
    init()
