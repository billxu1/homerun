import undetected_chromedriver as uc
from selenium import webdriver
import pytz
import re
timezone = pytz.timezone('Australia/Sydney')

def set_up_driver(headless=True):
    if not headless:
        return uc.Chrome()

    cho = webdriver.ChromeOptions()
    cho.headless = True
    cho.add_argument("--disable-dev-shm-usage")
    cho.add_argument("disable-infobars")
    cho.add_argument("--disable-extensions")
    cho.add_argument("--no-sandbox")
    return uc.Chrome(options=cho)

def safe_find_element(parent, by, value, attribute=None, remove_text=None):
    try:
        element = parent.find_element(by, value)
        text = element.get_attribute(attribute) if attribute else element.text
        return re.sub(remove_text, '', text) if remove_text else text
    except Exception:
        return None