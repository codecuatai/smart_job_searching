import hashlib
import hmac
import secrets
import time
from fastapi import Cookie, Depends, HTTPException
from .db import db


def hash_password(password):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 310000).hex()
    return f'{salt}${digest}'


def verify_password(password, value):
    salt, expected = value.split('$')
    actual = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 310000).hex()
    return hmac.compare_digest(expected, actual)


def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def current_user(unitalent_session: str | None = Cookie(default=None)):
    with db() as c:
        user = c.execute('''SELECT users.* FROM sessions JOIN users ON users.id=sessions.user_id
            WHERE token_hash=? AND expires_at>?''', (token_hash(unitalent_session or ''), time.time())).fetchone()
    if not user:
        raise HTTPException(401, 'Vui lòng đăng nhập.')
    return dict(user)


def require_role(role):
    def guard(user=Depends(current_user)):
        if user['role'] != role:
            raise HTTPException(403, 'Bạn không có quyền thực hiện thao tác này.')
        return user
    return guard
