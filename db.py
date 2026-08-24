from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base

Base = declarative_base()

DATABASE_URL = "sqlite:///./students.db"

engine = create_engine(DATABASE_URL)


class StudentDB(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    age = Column(Integer)
    course = Column(String)


Base.metadata.create_all(engine)
