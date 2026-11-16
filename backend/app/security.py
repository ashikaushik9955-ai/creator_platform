import bcrypt


def hash_password(password: str) -> str:
    """Return a bcrypt hash (salt included) for the given password."""
    return bcrypt.hashpw(
        password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    """Check a plain password against a stored bcrypt hash."""
    return bcrypt.checkpw(
        password.encode("utf-8"), hashed_password.encode("utf-8")
    )