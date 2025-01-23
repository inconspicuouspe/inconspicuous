from hashlib import sha3_512
from io import BytesIO
from typing import Optional
from base64 import urlsafe_b64encode, urlsafe_b64decode
from database import Database
import secrets

encode_b64 = urlsafe_b64encode
decode_b64 = urlsafe_b64decode

VALID_CHARACTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_"

def validate_username_and_password(username: str, password: str) -> Optional[str]:
    if len(username) < 3:
        return "Username must be between 3 and 32 characters long."
    if len(username) > 32:
        return "Username must be between 3 and 32 characters long."
    for char in username:
        if char not in VALID_CHARACTERS:
            return "Username must consist of characters a-z, A-Z, 0-9 and _."
    if len(password) < 5:
        return "Password must be between 5 and 65535 characters long."
    if len(password) > 65535:
        return "Password must be between 5 and 65535 characters long."
    return None

def create_session_data(username: str, password: str) -> tuple[str, int]:
    assert not validate_username_and_password(username, password)
    unhashed_data = BytesIO()
    unhashed_data.write(len(username).to_bytes(1))
    unhashed_data.write(username.encode("utf-8"))
    unhashed_data.write(len(password).to_bytes(2))
    unhashed_data.write(password.encode("utf-8"))
    session_token = secrets.randbits(64)
    unhashed_data.write(session_token.to_bytes(8))
    hashed_data = sha3_512(unhashed_data.getbuffer()).digest()
    return (encode_b64(hashed_data), session_token)

def lookup_user_by_session_data(database: Database, session_data: str) -> str:
    return database.user_by_session_data(session_data)