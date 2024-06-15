import time
from bs4 import BeautifulSoup
from datetime import datetime
from db import Session, Job
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def fetch_job_count():
    url = "https://robota.ua/zapros/junior/ukraine"
    service = Service(ChromeDriverManager().install())
    with webdriver.Chrome(service=service) as driver:
        driver.get(url)
        time.sleep(5)
        try:
            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")
            count_element = soup.find("div", {"class": "santa-typo-h2 santa-mr-10"})
            if count_element:
                vacancy_text = ''.join(filter(str.isdigit, count_element.text))
                vacancy_count = int(vacancy_text)
            else:
                vacancy_count = 0
            print(vacancy_count)
            return vacancy_count
        except Exception as e:
            return f"Error scraping product data from {url}: {e}"


def get_last_vacancy_count():
    with Session() as session:
        last_job = session.query(Job).order_by(Job.datetime.desc()).first()
        if last_job:
            return last_job.vacancy_count
        return None


def save_job_count(vacancy_count):
    with Session() as session:
        last_vacancy_count = get_last_vacancy_count()
        change = vacancy_count - last_vacancy_count if last_vacancy_count else 0
        new_job = Job(vacancy_count=vacancy_count, change=change)
        session.add(new_job)
        session.commit()


async def job():
    vacancy_count = fetch_job_count()
    save_job_count(vacancy_count)
    print(f"Saved {vacancy_count} vacancies at {datetime.now()}")
