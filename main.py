from pydantic import BaseModel, ConfigDict, Field
from fastapi import FastAPI, HTTPException

from db import SessionLocal, StudentDB

app = FastAPI()


@app.get("/")
def home():
    return {"message": "Student management is running"}


class Student(BaseModel):
    name: str
    age: int
    course: str

    interest_level: int = Field(default=3, ge=1, le=5)
    learning_depth: int = Field(default=3, ge=1, le=5)

    model_config = ConfigDict(from_attributes=True)


# CREATE STUDENT
@app.post("/students")
def add_student(student: Student):

    db = SessionLocal()

    new_student = StudentDB(
        name=student.name,
        age=student.age,
        course=student.course,
        interest_level=student.interest_level,
        learning_depth=student.learning_depth
    )

    db.add(new_student)
    db.commit()
    db.refresh(new_student)

    db.close()

    return new_student


# GET ALL STUDENTS
@app.get("/students")
def get_students():

    db = SessionLocal()

    students = db.query(StudentDB).all()

    db.close()

    return students


# GET ONE STUDENT
@app.get("/students/{student_id}")
def get_student(student_id: int):

    db = SessionLocal()

    student = db.query(StudentDB).filter(
        StudentDB.id == student_id
    ).first()

    if student is None:
        db.close()
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    db.close()

    return student


# UPDATE STUDENT
@app.put("/students/{student_id}")
def update_student(student_id: int, student: Student):

    db = SessionLocal()

    existing_student = db.query(StudentDB).filter(
        StudentDB.id == student_id
    ).first()

    if existing_student is None:
        db.close()
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    existing_student.name = student.name
    existing_student.age = student.age
    existing_student.course = student.course
    existing_student.interest_level = student.interest_level
    existing_student.learning_depth = student.learning_depth

    db.commit()
    db.refresh(existing_student)

    db.close()

    return existing_student


# DELETE STUDENT
@app.delete("/students/{student_id}")
def delete_student(student_id: int):

    db = SessionLocal()

    student = db.query(StudentDB).filter(
        StudentDB.id == student_id
    ).first()

    if student is None:
        db.close()
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    db.delete(student)
    db.commit()

    db.close()

    return {"message": "Student deleted successfully"}