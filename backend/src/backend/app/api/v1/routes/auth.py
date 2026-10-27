import uuid
import secrets
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from pydantic import BaseModel, Field, field_validator

from backend.app.api.v1.dependencies import current_user
from backend.app.core.security import create_access_token, create_oauth_state, hash_password, verify_oauth_state, verify_password
from backend.app.core.settings import settings
from backend.app.infrastructure.database.connection import connect


router = APIRouter(prefix="/auth", tags=["auth"])
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"


class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=8, max_length=128)
    teacher_invite_code: str | None = Field(default=None, min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        value = value.strip().lower()
        if value.count("@") != 1 or "." not in value.rsplit("@", 1)[1]:
            raise ValueError("Enter a valid email address")
        return value


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class TeacherRegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    unique_id: str = Field(min_length=4, max_length=80, pattern=r"^[A-Za-z0-9._-]+$")
    password: str = Field(min_length=8, max_length=128)
    teacher_invite_code: str = Field(min_length=8, max_length=128)


class TeacherLoginRequest(BaseModel):
    unique_id: str = Field(min_length=1, max_length=80)
    password: str


class TeacherUpgradeRequest(BaseModel):
    invite_code: str = Field(min_length=8, max_length=128)


def user_response(user: dict, token: str) -> dict:
    return {"access_token": token, "token_type": "bearer", "user": user}


def teacher_user(row: dict) -> dict:
    return {"id": row["id"], "email": row["email"], "name": row["name"], "role": "teacher", "unique_id": row["unique_id"]}


@router.get("/google/start")
def google_start(response: Response):
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=503, detail="Google OAuth is not configured")
    state = create_oauth_state(settings.secret_key)
    response = RedirectResponse(
        url=GOOGLE_AUTH_URL
        + "?"
        + urlencode({
            "client_id": settings.google_client_id,
            "redirect_uri": settings.google_redirect_uri,
            "response_type": "code",
            "scope": "openid profile email",
            "state": state,
            "prompt": "select_account",
        })
    )
    response.set_cookie("google_oauth_state", state, max_age=600, httponly=True, secure=False, samesite="lax")
    return response


@router.get("/google/callback")
async def google_callback(request: Request, code: str | None = None, state: str | None = None, error: str | None = None):
    if error:
        return RedirectResponse(f"{settings.frontend_url}/?auth_error={error}")
    expected_state = request.cookies.get("google_oauth_state")
    # The signed state is the source of truth. The cookie is an additional check
    # when the browser stays on one host; localhost and 127.0.0.1 cannot share cookies.
    if not code or not state or not verify_oauth_state(state, settings.secret_key):
        raise HTTPException(status_code=400, detail="Invalid OAuth state")
    async with httpx.AsyncClient(timeout=10) as client:
        token_response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if token_response.is_error:
            raise HTTPException(status_code=502, detail="Google token exchange failed")
        tokens = token_response.json()
        try:
            claims = id_token.verify_oauth2_token(tokens["id_token"], google_requests.Request(), settings.google_client_id)
        except Exception:
            raise HTTPException(status_code=401, detail="Google ID token verification failed") from None
        user_response = await client.get(GOOGLE_USERINFO_URL, headers={"Authorization": f"Bearer {tokens['access_token']}"})
        if user_response.is_error:
            raise HTTPException(status_code=502, detail="Google profile lookup failed")
        profile = user_response.json()
    if not claims.get("sub") or not claims.get("email") or not claims.get("email_verified"):
        raise HTTPException(status_code=400, detail="Google account email is not verified")
    profile = {**claims, **profile}
    connection = connect()
    row = connection.execute("SELECT * FROM users WHERE google_subject = %s OR email = %s", (profile["sub"], profile["email"].lower())).fetchone()
    if row is None:
        user = {"id": str(uuid.uuid4()), "email": profile["email"].lower(), "name": profile.get("name") or profile["email"].split("@")[0], "role": "student"}
        connection.execute(
            "INSERT INTO users (id, email, name, password_hash, role, google_subject) VALUES (%s, %s, %s, %s, %s, %s)",
            (user["id"], user["email"], user["name"], hash_password(secrets.token_urlsafe(32)), user["role"], profile["sub"]),
        )
    else:
        user = {"id": row["id"], "email": row["email"], "name": profile.get("name") or row["name"], "role": row["role"]}
        connection.execute("UPDATE users SET name = %s, google_subject = %s WHERE id = %s", (user["name"], profile["sub"], user["id"]))
    connection.commit()
    connection.close()
    token = create_access_token(user["id"], user["role"], settings.secret_key, settings.access_token_ttl_seconds)
    redirect = RedirectResponse(f"{settings.frontend_url}/classroom")
    redirect.set_cookie("access_token", token, max_age=settings.access_token_ttl_seconds, httponly=True, secure=False, samesite="lax")
    redirect.delete_cookie("google_oauth_state")
    return redirect


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response):
    response.delete_cookie("access_token")


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest):
    connection = connect()
    if payload.teacher_invite_code and (
        not settings.teacher_invite_code
        or not secrets.compare_digest(payload.teacher_invite_code, settings.teacher_invite_code)
    ):
        connection.close()
        raise HTTPException(status_code=403, detail="Teacher invite code is invalid")
    role = "teacher" if payload.teacher_invite_code else "student"
    user = {"id": str(uuid.uuid4()), "email": payload.email, "name": payload.name.strip(), "role": role}
    try:
        connection.execute(
            "INSERT INTO users (id, email, name, password_hash, role) VALUES (%s, %s, %s, %s, %s)",
            (user["id"], user["email"], user["name"], hash_password(payload.password), user["role"]),
        )
        connection.commit()
    except Exception as error:
        if "duplicate key" not in str(error).lower():
            raise
        raise HTTPException(status_code=409, detail="An account with this email already exists") from None
    finally:
        connection.close()
    token = create_access_token(user["id"], user["role"], settings.secret_key, settings.access_token_ttl_seconds)
    return user_response(user, token)


@router.post("/teacher/register", status_code=status.HTTP_201_CREATED)
def teacher_register(payload: TeacherRegisterRequest, response: Response):
    if not settings.teacher_invite_code or not secrets.compare_digest(payload.teacher_invite_code, settings.teacher_invite_code):
        raise HTTPException(status_code=403, detail="Teacher invite code is invalid")
    connection = connect()
    unique_id = payload.unique_id.strip().lower()
    user = {"id": str(uuid.uuid4()), "email": f"{unique_id}@teacher.local", "name": payload.name.strip(), "role": "teacher", "unique_id": unique_id}
    try:
        connection.execute(
            "INSERT INTO users (id, email, name, password_hash, role, unique_id) VALUES (%s, %s, %s, %s, 'teacher', %s)",
            (user["id"], user["email"], user["name"], hash_password(payload.password), unique_id),
        )
        connection.commit()
    except Exception as error:
        if "duplicate key" in str(error).lower():
            raise HTTPException(status_code=409, detail="That teacher ID is already registered") from None
        raise
    finally:
        connection.close()
    token = create_access_token(user["id"], "teacher", settings.secret_key, settings.access_token_ttl_seconds)
    response.set_cookie("access_token", token, max_age=settings.access_token_ttl_seconds, httponly=True, secure=False, samesite="lax")
    return user_response(user, token)


@router.post("/teacher/login")
def teacher_login(payload: TeacherLoginRequest, response: Response):
    connection = connect()
    row = connection.execute("SELECT * FROM users WHERE unique_id = %s AND role = 'teacher'", (payload.unique_id.strip().lower(),)).fetchone()
    connection.close()
    if row is None or not verify_password(payload.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect teacher ID or password")
    user = teacher_user(row)
    token = create_access_token(user["id"], "teacher", settings.secret_key, settings.access_token_ttl_seconds)
    response.set_cookie("access_token", token, max_age=settings.access_token_ttl_seconds, httponly=True, secure=False, samesite="lax")
    return user_response(user, token)


@router.post("/login")
def login(payload: LoginRequest):
    connection = connect()
    row = connection.execute("SELECT * FROM users WHERE email = %s", (payload.email,)).fetchone()
    connection.close()
    if row is None or not verify_password(payload.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    user = {"id": row["id"], "email": row["email"], "name": row["name"], "role": row["role"]}
    token = create_access_token(user["id"], user["role"], settings.secret_key, settings.access_token_ttl_seconds)
    return user_response(user, token)


@router.get("/me")
def me(user=Depends(current_user)):
    return {"user": user}


@router.post("/upgrade-teacher")
def upgrade_teacher(payload: TeacherUpgradeRequest, user=Depends(current_user)):
    if not settings.teacher_invite_code or not secrets.compare_digest(payload.invite_code, settings.teacher_invite_code):
        raise HTTPException(status_code=403, detail="Invalid teacher invite code")
    connection = connect()
    connection.execute("UPDATE users SET role = 'teacher' WHERE id = %s", (user["id"],))
    connection.commit()
    connection.close()
    return {"user": {**user, "role": "teacher"}}
