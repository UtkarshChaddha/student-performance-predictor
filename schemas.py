from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# ============================================================
# Shared configuration
# ============================================================

class StrictBaseModel(BaseModel):
    """
    Reject unexpected fields instead of silently accepting them.

    Example:
        {"email": "...", "role": "admin"}

    The "role" field will NOT be silently ignored.
    The request is rejected.
    """
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )


# ============================================================
# Authentication
# ============================================================

class RegisterRequest(StrictBaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    name: str = Field(min_length=2, max_length=120)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if value != value.strip():
            raise ValueError("Password must not begin or end with whitespace")

        if len(value) < 12:
            raise ValueError("Password must contain at least 12 characters")

        return value

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()

        if len(value) < 2:
            raise ValueError("Name must contain at least two characters")

        return value


class LoginRequest(StrictBaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()


class UserRead(StrictBaseModel):
    id: int
    email: EmailStr
    name: str
    role: str
    created_at: datetime


# ============================================================
# Student creation
# ============================================================

class StudentCreate(StrictBaseModel):
    """
    Kept for compatibility with the existing student endpoints.

    IMPORTANT:
    There is deliberately NO role field here.

    Authorization must always be decided by the backend.
    """

    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    name: str = Field(min_length=2, max_length=120)

    course: str | None = Field(
        default=None,
        max_length=120,
    )

    age: int | None = Field(
        default=None,
        ge=3,
        le=120,
    )

    interest_level: int | None = Field(
        default=3,
        ge=1,
        le=5,
    )

    learning_depth: int | None = Field(
        default=3,
        ge=1,
        le=5,
    )

    current_streak: int = Field(
        default=0,
        ge=0,
        le=10_000,
    )

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if value != value.strip():
            raise ValueError("Password must not begin or end with whitespace")

        return value

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()

        if len(value) < 2:
            raise ValueError("Name must contain at least two characters")

        return value

    @field_validator("course")
    @classmethod
    def normalize_course(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()

        return value or None


# ============================================================
# Student responses
# ============================================================

class StudentRead(BaseModel):
    """
    Public/API response model.

    Password hashes are intentionally absent.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    email: EmailStr
    name: str
    course: str | None
    age: int | None
    interest_level: int | None
    learning_depth: int | None
    current_streak: int
    created_at: datetime


class LegacyStudentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    age: int | None
    course: str | None
    interest_level: int | None
    learning_depth: int | None


# ============================================================
# Student profile updates
# ============================================================

class StudentUpdate(StrictBaseModel):
    """
    Used when an authenticated user updates their profile.

    Notice what is NOT here:
    - user_id
    - role
    - password_hash
    - email ownership
    - current_streak

    Those must not be mass-assigned by the client.
    """

    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=120,
    )

    course: str | None = Field(
        default=None,
        max_length=120,
    )

    age: int | None = Field(
        default=None,
        ge=3,
        le=120,
    )

    interest_level: int | None = Field(
        default=None,
        ge=1,
        le=5,
    )

    learning_depth: int | None = Field(
        default=None,
        ge=1,
        le=5,
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if len(value) < 2:
            raise ValueError("Name must contain at least two characters")

        return value

    @field_validator("course")
    @classmethod
    def normalize_course(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()

        return value or None


# ============================================================
# Subjects
# ============================================================

class SubjectCreate(StrictBaseModel):
    name: str = Field(
        min_length=2,
        max_length=120,
    )

    description: str | None = Field(
        default=None,
        max_length=2_000,
    )

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        value = value.strip()

        if len(value) < 2:
            raise ValueError("Subject name must contain at least two characters")

        return value

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()

        return value or None


class SubjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None


# ============================================================
# Progress
# ============================================================

class ProgressUpsert(StrictBaseModel):
    """
    Client may update progress values only.

    Ownership/authorization is handled by the backend,
    NOT by this schema.
    """

    progress: float = Field(
        ge=0,
        le=100,
    )

    average_score: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    questions_solved: int = Field(
        default=0,
        ge=0,
        le=10_000_000,
    )

    last_activity: datetime | None = None


class ProgressRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    subject_id: int
    subject_name: str
    progress: float
    average_score: float | None
    questions_solved: int
    last_activity: datetime | None

