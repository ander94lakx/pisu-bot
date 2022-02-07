from dotenv import load_dotenv
import logging
import os
import re
import schedule
from selenium import webdriver
import shelve
from shelve import Shelf
import telegram
from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.ext import Updater
from time import sleep


# Ordered URLs for requests to look for the cheapest prices around my city
IDEALISTA_URL = 'https://www.idealista.com/alquiler-viviendas/vitoria-gasteiz-alava/?ordenado-por=precios-asc'
FOTOCASA_URL = 'https://www.fotocasa.es/es/alquiler/viviendas/vitoria-gasteiz/todas-las-zonas/l?sortType=price&sortOrderDesc=false&latitude=42.8517&longitude=-2.67141&combinedLocationIds=724,18,1,439,0,1059,0,0,0'

# Default top price for channel messages and when no prices is specified
top_price = 700

# Messages
INITIAL_MESSAGE = 'Emaidazu minutu bat!'
INITIAL_AUTO_MESSAGE = 'Kaixo! Hamen dauzkazu oraintxe bertan dauden pisuak:'
FINAL_MESSAGE = 'Hortxe dauzkazu!'
START_MESSAGE = ('Kaixo!\n\n'
                 'Pisuak bilatzeko /bilatu komandoa erabili, mesedez!\n\n'
                 'Zerbitzu bakar bat erabiltezko, hurrengo komandoak dauzkazu:\n\n'
                 '    /idealista\n'
                 '    /fotocasa\n\n'
                 'Komandoak pisua alokatzeko gastatu nahi duzun gehiena onartzen dute, adibidez:\n\n'
                 '    /bilatu [euro]\n\n'
                 'Balio lehenetsia aldatzeko edo ikusteko, erabili hurrengo komandoa:\n\n'
                 '    /gehienekoa [euro]\n\n'
                 'Mila esker erabiltzeagatik!')

# Configuration dict
config: Shelf = None


# Scrapping methods

def scrap_idealista():
    driver = initialize_driver(IDEALISTA_URL)
    scroll_down_and_up(driver)

    # Be kind and accept the cookies
    try:
        driver.find_element_by_id('didomi-notice-agree-button').click()
    except:
        pass # No cookies button, no problem!

    # Find each flat element
    elements = driver.find_element_by_xpath('//*[@id="main-content"]')
    items = elements.find_elements_by_class_name('item-multimedia-container')

    flat_list = []

    for item in items:
        # Get the link for that flat
        link = item.find_element_by_xpath('./div/a[@href]')
        link = link.get_attribute('href')

        # Get the price for that flat
        result = re.search('.*\\n(.*)€\/mes', item.text)
        price_str = result.group(1).replace('.', '')
        price = int(price_str)

        if price <= config['top_price']:
            flat_list.append({ 
                'link': link, 
                'price': price,
                'image': item.screenshot_as_png, 
                'image_name': item.id + '.png' 
            })
    
    driver.quit()
    return flat_list


def scrap_fotocasa():
    driver = initialize_driver(FOTOCASA_URL)
    scroll_down_and_up(driver)

    # Be kind and accept the cookies
    try:
        elem = driver.find_element_by_xpath('//button[@data-testid="TcfAccept"]')
        elem.click()
    except:
        pass # No cookies button, no problem!

    # Find each flat element
    elements = driver.find_element_by_class_name('re-SearchResult')
    items = elements.find_elements_by_class_name('re-CardPackMinimal')

    flat_list = []

    for item in items:
        # Get the link for that flat
        link = item.find_element_by_xpath('./a[@href]')
        link = link.get_attribute('href')

        # Get the price for that flat
        result = re.search('.*\\n(.*) € \/mes', item.text)
        price_str = result.group(1).replace('.', '')
        price = int(price_str)

        if price <= config['top_price']:
            flat_list.append({ 
                'link': link, 
                'price': price,
                'image': item.screenshot_as_png
            })
    
    driver.quit()
    return flat_list


def send_results(flat_list: list, update: Update, context: CallbackContext):
    for flat in flat_list:
        context.bot.send_photo(chat_id=update.effective_chat.id, caption=flat['link'], photo=flat['image'])
        sleep(1)


# Scrapping utils

def initialize_driver(url):
    driver = webdriver.Chrome(executable_path='./chromedriver.exe')
    driver.get(url)
    sleep(2)
    driver.set_window_position(0,0)
    driver.set_window_size(1920, 1080)
    return driver


def scroll_down_and_up(driver):
    driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
    sleep(2)
    driver.execute_script('window.scrollTo(0, 0);')
   

# Telegram stuff

def start(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text=START_MESSAGE)


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
            text='Gehienekoa aldatuta! Oraingo balioa: '+config['top_price'])
    except:
        if context.args is not None and len(context.args) > 0 \
            and context.args[0] == 'lehenetsia':
            config['top_price'] = top_price
        context.bot.send_message(chat_id=update.effective_chat.id, \
            text=f'Oraingo balioa: {config["top_price"]}')
    
    
def scrap(update: Update, context: CallbackContext, site):
    context.bot.send_message(chat_id=update.effective_chat.id, text=INITIAL_MESSAGE)
    flat_list = []
    if site in { 'idealista', 'all' }:
        flat_list.extend(scrap_idealista())
    if site in { 'fotocasa', 'all' }:
        flat_list.extend(scrap_fotocasa())
    send_results(flat_list, update, context)
    context.bot.send_message(chat_id=update.effective_chat.id, text=FINAL_MESSAGE)


# Scheduled task stuff

def update_channel():
    # Get channel and bot info
    token = os.getenv('TOKEN')
    channel_id = os.getenv('CHANNEL_ID')

    bot = telegram.Bot(token=token)

    # Remove previously sended messages
    messages = config['sent_messages']
    while messages:
        try:
            bot.delete_message(chat_id=channel_id, message_id=messages.pop())
        except Exception as e: print(e)
    del config['sent_messages']
    config.sync()

    # Scrap all with the defaul top price
    flat_list = []
    flat_list.extend(scrap_idealista())
    flat_list.extend(scrap_fotocasa())

    # Send the messages with the info
    # Saves the message_id of the messages to be able to delete them on the next one
    messages.append(bot.send_message(chat_id=channel_id, text=INITIAL_AUTO_MESSAGE, disable_notification=True).message_id)
    for flat in flat_list:
        messages.append(bot.send_photo(chat_id=channel_id, caption=flat['link'], photo=flat['image'], disable_notification=True).message_id)
        sleep(1)
    messages.append(bot.send_message(chat_id=channel_id, text=FINAL_MESSAGE, disable_notification=True).message_id)

    config['sent_messages'] = messages
    config.sync()



# Main

def init():

    load_dotenv()

    global config, top_price
    config = shelve.open('config')
    if not 'top_price' in config:
        config['top_price'] = top_price
    if not 'sent_messages' in config:
        config['sent_messages'] = []


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

    schedule.every().day.at("09:00").do(update_channel)
    schedule.every().day.at("11:00").do(update_channel)
    schedule.every().day.at("13:00").do(update_channel)
    schedule.every().day.at("15:00").do(update_channel)
    schedule.every().day.at("17:00").do(update_channel)
    schedule.every().day.at("19:00").do(update_channel)
    schedule.every().day.at("21:00").do(update_channel)
    schedule.every().day.at("23:00").do(update_channel)

    update_channel()

    while True:
        schedule.run_pending()
        sleep(1) 

if __name__=='__main__':
    init()