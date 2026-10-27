from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.app.core.security import decode_access_token
from backend.app.core.settings import settings
from backend.app.infrastructure.database.connection import connect


bearer = HTTPBearer(auto_error=False)


def current_user(request: Request, credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)], access_token: str | None = Cookie(default=None)):
    token = credentials.credentials if credentials is not None else access_token
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        claims = decode_access_token(token, settings.secret_key)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from None
    connection = connect()
    user = connection.execute("SELECT id, email, name, role FROM users WHERE id = %s", (claims["sub"],)).fetchone()
    connection.close()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists")
    return dict(user)


def teacher_only(user=Depends(current_user)):
    if user["role"] != "teacher":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher access required")
    return user
