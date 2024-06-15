import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from db import create_db
from parser import job
from bot import dp, bot


async def main():
    create_db()
    scheduler = AsyncIOScheduler()
    await job()
    scheduler.add_job(job, "interval", hours=1)
    scheduler.start()

    print("Starting bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
