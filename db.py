from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, Integer, String

engine = create_engine("sqlite:///./students.db")

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


class StudentDB(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    age = Column(Integer)
    course = Column(String)

    interest_level = Column(Integer, default=3)
    learning_depth = Column(Integer, default=3)


Base.metadata.create_all(engine)


# Automatically add new columns to an existing database
with engine.connect() as connection:

    columns = connection.execute(
        text("PRAGMA table_info(students)")
    ).fetchall()

    column_names = [column[1] for column in columns]

    if "interest_level" not in column_names:
        connection.execute(
            text(
                "ALTER TABLE students "
                "ADD COLUMN interest_level INTEGER DEFAULT 3"
            )
        )

    if "learning_depth" not in column_names:
        connection.execute(
            text(
                "ALTER TABLE students "
                "ADD COLUMN learning_depth INTEGER DEFAULT 3"
            )
        )

    connection.commit()