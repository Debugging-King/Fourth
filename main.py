import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import json
import datetime
from icalendar import Calendar, Event
import uuid
from zoneinfo import ZoneInfo
import dropbox
from dotenv import load_dotenv
import os
import logging


def main():

    load_dotenv()
    required_vars = ['USERNAME', 'PASSWORD', 'DROPBOX_TOKEN']
    for var in required_vars:
        if not os.environ.get(var):
            raise ValueError(f"Missing environment variable: {var}")

    driver = get_driver('https://secure.fourth.com/fmplogin?brand=GLH')
    try:
        login(driver, os.environ.get('USERNAME'), os.environ.get('PASSWORD'))
        navigate_to_schedule(driver)
        session = load_cookies(driver)
    except Exception:
        print("Selenium error")
    finally:
        driver.quit()


    api = get_api()

    response = session.get(api)
    response.raise_for_status()

    save_data(response)


    date = get_date()
    save_to_calendar(date)
    upload_to_icloud('schedule.ics')

    upload_to_dropbox(
        local_path='schedule.ics',
        dropbox_path='/Apps/FourthCalendar/schedule.ics',
    )

def get_driver(link):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    service = Service()
    driver = webdriver.Chrome(service=service)
    driver.get(link)
    return driver

def login(driver, username, password):
    wait = WebDriverWait(driver, 10)
    username_textbox = wait.until(EC.presence_of_element_located((By.ID, 'j_id0:j_id2:j_id15:username')))
    username_textbox.send_keys(username)

    password_textbox = wait.until(EC.presence_of_element_located((By.NAME, 'j_id0:j_id2:j_id15:j_id24')))
    password_textbox.send_keys(password)


    button = driver.find_element(By.ID, 'j_id0:j_id2:j_id15:submit')
    button.click()

def navigate_to_schedule(driver):
    wait = WebDriverWait(driver, 10)
    wait.until(EC.url_contains('feed'))
    driver.get('https://api.fourth.com/myschedules/#/my-schedule?activeTab=all')

def load_cookies(driver):
    cookies = driver.get_cookies()
    session = requests.Session()
    for cookie in cookies:
        session.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])

    return session

def save_data(response):
    data = response.json()
    json_string = json.dumps(data, indent = 4)
    with open('schedule.json', 'w') as f:
        f.write(json_string)

def get_date():
    date_str = []
    date = []
    uk_tz = ZoneInfo('Europe/London')

    with open('schedule.json', 'r') as file:
        schedule = json.load(file)

    for f in schedule.get('entities'):
        temp = {}
        temp['startDateTime'] = f.get('properties').get('startDateTime')
        temp['endDateTime'] = f.get('properties').get('endDateTime')
        date_str.append(temp)

    for i in date_str:
        temp = {}
        temp['startDateTime'] = datetime.datetime.fromisoformat(i.get('startDateTime')).replace(tzinfo=uk_tz)
        temp['endDateTime'] = datetime.datetime.fromisoformat(i.get('endDateTime')).replace(tzinfo=uk_tz)
        date.append(temp)

    return date

def save_to_calendar(date):
    cal = Calendar()
    cal.add('prodid', '-//My Work Schedule//EN')
    cal.add('version', '2.0')

    for day in date:
        event = Event()
        event.add('summary', "Work")
        event.add('dtstart', day.get('startDateTime'))
        event.add('dtend', day.get('endDateTime'))
        event.add('uid', str(uuid.uuid4()))

        cal.add_component(event)

    with open('schedule.ics', 'wb') as f:
        f.write(cal.to_ical())

def upload_to_icloud(local_path):
    path = '/Users/noah/Library/Mobile Documents/com~apple~CloudDocs/schedule.ics'

    with open(local_path, 'rb') as local, open(path, 'wb') as f:
        f.write(local.read())

def upload_to_dropbox(local_path, dropbox_path):
    token_url = "https://api.dropbox.com/oauth2/token"
    token_data = {
        "grant_type": "refresh_token",
        "refresh_token": os.environ.get('REFRESH_TOKEN'),
        "client_id": os.environ.get('APP_KEY'),
        "client_secret": os.environ.get('APP_SECRET'),
    }

    r = requests.post(token_url, data=token_data)
    access_token = r.json()['access_token']

    upload_url = "https://content.dropboxapi.com/2/files/upload"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Dropbox-API-Arg": json.dumps({
            "path": dropbox_path,
            "mode": "overwrite",
            "autorename": True,
            "mute": False
        }),
        "Content-Type": "application/octet-stream"
    }


    with open(local_path, "rb") as f:
        response = requests.post(upload_url, headers=headers, data=f)

def get_api():
    from_date = datetime.datetime.now()
    from_year = from_date.year
    from_month = from_date.strftime('%m')
    from_day = from_date.strftime('%d')
    to_date = datetime.timedelta(21) + from_date
    to_year = to_date.year
    to_month = to_date.strftime('%m')
    to_day = to_date.strftime('%d')
    api = f'https://api.fourth.com/api/myschedules/schedule?&%24orderby=StartDateTime+asc&%24top=100&fromDate={from_year}%2F{from_month}%2F{from_day}&toDate={to_year}%2F{to_month}%2F{to_day}'
    return api

date_now = datetime.datetime.now()
file_date = datetime.datetime.fromtimestamp(os.path.getmtime('schedule.ics'))

if (date_now.day - file_date.day > 3):
    main()