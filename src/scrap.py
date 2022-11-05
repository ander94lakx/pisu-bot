import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from time import sleep

from constants import IDEALISTA_URL, FOTOCASA_URL
from models import Flat


def scrap_idealista(top_price: int):
    driver = initialize_driver(IDEALISTA_URL)
    scroll_down_and_up(driver)

    # Be kind and accept the cookies
    try:
        driver.find_element(By.ID, 'didomi-notice-agree-button').click()
    except Exception:
        pass # No cookies button, no problem!

    # Find each flat element

    element = driver.find_element(By.XPATH, '//*[@id="main-content"]')
    items = element.find_elements(By.CLASS_NAME, 'item-multimedia-container')

    flat_list = []

    for item in items:
        # Get the link for that flat
        link = item.find_element(By.XPATH, './div/a[@href]')
        link = link.get_attribute('href')

        # Get the price for that flat
        result = re.search('.*\\n(.*)€\/mes', item.text)
        price_str = result.group(1).replace('.', '')
        price = int(price_str)

        if price <= top_price:
            flat_list.append(Flat(link, price, item.screenshot_as_png))

    driver.quit()
    return flat_list


def scrap_fotocasa(top_price: int):
    driver = initialize_driver(FOTOCASA_URL)
    scroll_down_and_up(driver)

    # Be kind and accept the cookies
    try:
        elem = driver.find_element(By.XPATH, '//button[@data-testid="TcfAccept"]')
        elem.click()
    except Exception:
        pass # No cookies button, no problem!

    # Find each flat element
    element = driver.find_element(By.CLASS_NAME, 're-SearchResult')
    items = element.find_elements(By.CLASS_NAME, 're-CardPackMinimal')

    flat_list = []

    for item in items:
        # Get the link for that flat
        link = item.find_element(By.XPATH, './a[@href]')
        link = link.get_attribute('href')

        # Get the price for that flat
        result = re.search('.*\\n(.*) € \/mes', item.text)
        price_str = result.group(1).replace('.', '')
        price = int(price_str)

        if price <= top_price:
            flat_list.append(Flat(link, price, item.screenshot_as_png))

    driver.quit()
    return flat_list

# Scrapping utils

def initialize_driver(url):
    chrome_options = webdriver.ChromeOptions()

    # Options to try to avoid annoying anti-scrapping techniques
    # Removes navigator.webdriver flag
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    # Standard User-Agent
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 13_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36")

    # Headless mode
    chrome_options.add_argument("--headless")

    driver = webdriver.Chrome(executable_path='./chromedriver.exe', options=chrome_options)
    driver.get(url)
    sleep(4)
    driver.set_window_position(0,0)
    driver.set_window_size(1920, 1080)

    return driver


def scroll_down_and_up(driver):
    driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
    sleep(2)
    driver.execute_script('window.scrollTo(0, 0);')


if __name__=='__main__':
    flats: Flat = scrap_idealista(700)
    for flat in flats:
        print(f'FLAT ({flat.price} euros): {flat.link}')
