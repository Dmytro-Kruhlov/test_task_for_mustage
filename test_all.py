from unittest.mock import MagicMock

import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import session

from bot import get_today_data, generate_report
from db import Base, Job, Session
from parser import get_last_vacancy_count, save_job_count, job, fetch_job_count


@pytest.fixture(scope="module")
def setup_test_db():
    engine = create_engine("sqlite:///:memory:")
    Session.configure(bind=engine)
    Base.metadata.create_all(engine)
    yield Session
    session.close_all_sessions()
    Base.metadata.drop_all(engine)


def test_create_db(setup_test_db):
    with setup_test_db() as s:
        jobs = s.query(Job).all()
        assert jobs == []


def test_insert_job(setup_test_db):
    with setup_test_db() as s:
        new_job = Job(vacancy_count=10, change=0)
        s.add(new_job)
        s.commit()

        job_from_db = s.query(Job).first()
        assert job_from_db.vacancy_count == 10
        assert job_from_db.change == 0


def test_get_last_vacancy_count_no_records(setup_test_db):
    with setup_test_db() as s:
        s.query(Job).delete()
        s.commit()

        result = get_last_vacancy_count()
        assert result is None


def test_get_last_vacancy_count_with_records(setup_test_db):
    with setup_test_db() as s:
        new_job = Job(vacancy_count=5, change=0)
        s.add(new_job)
        s.commit()

        result = get_last_vacancy_count()
        assert result == 5


def test_save_job_count_no_previous_records(setup_test_db):
    with setup_test_db() as s:
        s.query(Job).delete()
        s.commit()

    save_job_count(10)

    with setup_test_db() as s:
        jobs = s.query(Job).all()
        assert len(jobs) == 1
        assert jobs[0].vacancy_count == 10
        assert jobs[0].change == 0


def test_save_job_count_with_previous_records(setup_test_db):
    with setup_test_db() as s:
        s.query(Job).delete()
        new_job = Job(vacancy_count=5, change=0)
        s.add(new_job)
        s.commit()

    save_job_count(15)

    with setup_test_db() as s:
        jobs = s.query(Job).all()
        assert len(jobs) == 2
        assert jobs[-1].vacancy_count == 15
        assert jobs[-1].change == 10


@pytest.mark.asyncio
async def test_job(mocker, setup_test_db):
    mocker.patch("parser.fetch_job_count", return_value=10)

    await job()

    with setup_test_db() as s:
        jobs = s.query(Job).all()
        assert len(jobs) == 3
        assert jobs[-1].vacancy_count == 10
        assert jobs[-1].change == 5


def test_fetch_job_count(mocker):
    mock_driver = MagicMock()
    mock_webdriver = mocker.patch("parser.webdriver.Chrome", autospec=True)
    mock_webdriver.return_value.__enter__.return_value = mock_driver
    mock_driver.page_source = (
        '<div class="santa-typo-h2 santa-mr-10">123 вакансій</div>'
    )
    result = fetch_job_count()
    assert result == 123


def test_get_today_data(setup_test_db):

    results = get_today_data()
    assert len(results) == 3
    assert results[-1].vacancy_count == 10
    assert results[-1].change == 5


@pytest.mark.asyncio
async def test_generate_report(mocker, setup_test_db):
    mock_xlsxwriter = mocker.patch("bot.xlsxwriter.Workbook", autospec=True)
    mock_workbook = mock_xlsxwriter.return_value
    mock_worksheet = mock_workbook.add_worksheet.return_value

    file_path = await generate_report()
    assert file_path is not None

    mock_xlsxwriter.assert_called_once()
    mock_workbook.add_worksheet.assert_called_once_with("statistic")
    mock_workbook.add_format.assert_called_once_with({"num_format": "yyyy-mm-dd hh:mm"})
    mock_worksheet.write_row.assert_called_once_with(
        0, 0, ["datetime", "vacancy_count", "change"]
    )
    assert mock_worksheet.write_datetime.call_count == 3
    assert mock_worksheet.write_number.call_count == 6
