from datetime import datetime
from enum import Enum

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    func,
    text,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    sessionmaker,
)

from backend.config import settings


# ============================================================
# Base
# ============================================================

class Base(DeclarativeBase):
    pass


# ============================================================
# Database engine
# ============================================================

engine_options = {
    "pool_pre_ping": True,
    "pool_recycle": 1800,
    "future": True,
}

if settings.database_url.startswith("sqlite"):
    engine_options["connect_args"] = {"check_same_thread": False}
else:
    engine_options.update(
        pool_size=5,
        max_overflow=10,
    )

engine = create_engine(
    settings.database_url,
    **engine_options,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


# ============================================================
# Roles
# ============================================================

class UserRole(str, Enum):
    TRAINEE = "trainee"
    TRAINER = "trainer"
    ADMIN = "admin"


# ============================================================
# User
# ============================================================

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    email: Mapped[str] = mapped_column(
        String(320),
        unique=True,
        nullable=False,
        index=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    role: Mapped[UserRole] = mapped_column(
        String(20),
        nullable=False,
        default=UserRole.TRAINEE,
        server_default=UserRole.TRAINEE.value,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    student_profile: Mapped["StudentProfile | None"] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
        single_parent=True,
    )

    sessions: Mapped[list["UserSession"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        CheckConstraint(
            "length(trim(email)) >= 5",
            name="ck_users_email_length",
        ),
        CheckConstraint(
            "length(trim(name)) >= 2",
            name="ck_users_name_length",
        ),
        CheckConstraint(
            "role IN ('trainee', 'trainer', 'admin')",
            name="ck_users_role",
        ),
        Index(
            "ix_users_email_lower",
            func.lower(email),
            unique=True,
        ),
    )


# ============================================================
# Community
# ============================================================

class CommunityPost(Base):
    __tablename__ = "community_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    topic: Mapped[str] = mapped_column(String(30), nullable=False, default="discussion")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    author: Mapped[User] = relationship()
    comments: Mapped[list["CommunityComment"]] = relationship(
        back_populates="post", cascade="all, delete-orphan", order_by="CommunityComment.created_at"
    )
    likes: Mapped[list["CommunityLike"]] = relationship(
        back_populates="post", cascade="all, delete-orphan"
    )


class CommunityComment(Base):
    __tablename__ = "community_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_id: Mapped[int] = mapped_column(
        ForeignKey("community_posts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    post: Mapped[CommunityPost] = relationship(back_populates="comments")
    author: Mapped[User] = relationship()


class CommunityLike(Base):
    __tablename__ = "community_likes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_id: Mapped[int] = mapped_column(
        ForeignKey("community_posts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    post: Mapped[CommunityPost] = relationship(back_populates="likes")
    user: Mapped[User] = relationship()

    __table_args__ = (UniqueConstraint("post_id", "user_id", name="uq_community_like"),)


# ============================================================
# User sessions
# ============================================================

class UserSession(Base):
    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    jti: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship(
        back_populates="sessions",
    )

    __table_args__ = (
        Index(
            "ix_user_sessions_user_active",
            "user_id",
            "revoked_at",
        ),
    )


# ============================================================
# Student profile
# ============================================================

class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        unique=True,
        nullable=False,
        index=True,
    )

    course: Mapped[str | None] = mapped_column(
        String(120),
    )

    age: Mapped[int | None] = mapped_column(
        Integer,
    )

    interest_level: Mapped[int | None] = mapped_column(
        Integer,
        default=3,
        server_default="3",
    )

    learning_depth: Mapped[int | None] = mapped_column(
        Integer,
        default=3,
        server_default="3",
    )

    current_streak: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )

    user: Mapped[User] = relationship(
        back_populates="student_profile",
    )

    progress_records: Mapped[list["StudentProgress"]] = relationship(
        back_populates="student",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        CheckConstraint(
            "age IS NULL OR age BETWEEN 3 AND 120",
            name="ck_student_profiles_age",
        ),
        CheckConstraint(
            "interest_level IS NULL OR interest_level BETWEEN 1 AND 5",
            name="ck_student_profiles_interest_level",
        ),
        CheckConstraint(
            "learning_depth IS NULL OR learning_depth BETWEEN 1 AND 5",
            name="ck_student_profiles_learning_depth",
        ),
        CheckConstraint(
            "current_streak >= 0",
            name="ck_student_profiles_current_streak",
        ),
        CheckConstraint(
            "current_streak <= 100000",
            name="ck_student_profiles_current_streak_max",
        ),
    )
    interactions: Mapped[list["LearningInteraction"]] = relationship(
        back_populates="student",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


# ============================================================
# Subject
# ============================================================

class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(120),
        unique=True,
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
    )

    progress_records: Mapped[list["StudentProgress"]] = relationship(
        back_populates="subject",
        passive_deletes=True,
    )

    __table_args__ = (
        CheckConstraint(
            "length(trim(name)) >= 2",
            name="ck_subjects_name_length",
        ),
        Index(
            "ix_subjects_name_lower",
            text("lower(name)"),
            unique=True,
        ),
    )


# ============================================================
# Student progress
# ============================================================

class StudentProgress(Base):
    __tablename__ = "student_progress"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    student_id: Mapped[int] = mapped_column(
        ForeignKey(
            "student_profiles.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    subject_id: Mapped[int] = mapped_column(
        ForeignKey(
            "subjects.id",
        ),
        nullable=False,
        index=True,
    )

    progress: Mapped[float] = mapped_column(
        Float,
        default=0,
        server_default="0",
        nullable=False,
    )

    average_score: Mapped[float | None] = mapped_column(
        Float,
    )

    questions_solved: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )

    last_activity: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    student: Mapped[StudentProfile] = relationship(
        back_populates="progress_records",
    )

    subject: Mapped[Subject] = relationship(
        back_populates="progress_records",
    )

    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "subject_id",
            name="uq_student_progress_student_subject",
        ),
        CheckConstraint(
            "progress BETWEEN 0 AND 100",
            name="ck_student_progress_progress",
        ),
        CheckConstraint(
            "average_score IS NULL OR average_score BETWEEN 0 AND 100",
            name="ck_student_progress_average_score",
        ),
        CheckConstraint(
            "questions_solved >= 0",
            name="ck_student_progress_questions_solved",
        ),
        CheckConstraint(
            "questions_solved <= 10000000",
            name="ck_student_progress_questions_solved_max",
        ),
        Index(
            "ix_student_progress_student_subject",
            "student_id",
            "subject_id",
        ),
    )
# ============================================================
# LEARNING INTERACTION HISTORY
# ============================================================

class LearningInteraction(Base):

    __tablename__ = "learning_interactions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    student_id: Mapped[int] = mapped_column(
        ForeignKey(
            "student_profiles.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    subject_id: Mapped[int] = mapped_column(
        ForeignKey(
            "subjects.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    topic: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    action: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    correctness: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    time_taken: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    reward: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    student = relationship(
        "StudentProfile",
        back_populates="interactions",
    )

    subject = relationship(
        "Subject",
    )

    __table_args__ = (
        CheckConstraint(
            "correctness IS NULL OR "
            "(correctness >= 0 AND correctness <= 1)",
            name="ck_interaction_correctness",
        ),
        CheckConstraint(
            "attempts >= 0",
            name="ck_interaction_attempts",
        ),
    )