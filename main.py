from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()
class Student(BaseModel):
    name: str
    age: int
    course: str
@app.get("/")
def home():
    return {"message": "Student Management System is running!"}
@app.post("/students")
def add_student(student: Student):
    return student