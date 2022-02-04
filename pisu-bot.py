import re
import logging
from time import sleep
from typing import List

from selenium import webdriver

import schedule

import telegram
from telegram import Bot, Update
from telegram.ext import Updater
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler

# Ordered URLs for requests to look for the cheapest prices around my city

IDEALISTA_URL = 'https://www.idealista.com/alquiler-viviendas/vitoria-gasteiz-alava/?ordenado-por=precios-asc'
FOTOCASA_URL = 'https://www.fotocasa.es/es/alquiler/viviendas/vitoria-gasteiz/todas-las-zonas/l?sortType=price&sortOrderDesc=false&latitude=42.8517&longitude=-2.67141&combinedLocationIds=724,18,1,439,0,1059,0,0,0'

top_price = 700

# Scrapping methods

def scrap_idealista(max_price):
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

        if price <= max_price:
            flat_list.append({ 
                'link': link, 
                'price': price,
                'image': item.screenshot_as_png, 
                'image_name': item.id + '.png' 
            })
    
    driver.quit()
    return flat_list


def scrap_fotocasa(max_price):
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

        if price <= max_price:
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


def get_max_price(context: CallbackContext):
    global top_price
    try:
        return int(context.args[0])
    except:
        return top_price
    

# Telegram stuff

def start(update: Update, context: CallbackContext):
    start_msg = ('Kaixo!\n\n'
                'Pisuak bilatzeko /bilatu komandoa erabili, mesedez!\n\n'
                'Zerbitzu bakar bat erabiltezko, hurrengo komandoak dauzkazu:\n\n'
                '    /idealista\n'
                '    /fotocasa\n\n'
                'Komandoak pisua alokatzeko gastatu nahi duzun gehiena onartzen dute, adibidez:\n\n'
                '    /bilatu 650\n\n'
                'Balio lehenetsia 700 euro dira\n\n'
                'Mila esker erabiltzeagatik!')
    context.bot.send_message(chat_id=update.effective_chat.id, text=start_msg)


def bilatu(update: Update, context: CallbackContext):
    scrap(update, context, 'all')


def idealista(update: Update, context: CallbackContext):
    scrap(update, context, 'idealista')


def fotocasa(update: Update, context: CallbackContext):
    scrap(update, context, 'fotocasa')


def scrap(update: Update, context: CallbackContext, site):
    send_initial_message(context, update)
    max_price = get_max_price(context)
    flat_list = []
    if site in { 'idealista', 'all' }:
        flat_list.extend(scrap_idealista(max_price))
    if site in { 'fotocasa', 'all' }:
        flat_list.extend(scrap_fotocasa(max_price))
    send_results(flat_list, update, context)
    send_final_message(context, update)


def send_initial_message(context, update):
    context.bot.send_message(chat_id=update.effective_chat.id, text='Emaidazu minutu bat!')


def send_final_message(context, update):
    context.bot.send_message(chat_id=update.effective_chat.id, text='Hortxe dauzkazu!')


# Scheduled task stuff

def update_channel():
    # Get channel and bot info
    with open('token.txt') as f:
        token = f.read()
    with open('channel_id.txt') as f:
        channel_id = f.read()

    bot = telegram.Bot(token=token)

    # Remove previously sended messages
    stacked_messages = []
    with open('sent_messages.txt', 'r') as f:
        for line in f.readlines():
            stacked_messages.append(int(line))
    while stacked_messages:
        bot.delete_message(chat_id=channel_id, message_id=stacked_messages.pop())

    # Scrap all with the defaul top price
    flat_list = []
    flat_list.extend(scrap_idealista(top_price))
    flat_list.extend(scrap_fotocasa(top_price))

    # Send the messages with the info
    # Saves the message_id of the messages to be able to delete them on the next one
    stacked_messages.append(bot.send_message(chat_id=channel_id, text='Kaixo! Hamen dauzkazu oraintxe bertan dauden pisuak:').message_id)
    for flat in flat_list:
        stacked_messages.append(bot.send_photo(chat_id=channel_id, caption=flat['link'], photo=flat['image']).message_id)
        sleep(1)
    stacked_messages.append(bot.send_message(chat_id=channel_id, text='Hortxe dauzkazu!').message_id)

    with open('sent_messages.txt', 'w') as f:
        for message in stacked_messages:
            f.write(str(message) + '\n')

# Main

def init():
    with open('token.txt') as f:
        token = f.read()

    updater = Updater(token=token, use_context=True)
    dispatcher = updater.dispatcher

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('bilatu', bilatu))
    dispatcher.add_handler(CommandHandler('idealista', idealista))
    dispatcher.add_handler(CommandHandler('fotocasa', fotocasa))

    updater.start_polling()

    schedule.every().hour.at(":00").do(update_channel)

    while True:
        schedule.run_pending()
        sleep(1) 

if __name__=='__main__':
    init()