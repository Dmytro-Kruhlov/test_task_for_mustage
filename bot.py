import xlsxwriter
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile

from config import settings
from db import Session, Job
from datetime import datetime


bot = Bot(token=settings.BOT_TOKEN.get_secret_value())
dp = Dispatcher()


def get_today_data():
    with Session() as session:
        today_date = datetime.now().date()
        results = session.query(Job).filter(Job.datetime >= today_date).all()
        return results


async def generate_report():
    data = get_today_data()
    if data:
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M")
        file_path = f"today_statistic_at_{current_time}.xlsx"
        workbook = xlsxwriter.Workbook(file_path)
        worksheet = workbook.add_worksheet("statistic")
        date_format = workbook.add_format({"num_format": "yyyy-mm-dd hh:mm"})
        worksheet.write_row(0, 0, ["datetime", "vacancy_count", "change"])

        row = 1
        for job in data:
            formatted_datetime = job.datetime.replace(second=0, microsecond=0)
            worksheet.write_datetime(row, 0, formatted_datetime, date_format)
            worksheet.write_number(row, 1, job.vacancy_count)
            worksheet.write_number(row, 2, job.change)
            row += 1

        workbook.close()
        return file_path
    else:
        return None


@dp.message(Command("get_today_statistic"))
async def send_today_statistic(message: types.Message):
    file_path = await generate_report()
    if file_path:
        excel_document = FSInputFile(file_path)
        await message.answer_document(excel_document)
    else:
        await message.answer("No data for today.")
