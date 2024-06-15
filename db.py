from sqlalchemy import create_engine, Column, Integer, DateTime, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base

DATABASE_URL = "sqlite:///job_data.db"
Base = declarative_base()
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True)
    datetime = Column(DateTime, default=func.now())
    vacancy_count = Column(Integer)
    change = Column(Integer)


def create_db():
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    create_db()
