from collections.abc import Generator
from datetime import datetime, timedelta, timezone

import os
import secrets

import jwt

from fastapi import (
    Cookie,
    Depends,
    FastAPI,
    HTTPException,
    Request,
    Response,
    status,
)

from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from backend.config import settings

from backend.database import (
    SessionLocal,
    StudentProfile,
    StudentProgress,
    Subject,
    User,
    UserRole,
    UserSession,
)

from backend.schemas import (
    LegacyStudentRead,
    LoginRequest,
    ProgressRead,
    ProgressUpsert,
    RegisterRequest,
    StudentCreate,
    StudentRead,
    StudentUpdate,
    SubjectCreate,
    SubjectRead,
    UserRead,
)

from backend.security import (
    generate_secure_token,
    hash_password,
    verify_password,
)


# ============================================================
# Application
# ============================================================

app = FastAPI(
    title="Adhyan API",
    version="1.0.0",
)


# ============================================================
# Rate limiting
# ============================================================

# Limit requests based on the client's IP address.
limiter = Limiter(
    key_func=get_remote_address
)

app.state.limiter = limiter

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler,
)


# ============================================================
# CORS
# ============================================================

# Never use "*" with credentialed authentication.
#
# Change this environment variable when deploying:
#
# FRONTEND_ORIGIN=https://your-domain.com
#
# For local development we allow common localhost ports.

frontend_origin = os.getenv(
    "FRONTEND_ORIGIN",
    "http://127.0.0.1:5500",
)

allowed_origins = {
    frontend_origin,
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
}

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(allowed_origins),
    allow_credentials=True,
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
    ],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-CSRF-Token",
    ],
)


# ============================================================
# Security configuration
# ============================================================

SESSION_COOKIE = "adhyan_session"
CSRF_COOKIE = "adhyan_csrf"

SESSION_DURATION = timedelta(hours=12)
LONG_SESSION_DURATION = timedelta(days=30)

COOKIE_SAMESITE = "lax"


# ============================================================
# Database dependency
# ============================================================

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# ============================================================
# Authentication helpers
# ============================================================

def create_session_token(
    user: User,
    duration: timedelta,
) -> tuple[str, str, datetime]:
    """
    Create a signed authentication token.

    The JTI uniquely identifies this login session.
    The JTI is stored in the database so the session
    can later be revoked during logout.
    """

    now = datetime.now(timezone.utc)
    expires_at = now + duration
    jti = secrets.token_hex(16)

    payload = {
        "sub": str(user.id),
        "iat": now,
        "exp": expires_at,
        "jti": jti,
    }

    token = jwt.encode(
        payload,
        settings.secret_key,
        algorithm="HS256",
    )

    return token, jti, expires_at


def decode_session_token(
    token: str,
) -> tuple[int, str, datetime]:
    """
    Decode and validate the authentication token.

    Returns:
        user_id
        jti
        expiration time
    """

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=["HS256"],
            options={
                "require": [
                    "sub",
                    "iat",
                    "exp",
                    "jti",
                ]
            },
        )

        user_id = payload.get("sub")
        jti = payload.get("jti")
        exp = payload.get("exp")

        if not isinstance(user_id, str):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication",
            )

        if not isinstance(jti, str):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication",
            )

        if not isinstance(exp, (int, float)):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication",
            )

        expires_at = datetime.fromtimestamp(
            exp,
            tz=timezone.utc,
        )

        return int(user_id), jti, expires_at

    except (
        jwt.ExpiredSignatureError,
        jwt.InvalidTokenError,
        ValueError,
        TypeError,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication",
        )


def get_current_user(
    session_token: str | None = Cookie(
        default=None,
        alias=SESSION_COOKIE,
    ),
    db: Session = Depends(get_db),
) -> User:
    """
    Authenticate the request.

    The JWT proves the token was signed by Adhyan.
    The database confirms that the session is still active.
    """

    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    user_id, jti, _ = decode_session_token(
        session_token
    )

    session = db.scalar(
        select(UserSession).where(
            UserSession.jti == jti,
            UserSession.user_id == user_id,
            UserSession.revoked_at.is_(None),
        )
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    now = datetime.now(timezone.utc)

    if session.expires_at <= now:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    user = db.get(
        User,
        user_id,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    return user


# ============================================================
# Authorization helpers
# ============================================================

def require_roles(
    *allowed_roles: UserRole,
):
    """
    Create a dependency requiring one of
    the specified roles.
    """

    def dependency(
        current_user: User = Depends(
            get_current_user
        ),
    ) -> User:

        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return current_user

    return dependency


def require_student_owner(
    student_id: int,
    current_user: User,
    db: Session,
) -> StudentProfile:

    profile = db.get(
        StudentProfile,
        student_id,
    )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    # Admin can access everything.
    if current_user.role == UserRole.ADMIN:
        return profile

    # Trainers may access student records.
    if current_user.role == UserRole.TRAINER:
        return profile

    # Trainees can ONLY access their own profile.
    if profile.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot access this student",
        )

    return profile


# ============================================================
# CSRF protection
# ============================================================

def verify_csrf(
    request: Request,
    csrf_cookie: str | None = Cookie(
        default=None,
        alias=CSRF_COOKIE,
    ),
) -> None:
    """
    Double-submit CSRF protection.
    """

    # Safe methods do not modify state.
    if request.method in {
        "GET",
        "HEAD",
        "OPTIONS",
    }:
        return

    csrf_header = request.headers.get(
        "X-CSRF-Token"
    )

    if not csrf_cookie or not csrf_header:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF validation failed",
        )

    if not secrets.compare_digest(
        csrf_cookie,
        csrf_header,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF validation failed",
        )


# ============================================================
# Response helpers
# ============================================================

def student_response(
    profile: StudentProfile,
) -> StudentRead:

    return StudentRead(
        id=profile.id,
        user_id=profile.user_id,
        email=profile.user.email,
        name=profile.user.name,
        course=profile.course,
        age=profile.age,
        interest_level=profile.interest_level,
        learning_depth=profile.learning_depth,
        current_streak=profile.current_streak,
        created_at=profile.user.created_at,
    )


def legacy_student_response(
    profile: StudentProfile,
) -> LegacyStudentRead:

    return LegacyStudentRead(
        id=profile.id,
        name=profile.user.name,
        age=profile.age,
        course=profile.course,
        interest_level=profile.interest_level,
        learning_depth=profile.learning_depth,
    )


def progress_response(
    record: StudentProgress,
) -> ProgressRead:

    return ProgressRead(
        id=record.id,
        student_id=record.student_id,
        subject_id=record.subject_id,
        subject_name=record.subject.name,
        progress=record.progress,
        average_score=record.average_score,
        questions_solved=record.questions_solved,
        last_activity=record.last_activity,
    )


# ============================================================
# Student creation
# ============================================================

def create_student_record(
    student: StudentCreate,
    db: Session,
) -> StudentProfile:

    existing_user = db.scalar(
        select(User).where(
            User.email == student.email
        )
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        )

    user = User(
        email=student.email,
        password_hash=hash_password(
            student.password
        ),
        name=student.name,
        role=UserRole.TRAINEE,
    )

    profile = StudentProfile(
        user=user,
        course=student.course,
        age=student.age,
        interest_level=student.interest_level,
        learning_depth=student.learning_depth,
        current_streak=0,
    )

    db.add(profile)

    try:
        db.commit()

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        )

    db.refresh(profile)

    return profile


# ============================================================
# Health / root
# ============================================================

@app.get("/")
def home() -> dict[str, str]:
    return {
        "message": "Adhyan backend is running"
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok"
    }


# ============================================================
# Registration
# ============================================================

@app.post(
    "/auth/register",
    response_model=StudentRead,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("3/minute")
def register(
    request: Request,
    registration: RegisterRequest,
    db: Session = Depends(get_db),
) -> StudentRead:

    existing_user = db.scalar(
        select(User).where(
            User.email == registration.email
        )
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        )

    user = User(
        email=str(
            registration.email
        ).lower(),
        password_hash=hash_password(
            registration.password
        ),
        name=registration.name,
        role=UserRole.TRAINEE,
    )

    profile = StudentProfile(
        user=user,
        current_streak=0,
    )

    db.add(profile)

    try:
        db.commit()

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        )

    db.refresh(profile)

    return student_response(profile)


# ============================================================
# Login
# ============================================================

@app.post("/auth/login")
@limiter.limit("5/minute")
def login(
    request: Request,
    login_data: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> dict[str, str]:

    user = db.scalar(
        select(User).where(
            User.email == login_data.email
        )
    )

    # IMPORTANT:
    # Do not reveal whether an email exists.
    #
    # We still perform password hashing work
    # when the user does not exist.

    if not user:
        hash_password(
            login_data.password
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(
        login_data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    duration = SESSION_DURATION

    session_token, jti, expires_at = create_session_token(
        user,
        duration,
    )

    user_session = UserSession(
        user_id=user.id,
        jti=jti,
        expires_at=expires_at,
    )

    db.add(user_session)

    try:
        db.commit()

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create session",
        )

    csrf_token = generate_secure_token(32)

    response.set_cookie(
        key=SESSION_COOKIE,
        value=session_token,
        httponly=True,
        secure=False,
        samesite=COOKIE_SAMESITE,
        max_age=int(
            duration.total_seconds()
        ),
        path="/",
    )

    response.set_cookie(
        key=CSRF_COOKIE,
        value=csrf_token,
        httponly=False,
        secure=False,
        samesite=COOKIE_SAMESITE,
        max_age=int(
            duration.total_seconds()
        ),
        path="/",
    )

    return {
        "message": "Login successful"
    }


# ============================================================
# Current user
# ============================================================

@app.get(
    "/auth/me",
    response_model=UserRead,
)
def current_user(
    user: User = Depends(
        get_current_user
    ),
) -> User:

    return user


# ============================================================
# Logout
# ============================================================

@app.post("/auth/logout")
def logout(
    response: Response,
    session_token: str | None = Cookie(
        default=None,
        alias=SESSION_COOKIE,
    ),
    db: Session = Depends(get_db),
    _: None = Depends(
        verify_csrf
    ),
) -> dict[str, str]:

    if session_token:

        try:
            _, jti, _ = decode_session_token(
                session_token
            )

            user_session = db.scalar(
                select(UserSession).where(
                    UserSession.jti == jti
                )
            )

            if (
                user_session
                and user_session.revoked_at is None
            ):
                user_session.revoked_at = datetime.now(
                    timezone.utc
                )

                db.commit()

        except HTTPException:
            # Even if the token is already invalid,
            # still clear the browser cookies.
            pass

    response.delete_cookie(
        SESSION_COOKIE,
        path="/",
    )

    response.delete_cookie(
        CSRF_COOKIE,
        path="/",
    )

    return {
        "message": "Logged out successfully"
    }


# ============================================================
# Students
# ============================================================

@app.get(
    "/api/students",
    response_model=list[StudentRead],
)
def list_students(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
) -> list[StudentRead]:

    # Trainees should never receive
    # the entire student database.

    if current_user.role == UserRole.TRAINEE:

        profile = current_user.student_profile

        if not profile:
            return []

        return [
            student_response(profile)
        ]

    profiles = db.scalars(
        select(StudentProfile)
        .order_by(StudentProfile.id)
    ).all()

    return [
        student_response(profile)
        for profile in profiles
    ]


@app.get(
    "/api/students/{student_id}",
    response_model=StudentRead,
)
def retrieve_student(
    student_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
) -> StudentRead:

    profile = require_student_owner(
        student_id,
        current_user,
        db,
    )

    return student_response(profile)


@app.patch(
    "/api/students/{student_id}",
    response_model=StudentRead,
)
def update_student(
    student_id: int,
    update: StudentUpdate,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
    _: None = Depends(
        verify_csrf
    ),
) -> StudentRead:

    profile = require_student_owner(
        student_id,
        current_user,
        db,
    )

    if update.name is not None:
        profile.user.name = update.name

    if update.course is not None:
        profile.course = update.course

    if update.age is not None:
        profile.age = update.age

    if update.interest_level is not None:
        profile.interest_level = (
            update.interest_level
        )

    if update.learning_depth is not None:
        profile.learning_depth = (
            update.learning_depth
        )

    db.commit()
    db.refresh(profile)

    return student_response(profile)


# ============================================================
# Subjects
# ============================================================

@app.post(
    "/api/subjects",
    response_model=SubjectRead,
    status_code=status.HTTP_201_CREATED,
)
def create_subject(
    subject: SubjectCreate,
    current_user: User = Depends(
        require_roles(
            UserRole.ADMIN,
            UserRole.TRAINER,
        )
    ),
    db: Session = Depends(get_db),
    _: None = Depends(
        verify_csrf
    ),
) -> Subject:

    existing_subject = db.scalar(
        select(Subject).where(
            Subject.name == subject.name
        )
    )

    if existing_subject:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Subject already exists",
        )

    new_subject = Subject(
        name=subject.name,
        description=subject.description,
    )

    db.add(new_subject)

    try:
        db.commit()

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Subject already exists",
        )

    db.refresh(new_subject)

    return new_subject


@app.get(
    "/api/subjects",
    response_model=list[SubjectRead],
)
def list_subjects(
    _: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
) -> list[Subject]:

    return db.scalars(
        select(Subject)
        .order_by(Subject.name)
    ).all()


# ============================================================
# Student progress
# ============================================================

@app.put(
    "/api/students/{student_id}/progress/{subject_id}",
    response_model=ProgressRead,
)
def create_or_update_progress(
    student_id: int,
    subject_id: int,
    progress: ProgressUpsert,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
    _: None = Depends(
        verify_csrf
    ),
) -> ProgressRead:

    student = require_student_owner(
        student_id,
        current_user,
        db,
    )

    subject = db.get(
        Subject,
        subject_id,
    )

    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found",
        )

    record = db.scalar(
        select(StudentProgress).where(
            StudentProgress.student_id == student.id,
            StudentProgress.subject_id == subject.id,
        )
    )

    if not record:
        record = StudentProgress(
            student=student,
            subject=subject,
        )

        db.add(record)

    record.progress = progress.progress

    record.average_score = (
        progress.average_score
    )

    record.questions_solved = (
        progress.questions_solved
    )

    # Server controls activity timestamps.
    record.last_activity = (
        datetime.now(timezone.utc)
    )

    db.commit()
    db.refresh(record)

    return progress_response(record)


@app.get(
    "/api/students/{student_id}/progress",
    response_model=list[ProgressRead],
)
def retrieve_student_progress(
    student_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
) -> list[ProgressRead]:

    student = require_student_owner(
        student_id,
        current_user,
        db,
    )

    records = db.scalars(
        select(StudentProgress)
        .where(
            StudentProgress.student_id
            == student.id
        )
        .order_by(
            StudentProgress.subject_id
        )
    ).all()

    return [
        progress_response(record)
        for record in records
    ]


# ============================================================
# Legacy compatibility endpoints
# ============================================================

@app.get(
    "/students",
    response_model=list[LegacyStudentRead],
)
def legacy_list_students(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
) -> list[LegacyStudentRead]:

    if current_user.role == UserRole.TRAINEE:

        profile = current_user.student_profile

        if not profile:
            return []

        return [
            legacy_student_response(profile)
        ]

    profiles = db.scalars(
        select(StudentProfile)
        .order_by(StudentProfile.id)
    ).all()

    return [
        legacy_student_response(profile)
        for profile in profiles
    ]


@app.post(
    "/students",
    status_code=status.HTTP_201_CREATED,
)
def legacy_create_student(
    student: StudentCreate,
    current_user: User = Depends(
        require_roles(
            UserRole.ADMIN
        )
    ),
    db: Session = Depends(get_db),
    _: None = Depends(
        verify_csrf
    ),
) -> dict[str, LegacyStudentRead | str]:

    profile = create_student_record(
        student,
        db,
    )

    return {
        "message": "Student added successfully",
        "student": legacy_student_response(
            profile
        ),
    }


# ============================================================
# Dashboard
# ============================================================

@app.get("/dashboard")
def get_dashboard(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
) -> dict:

    # A trainee gets ONLY their own information.

    if current_user.role == UserRole.TRAINEE:

        profile = current_user.student_profile

        if not profile:
            return {
                "student_count": 0,
                "average_interest": 0,
                "average_learning_depth": 0,
                "students": [],
            }

        return {
            "student_count": 1,
            "average_interest":
                profile.interest_level or 0,
            "average_learning_depth":
                profile.learning_depth or 0,
            "students": [
                legacy_student_response(
                    profile
                )
            ],
        }

    profiles = db.scalars(
        select(StudentProfile)
        .order_by(StudentProfile.id)
    ).all()

    total_students = len(profiles)

    if not total_students:
        return {
            "student_count": 0,
            "average_interest": 0,
            "average_learning_depth": 0,
            "students": [],
        }

    return {
        "student_count": total_students,
        "average_interest": round(
            sum(
                profile.interest_level or 0
                for profile in profiles
            ) / total_students,
            1,
        ),
        "average_learning_depth": round(
            sum(
                profile.learning_depth or 0
                for profile in profiles
            ) / total_students,
            1,
        ),
        "students": [
            legacy_student_response(profile)
            for profile in profiles
        ],
    }


# ============================================================
# Delete student
# ============================================================

@app.delete("/students/{student_id}")
def delete_student(
    student_id: int,
    current_user: User = Depends(
        require_roles(
            UserRole.ADMIN
        )
    ),
    db: Session = Depends(get_db),
    _: None = Depends(
        verify_csrf
    ),
) -> dict[str, str]:

    profile = db.get(
        StudentProfile,
        student_id,
    )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    db.delete(profile.user)
    db.commit()

    return {
        "message": "Student deleted successfully"
    }