import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.api.v1.dependencies import current_user, teacher_only
from backend.app.core.security import hash_secret, random_base62
from backend.app.core.settings import settings
from backend.app.infrastructure.database.connection import connect


router = APIRouter(prefix="/classrooms", tags=["classrooms"])


class CreateClassroomRequest(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=2000)


class JoinClassroomRequest(BaseModel):
    code: str = Field(min_length=8, max_length=32)


def unique_values(connection) -> tuple[str, str, str]:
    for _ in range(10):
        classroom_id = str(uuid.uuid4())
        public_slug = random_base62(20)
        join_code = random_base62(10)
        join_hash = hash_secret(join_code, settings.secret_key)
        exists = connection.execute(
            "SELECT 1 FROM classrooms WHERE public_slug = %s OR join_code_hash = %s", (public_slug, join_hash)
        ).fetchone()
        if not exists:
            return classroom_id, public_slug, join_code
    raise HTTPException(status_code=503, detail="Could not allocate a unique classroom identifier")


def classroom_view(row, *, join_code: str | None = None) -> dict:
    result = {
        "id": row["id"],
        "slug": row["public_slug"],
        "name": row["name"],
        "description": row["description"],
        "owner_id": row["owner_id"],
        "created_at": row["created_at"],
    }
    if join_code is not None:
        result["join_code"] = join_code
    return result


@router.post("", status_code=status.HTTP_201_CREATED)
def create_classroom(payload: CreateClassroomRequest, teacher=Depends(teacher_only)):
    connection = connect()
    classroom_id, slug, join_code = unique_values(connection)
    try:
        connection.execute(
            "INSERT INTO classrooms (id, public_slug, name, description, owner_id, join_code_hash) VALUES (%s, %s, %s, %s, %s, %s)",
            (classroom_id, slug, payload.name.strip(), payload.description, teacher["id"], hash_secret(join_code, settings.secret_key)),
        )
        connection.execute(
            "INSERT INTO classroom_memberships (classroom_id, user_id, role) VALUES (%s, %s, 'owner')",
            (classroom_id, teacher["id"]),
        )
        connection.commit()
        row = connection.execute("SELECT * FROM classrooms WHERE id = %s", (classroom_id,)).fetchone()
    finally:
        connection.close()
    return {"classroom": classroom_view(row, join_code=join_code), "join_code_notice": "Store or share this code now; it is not exposed in URLs."}


@router.post("/join")
def join_classroom(payload: JoinClassroomRequest, user=Depends(current_user)):
    code_hash = hash_secret(payload.code.strip(), settings.secret_key)
    connection = connect()
    classroom = connection.execute("SELECT * FROM classrooms WHERE join_code_hash = %s", (code_hash,)).fetchone()
    if classroom is None:
        connection.close()
        raise HTTPException(status_code=404, detail="Invalid classroom code")
    if classroom["owner_id"] == user["id"]:
        connection.close()
        return {"classroom": classroom_view(classroom), "already_member": True}
    try:
        connection.execute(
            "INSERT INTO classroom_memberships (classroom_id, user_id, role) VALUES (%s, %s, 'student')",
            (classroom["id"], user["id"]),
        )
        connection.commit()
        already_member = False
    except Exception as error:
        if "duplicate key" not in str(error).lower():
            raise
        already_member = True
    finally:
        connection.close()
    return {"classroom": classroom_view(classroom), "already_member": already_member}


@router.get("")
def list_classrooms(user=Depends(current_user)):
    connection = connect()
    rows = connection.execute(
        "SELECT c.* FROM classrooms c JOIN classroom_memberships m ON m.classroom_id = c.id WHERE m.user_id = %s ORDER BY c.created_at DESC",
        (user["id"],),
    ).fetchall()
    connection.close()
    return {"classrooms": [classroom_view(row) for row in rows]}


def get_member_classroom(slug: str, user_id: str):
    connection = connect()
    row = connection.execute(
        "SELECT c.* FROM classrooms c JOIN classroom_memberships m ON m.classroom_id = c.id WHERE c.public_slug = %s AND m.user_id = %s",
        (slug, user_id),
    ).fetchone()
    connection.close()
    if row is None:
        raise HTTPException(status_code=404, detail="Classroom not found")
    return row


@router.get("/{slug}")
def get_classroom(slug: str, user=Depends(current_user)):
    return {"classroom": classroom_view(get_member_classroom(slug, user["id"]))}


@router.post("/{slug}/rotate-code")
def rotate_join_code(slug: str, teacher=Depends(teacher_only)):
    connection = connect()
    classroom = connection.execute("SELECT * FROM classrooms WHERE public_slug = %s AND owner_id = %s", (slug, teacher["id"])).fetchone()
    if classroom is None:
        connection.close()
        raise HTTPException(status_code=404, detail="Classroom not found")
    _, _, join_code = unique_values(connection)
    connection.execute("UPDATE classrooms SET join_code_hash = %s WHERE id = %s", (hash_secret(join_code, settings.secret_key), classroom["id"]))
    connection.commit()
    connection.close()
    return {"slug": slug, "join_code": join_code, "notice": "The previous join code is now invalid."}
