import re
import requests
import phonenumbers
import psycopg2
import schedule
import time
import os
import subprocess

from bs4 import BeautifulSoup
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

start_url = "https://auto.ria.com/uk/car/used/"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                  ' AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'
        }
host = "psql"     # for local use "localhost"
database = "cars_db"
user = "postgres"
password = "11111"


def write_to_database(car_data):
    """
    Write car data to PostgreSQL database

    """

    connection = None
    try:
        connection = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password
        )

        cursor = connection.cursor()
        create_table_query = '''
                CREATE TABLE IF NOT EXISTS cars (
                    id SERIAL PRIMARY KEY,
                    url VARCHAR,
                    title VARCHAR,
                    price_usd DECIMAL,
                    odometer INT,
                    username VARCHAR,
                    phone_number VARCHAR,
                    image_url VARCHAR,
                    images_count INT,
                    car_number VARCHAR,
                    car_vin VARCHAR,
                    datetime_found TIMESTAMP
                );
            '''
        cursor.execute(create_table_query)
        connection.commit()

        sql_query = """
            INSERT INTO cars (title, url, price_usd, odometer, username, phone_number, image_url, 
                              images_count, car_number, car_vin, datetime_found)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(sql_query, (
            car_data['title'], car_data['url'], car_data['price_usd'], car_data['odometer'],
            car_data['username'], car_data['phone_number'], car_data['image_url'],
            car_data['images_count'], car_data['car_number'], car_data['car_vin'],
            car_data['datetime_found']
        ))

        connection.commit()

    except (Exception, psycopg2.Error) as error:
        print("Error PostgreSQL:", error)
    finally:
        # Закрытие соединения
        if connection:
            cursor.close()
            connection.close()


def get_pages_count(url: str, headers: dict) -> int:
    """
    Get number of pages
    :param headers:
    :param url: start page in auto.ria.com, example: https://auto.ria.com/uk/car/used/
    :return: number of pages
    """

    url = url + "?page=1"
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    pages = soup.find('span', class_='page-item dhide text-c').text.strip()[4:]
    pages = int(pages.replace(' ', ''))
    return pages


def get_url_car(url: str, headers: dict) -> str:
    """
    Get url car
    :param headers:
    :param url: start page in auto.ria.com, example: https://auto.ria.com/uk/car/used/
    :return: url car
    """

    pages = get_pages_count(url, headers)

    for page in range(1, pages + 1):
        response = requests.get(url + f"?page={page}", headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('div', class_='content-bar'):
            url_car = link.find('a', class_='m-link-ticket').get('href')
            yield url_car


def get_phone_number(url: str):
    """
    Get phone number
    :param url: car url
    :return: phone number
    """

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=options)
    driver.get(url)
    time.sleep(3)
    phone_button = driver.find_element(By.ID, 'openPopupCommentSeller')
    driver.execute_script("arguments[0].scrollIntoView(true);", phone_button)

    WebDriverWait(driver, 10).until(EC.visibility_of(phone_button))

    phone_button.click()

    phone_number_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'popup-successful-call-desk'))
    )

    phone_number = phone_number_element.text.strip()
    # parsed_phone_number = phonenumbers.parse(phone_number, "UA")
    # formatted_phone_number = (phonenumbers.format_number(parsed_phone_number,
    #                           phonenumbers.PhoneNumberFormat.INTERNATIONAL)).replace(" ", "")
    return phone_number


def get_data_car(url: str, headers: dict):
    """
    Get data car
    :param url: url car, example: https://auto.ria.com/uk/auto_nissan_patrol_35554720.html
    :return: data car
    """

    for link in get_url_car(url, headers):
        response = requests.get(link, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        if soup.find('div', class_='notice_head'):
            continue
        url = link
        if soup.find('h3', class_='auto-content_title'):
            title = soup.find('h3', class_='auto-content_title').text.strip()
        else:
            title = "Empty"
        if soup.find('strong', class_=''):
            price_usd = int(soup.find('strong', class_='').text.strip().replace(' ', '').replace('$', ''))
        else:
            price_usd = "Empty"
        if soup.find('div', class_='bold dhide'):
            odometer = int("".join(re.findall(r'\d+', soup.find('div', class_='bold dhide').text))) * 1000
        else:
            odometer = "Empty"
        if soup.find('div', class_='seller_info_name bold'):
            username = soup.find('div', class_='seller_info_name bold').text.strip()
        else:
            username = "Empty"
        phone_number = get_phone_number(link)
        if soup.find('img', class_='outline m-auto'):
            image_url = soup.find('img', class_='outline m-auto').get('src')
        else:
            image_url = "Empty"
        if soup.find('a', class_='show-all link-dotted'):
            images_count = int("".join(re.findall(r'\d+', soup.find('a', class_='show-all link-dotted').text)))
        else:
            images_count = "Empty"
        if soup.find('span', class_='state-num ua'):
            car_number = soup.find('span', class_='state-num ua').contents[0].text.strip()
        else:
            car_number = "Empty"
        if soup.find('span', class_='label-vin'):
            car_vin = soup.find('span', class_='label-vin').text.strip()
        else:
            car_vin = "Empty"
        datetime_found = datetime.now().date().strftime("%Y-%m-%d")
        car_data = {
            'title': title,
            'url': url,
            'price_usd': price_usd,
            'odometer': odometer,
            'username': username,
            'phone_number': phone_number,
            'image_url': image_url,
            'images_count': images_count,
            'car_number': car_number,
            'car_vin': car_vin,
            'datetime_found': datetime_found
        }
        print(car_data)
        write_to_database(car_data)


def create_database_dump(db_name, db_user, db_password, dump_folder="dumps"):
    """
    Create database dump
    :param db_name: name database
    :param db_user: user database
    :param db_password: password database
    :param dump_folder: folder to save dump
    """

    if not os.path.exists(dump_folder):
        os.makedirs(dump_folder)

    current_date = datetime.now().strftime("%Y-%m-%d")
    dump_file_path = os.path.join(dump_folder, f"{db_name}_dump_{current_date}.sql")

    dump_command = [
        "pg_dump",
        f"--dbname=postgresql://{db_user}:{db_password}@{host}:5432/{db_name}",
        f"--file={dump_file_path}",
    ]

    try:
        subprocess.run(dump_command, check=True)
        print(f"Database dump created successfully: {dump_file_path}")

        # # Clear database
        # with psycopg2.connect(
        #         host="localhost",
        #         database=db_name,
        #         user=db_user,
        #         password=db_password
        # ) as connection:
        #     with connection.cursor() as cursor:
        #         cursor.execute("TRUNCATE TABLE cars RESTART IDENTITY;")
        #         connection.commit()
    except subprocess.CalledProcessError as e:
        print(f"Error creating database dump: {e}")
    except psycopg2.Error as e:
        print(f"Error clearing database: {e}")


def get_data_job():
    print("Job started")
    create_database_dump(database, user, password)
    get_data_car(start_url, headers)


schedule.every().day.at('22:00').do(get_data_job)

while True:
    schedule.run_pending()
