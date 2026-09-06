import secrets

from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher


# Argon2id password hashing.
#
# pwdlib handles:
# - unique random salts
# - secure password hashing
# - constant-time verification
# - encoded hash parameters
#
# We deliberately do NOT implement cryptography ourselves.
password_hasher = PasswordHash(
    (
        Argon2Hasher(
            time_cost=3,
            memory_cost=65536,  # 64 MiB
            parallelism=4,
            hash_len=32,
            salt_len=16,
        ),
    )
)


def hash_password(password: str) -> str:
    """Hash a password using Argon2id."""
    if not isinstance(password, str):
        raise TypeError("Password must be a string")

    if not password:
        raise ValueError("Password cannot be empty")

    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Safely verify a password against an Argon2id hash."""
    if not isinstance(password, str):
        return False

    if not isinstance(password_hash, str):
        return False

    if not password_hash:
        return False

    try:
        return password_hasher.verify(password, password_hash)
    except (ValueError, TypeError):
        return False


def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token."""
    if length < 32:
        raise ValueError("Token length must be at least 32 bytes")

    return secrets.token_urlsafe(length)