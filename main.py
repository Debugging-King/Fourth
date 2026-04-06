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


def main():
    driver = get_driver('https://secure.fourth.com/fmplogin?brand=GLH')
    login(driver, 'enter username', 'enter password')
    navigate_to_schedule(driver)
    session = load_cookies(driver)
    driver.quit()
    api = 'https://api.fourth.com/api/myschedules/schedule?&%24orderby=StartDateTime+asc&%24top=100&fromDate=2026%2F04%2F07&toDate=2026%2F04%2F19'
    response = session.get(api)
    save_data(response)


    date = get_date()
    save_to_calendar(date)



def get_driver(link):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    service = Service()
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(link)
    return driver

def login(driver, username, password):
    wait = WebDriverWait(driver, 10)

    username = wait.until(EC.presence_of_element_located((By.ID, 'j_id0:j_id2:j_id15:username')))
    username.send_keys(username)

    password = wait.until(EC.presence_of_element_located((By.NAME, 'j_id0:j_id2:j_id15:j_id24')))
    password.send_keys(password)

    button = driver.find_element(By.ID, 'j_id0:j_id2:j_id15:submit')
    button.click()

def navigate_to_schedule(driver):
    wait = WebDriverWait(driver, 10)
    wait.until(EC.url_contains('feed'))
    driver.get('https://api.fourth.com/myschedules/#/my-schedule?activeTab=all')

def load_cookies(driver):
    cookies = driver.get_cookies()
    print("Cookies grabbed:", [c['name'] for c in cookies])

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
    cal.add('Version', '2.0')

    for day in date:
        event = Event()
        event.add('summary', "Work")
        event.add('dtstart', day.get('startDateTime'))
        event.add('dtend', day.get('endDateTime'))
        event.add('uid', str(uuid.uuid4()))

        cal.add_component(event)



    with open('schedule.ics', 'wb') as f:
        f.write(cal.to_ical())




main()