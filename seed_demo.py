"""Seed an idempotent demo learner profile for the hackathon walkthrough."""

import os
from datetime import datetime, timezone

from sqlalchemy import select

from backend.database import SessionLocal, StudentProgress, StudentProfile, Subject, User, UserRole
from backend.security import hash_password


DEMO_EMAIL = "demo@adhyan.com"
DEMO_PASSWORD = "DemoPassword123!"

SUBJECTS = {
    "Python": (75.0, 82.0, 40),
    "Java": (55.0, 68.0, 30),
    "C Programming": (88.0, 91.0, 55),
    "Data Structures": (42.0, 61.0, 20),
    "Machine Learning": (35.0, 58.0, 15),
    "SQL": (65.0, 74.0, 28),
}

SUBJECT_DESCRIPTIONS = {
    "Python": "Adaptive Python learning path covering syntax, data structures, and OOP.",
    "Java": "Adaptive Java learning path covering core language, collections, and concurrency.",
    "C Programming": "Adaptive C learning path covering memory safety, pointers, and systems programming.",
    "Data Structures": "Adaptive Data Structures path covering arrays, trees, graphs, and algorithms.",
    "Machine Learning": "Adaptive Machine Learning path covering fundamentals, models, and evaluation.",
    "SQL": "Adaptive SQL path covering queries, joins, indexes, and transactions.",
}


def seed_demo() -> None:
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == DEMO_EMAIL))
        if user is None:
            user = User(
                email=DEMO_EMAIL,
                password_hash=hash_password(DEMO_PASSWORD),
                name="Adhyan Demo Student",
                role=UserRole.TRAINEE,
            )
            db.add(user)
            db.flush()

        profile = db.scalar(
            select(StudentProfile).where(StudentProfile.user_id == user.id)
        )
        if profile is None:
            profile = StudentProfile(
                user=user,
                course="AI-Powered Computer Science",
                age=20,
                interest_level=4,
                learning_depth=4,
                current_streak=12,
            )
            db.add(profile)
            db.flush()

        for name, values in SUBJECTS.items():
            subject = db.scalar(select(Subject).where(Subject.name == name))
            if subject is None:
                subject = Subject(
                    name=name,
                    description=SUBJECT_DESCRIPTIONS.get(name, f"Adaptive {name} learning path powered by Adhyan DQN."),
                )
                db.add(subject)
                db.flush()

            progress = db.scalar(
                select(StudentProgress).where(
                    StudentProgress.student_id == profile.id,
                    StudentProgress.subject_id == subject.id,
                )
            )
            progress_values = {
                "progress": values[0],
                "average_score": values[1],
                "questions_solved": values[2],
                "last_activity": datetime.now(timezone.utc),
            }
            if progress is None:
                db.add(
                    StudentProgress(
                        student=profile,
                        subject=subject,
                        **progress_values,
                    )
                )
            else:
                for key, value in progress_values.items():
                    setattr(progress, key, value)

        db.commit()
        print(
            f"Seeded {DEMO_EMAIL} with Python, Java, C Programming, Data Structures, Machine Learning, and SQL progress data."
        )


if __name__ == "__main__":
    if not os.getenv("DATABASE_URL"):
        raise RuntimeError("DATABASE_URL must be set before seeding the demo.")
    if not os.getenv("SECRET_KEY"):
        raise RuntimeError("SECRET_KEY must be set before seeding the demo.")
    seed_demo()
