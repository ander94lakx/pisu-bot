from dotenv import load_dotenv
import logging
import os
import shelve
from shelve import Shelf
from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.ext import Updater
from time import sleep

import constants
from models import Flat
from scrap import scrap_fotocasa, scrap_idealista


# Configuration dict
config: Shelf = None


def send_results(flat_list: list[Flat], update: Update, context: CallbackContext):
    for flat in flat_list:
        context.bot.send_photo(chat_id=update.effective_chat.id, caption=flat.link, photo=flat.inmage)
        sleep(1)


def start(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text=constants.START_MESSAGE)


def bilatu(update: Update, context: CallbackContext):
    scrap(update, context, 'all')


def idealista(update: Update, context: CallbackContext):
    scrap(update, context, 'idealista')


def fotocasa(update: Update, context: CallbackContext):
    scrap(update, context, 'fotocasa')


def gehienekoa(update: Update, context: CallbackContext):
    try:
        config['top_price'] = int(context.args[0])
        config.sync()
        context.bot.send_message(chat_id=update.effective_chat.id, \
            text=f'Gehienekoa aldatuta! Oraingo balioa: {config["top_price"]}')
    except Exception:
        if context.args is not None and len(context.args) > 0 \
            and context.args[0] == 'lehenetsia':
            config['top_price'] = top_price
        context.bot.send_message(chat_id=update.effective_chat.id, \
            text=f'Oraingo balioa: {config["top_price"]}')


def scrap(update: Update, context: CallbackContext, site):
    context.bot.send_message(chat_id=update.effective_chat.id, text=constants.INITIAL_MESSAGE)
    flat_list = []
    if site in { 'idealista', 'all' }:
        flat_list.extend(scrap_idealista(config['top_price']))
    if site in { 'fotocasa', 'all' }:
        flat_list.extend(scrap_fotocasa(config['top_price']))
    send_results(flat_list, update, context)
    context.bot.send_message(chat_id=update.effective_chat.id, text=constants.FINAL_MESSAGE)


def init():

    load_dotenv()

    global config, top_price
    config = shelve.open('../config')
    if not 'top_price' in config:
        config['top_price'] = constants.DEFAULT_TOP_PRICE
    if not 'sent_messages' in config:
        config['sent_messages'] = []
    if not 'previous_flats' in config:
        config['previous_flats'] = []

    token = os.getenv('TOKEN')

    updater = Updater(token=token, use_context=True)
    dispatcher = updater.dispatcher

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('bilatu', bilatu))
    dispatcher.add_handler(CommandHandler('idealista', idealista))
    dispatcher.add_handler(CommandHandler('fotocasa', fotocasa))
    dispatcher.add_handler(CommandHandler('gehienekoa', gehienekoa))

    updater.start_polling()


if __name__=='__main__':
    init()
