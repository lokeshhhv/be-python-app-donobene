import bcrypt

def hash_password(password: str) -> str:
    """Hash password using bcrypt directly."""
    truncated = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(truncated, salt)
    return hashed.decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    """Verify password against bcrypt hash."""
    truncated = plain.encode("utf-8")[:72]
    return bcrypt.checkpw(truncated, hashed.encode("utf-8"))