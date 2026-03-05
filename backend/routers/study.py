"""Study/workspace router: persisted notes, saved queries, compare history, timeline."""

from __future__ import annotations

import json
import hashlib
import uuid
import math
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import text
from sqlalchemy.orm import Session

from core.db import build_engine, build_session_local, get_database_url
from core.job_queue import get_job_queue
from .auth import get_current_user

DATABASE_URL = get_database_url()
engine = build_engine(DATABASE_URL)
SessionLocal = build_session_local(engine)

router = APIRouter(prefix="/api/v1/study", tags=["study"])


def _parse_iso_datetime(value: str, field_name: str) -> datetime:
    candidate = value.strip()
    try:
        return datetime.fromisoformat(candidate.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a valid ISO date/datetime string") from exc


class BBox(BaseModel):
    min_lon: float = Field(..., ge=-180, le=180)
    min_lat: float = Field(..., ge=-90, le=90)
    max_lon: float = Field(..., ge=-180, le=180)
    max_lat: float = Field(..., ge=-90, le=90)

    @model_validator(mode="after")
    def validate_bbox(self):
        if self.min_lon > self.max_lon:
            raise ValueError("bbox.min_lon must be <= bbox.max_lon")
        if self.min_lat > self.max_lat:
            raise ValueError("bbox.min_lat must be <= bbox.max_lat")
        return self


class WorkspaceCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=500)


class WorkspaceUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=500)


class WorkspaceCloneRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    include_notes: bool = True
    include_queries: bool = True


class WorkspaceVersionCreateRequest(BaseModel):
    label: Optional[str] = Field(default=None, min_length=1, max_length=120)
    include_notes: bool = True
    include_queries: bool = True
    include_compare_history: bool = True
    include_timeline_history: bool = True
    history_limit: int = Field(default=200, ge=1, le=500)


class WorkspaceVersionRestoreRequest(BaseModel):
    dry_run: bool = True
    restore_notes: bool = True
    restore_queries: bool = True
    restore_compare_history: bool = True
    restore_timeline_history: bool = True
    mode: Literal["replace"] = "replace"


class ReproPackageJobRequest(BaseModel):
    version_id: Optional[str] = None


class WorkspaceMemberInviteRequest(BaseModel):
    user_identifier: str = Field(..., min_length=3, max_length=255)
    role: Literal["viewer", "editor"] = "viewer"


class WorkspaceMemberUpdateRequest(BaseModel):
    role: Literal["viewer", "editor"]
    status: Literal["active", "revoked"] = "active"


class NoteCreateRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)


class SavedQueryCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=160)
    query_payload: Dict[str, Any]


class CompareRequest(BaseModel):
    region_a: str = Field(..., min_length=1, max_length=64)
    region_b: str = Field(..., min_length=1, max_length=64)
    bbox_a: Optional[BBox] = None
    bbox_b: Optional[BBox] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    workspace_id: Optional[str] = None
    save_session: bool = True

    @model_validator(mode="after")
    def validate_date_range(self):
        if self.start_date and self.end_date:
            start = _parse_iso_datetime(self.start_date, "start_date")
            end = _parse_iso_datetime(self.end_date, "end_date")
            if start > end:
                raise ValueError("start_date must be <= end_date")
        return self


class TimelineRequest(BaseModel):
    bbox: Optional[BBox] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    workspace_id: Optional[str] = None
    label: Optional[str] = Field(default=None, max_length=120)

    @model_validator(mode="after")
    def validate_date_range(self):
        if self.start_date and self.end_date:
            start = _parse_iso_datetime(self.start_date, "start_date")
            end = _parse_iso_datetime(self.end_date, "end_date")
            if start > end:
                raise ValueError("start_date must be <= end_date")
        return self


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_study_tables(db: Session) -> None:
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS study_workspaces (
                id VARCHAR(64) PRIMARY KEY,
                user_id VARCHAR(64) NOT NULL,
                name VARCHAR(120) NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS study_notes (
                id VARCHAR(64) PRIMARY KEY,
                workspace_id VARCHAR(64) NOT NULL,
                user_id VARCHAR(64) NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS study_saved_queries (
                id VARCHAR(64) PRIMARY KEY,
                workspace_id VARCHAR(64) NOT NULL,
                user_id VARCHAR(64) NOT NULL,
                name VARCHAR(160) NOT NULL,
                query_payload TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS study_compare_sessions (
                id VARCHAR(64) PRIMARY KEY,
                workspace_id VARCHAR(64),
                user_id VARCHAR(64) NOT NULL,
                region_a VARCHAR(64) NOT NULL,
                region_b VARCHAR(64) NOT NULL,
                floats_a INTEGER NOT NULL,
                floats_b INTEGER NOT NULL,
                profiles_a INTEGER NOT NULL,
                profiles_b INTEGER NOT NULL,
                start_date VARCHAR(32),
                end_date VARCHAR(32),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS study_timeline_runs (
                id VARCHAR(64) PRIMARY KEY,
                workspace_id VARCHAR(64),
                user_id VARCHAR(64) NOT NULL,
                label VARCHAR(120),
                request_payload TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS study_workspace_versions (
                id VARCHAR(64) PRIMARY KEY,
                workspace_id VARCHAR(64) NOT NULL,
                user_id VARCHAR(64) NOT NULL,
                label VARCHAR(120),
                snapshot_hash VARCHAR(64) NOT NULL,
                snapshot_payload TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS study_workspace_members (
                id VARCHAR(64) PRIMARY KEY,
                workspace_id VARCHAR(64) NOT NULL,
                user_id VARCHAR(64) NOT NULL,
                role VARCHAR(16) NOT NULL,
                status VARCHAR(16) NOT NULL DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )
    db.commit()


def _bbox_where(prefix: str, bbox: Optional[BBox], params: Dict[str, Any]) -> str:
    if not bbox:
        return ""
    params[f"{prefix}_min_lon"] = bbox.min_lon
    params[f"{prefix}_max_lon"] = bbox.max_lon
    params[f"{prefix}_min_lat"] = bbox.min_lat
    params[f"{prefix}_max_lat"] = bbox.max_lat
    return (
        f" AND longitude BETWEEN :{prefix}_min_lon AND :{prefix}_max_lon"
        f" AND latitude BETWEEN :{prefix}_min_lat AND :{prefix}_max_lat"
    )


def _normalize_dt(value: Any) -> str:
    if value is None:
        return ""
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _aggregate_profile_timeline(rows: List[Any]) -> List[Dict[str, Any]]:
    buckets: Dict[str, int] = defaultdict(int)
    for row in rows:
        dt_raw = row[0]
        if dt_raw is None:
            continue
        dt_string = _normalize_dt(dt_raw)
        try:
            dt = datetime.fromisoformat(dt_string.replace("Z", "+00:00"))
            bucket = f"{dt.year:04d}-{dt.month:02d}"
        except Exception:
            bucket = dt_string[:7]
        buckets[bucket] += 1
    return [{"month": month, "profiles": buckets[month]} for month in sorted(buckets.keys())]


def _workspace_exists_any(db: Session, workspace_id: str) -> bool:
    row = db.execute(
        text("SELECT id FROM study_workspaces WHERE id = :workspace_id"),
        {"workspace_id": workspace_id},
    ).first()
    return bool(row)


def _get_workspace_role(db: Session, workspace_id: str, user_id: str) -> Optional[str]:
    owner_row = db.execute(
        text(
            """
            SELECT id
            FROM study_workspaces
            WHERE id = :workspace_id AND user_id = :user_id
            """
        ),
        {"workspace_id": workspace_id, "user_id": user_id},
    ).first()
    if owner_row:
        return "owner"

    member_row = db.execute(
        text(
            """
            SELECT role
            FROM study_workspace_members
            WHERE workspace_id = :workspace_id
              AND user_id = :user_id
              AND status = 'active'
            ORDER BY created_at DESC
            LIMIT 1
            """
        ),
        {"workspace_id": workspace_id, "user_id": user_id},
    ).first()
    if member_row:
        return str(member_row[0])
    return None


def _workspace_exists(db: Session, workspace_id: str, user_id: str) -> bool:
    return _get_workspace_role(db, workspace_id, user_id) is not None


def _require_workspace_role(db: Session, workspace_id: str, user_id: str, allowed_roles: List[str]) -> str:
    role = _get_workspace_role(db, workspace_id, user_id)
    if role in allowed_roles:
        return str(role)
    if _workspace_exists_any(db, workspace_id):
        raise HTTPException(status_code=403, detail="Insufficient workspace permissions")
    raise HTTPException(status_code=404, detail="Workspace not found")


def _workspace_owner_id(db: Session, workspace_id: str) -> Optional[str]:
    row = db.execute(
        text("SELECT user_id FROM study_workspaces WHERE id = :workspace_id"),
        {"workspace_id": workspace_id},
    ).first()
    if not row:
        return None
    return str(row[0])


def _resolve_auth_user(db: Session, identifier: str) -> Optional[Dict[str, Any]]:
    ident = identifier.strip().lower()
    if not ident:
        return None
    row = db.execute(
        text(
            """
            SELECT id, email, username
            FROM auth_users
            WHERE LOWER(email) = :ident OR LOWER(username) = :ident
            LIMIT 1
            """
        ),
        {"ident": ident},
    ).first()
    if not row:
        return None
    return {"id": row[0], "email": row[1], "username": row[2]}


def _safe_json_load(value: Any, fallback: Any):
    if value is None:
        return fallback
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return fallback


def _snapshot_counts(snapshot: Dict[str, Any]) -> Dict[str, int]:
    return {
        "notes": len(snapshot.get("notes", [])),
        "saved_queries": len(snapshot.get("saved_queries", [])),
        "compare_history": len(snapshot.get("compare_history", [])),
        "timeline_history": len(snapshot.get("timeline_history", [])),
    }


def _build_repro_package_response(
    snapshot: Dict[str, Any],
    workspace_id: str,
    version_meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    version_meta = version_meta or {"id": None, "label": None, "snapshot_hash": None, "created_at": None}
    generated_at = datetime.now(timezone.utc).isoformat()
    counts = _snapshot_counts(snapshot)
    citation = (
        "FloatChat Study Reproducibility Package; "
        f"workspace_id={workspace_id}; version_id={version_meta.get('id') or 'live'}; generated_at={generated_at}"
    )
    return {
        "metadata": {
            "workspace_id": workspace_id,
            "generated_at": generated_at,
            "version": version_meta,
            "counts": counts,
            "citation": citation,
            "repro_steps": [
                "Use workspace snapshot metadata and filters to rebuild analysis context.",
                "Re-run compare and timeline endpoints with saved payloads.",
                "Include citation and timestamp in reports for reproducibility.",
            ],
        },
        "snapshot": snapshot,
    }


def _build_workspace_snapshot(
    db: Session,
    workspace_id: str,
    user_id: str,
    include_notes: bool = True,
    include_queries: bool = True,
    include_compare_history: bool = True,
    include_timeline_history: bool = True,
    history_limit: int = 20,
) -> Dict[str, Any]:
    workspace_row = db.execute(
        text(
            """
            SELECT id, name, description, created_at, updated_at
            FROM study_workspaces
            WHERE id = :workspace_id AND user_id = :user_id
            """
        ),
        {"workspace_id": workspace_id, "user_id": user_id},
    ).first()
    if not workspace_row:
        raise HTTPException(status_code=404, detail="Workspace not found")

    notes: List[Dict[str, Any]] = []
    if include_notes:
        rows = db.execute(
            text(
                """
                SELECT id, content, created_at
                FROM study_notes
                WHERE workspace_id = :workspace_id AND user_id = :user_id
                ORDER BY created_at DESC
                """
            ),
            {"workspace_id": workspace_id, "user_id": user_id},
        ).fetchall()
        notes = [{"id": row[0], "content": row[1], "created_at": _normalize_dt(row[2])} for row in rows]

    saved_queries: List[Dict[str, Any]] = []
    if include_queries:
        rows = db.execute(
            text(
                """
                SELECT id, name, query_payload, created_at
                FROM study_saved_queries
                WHERE workspace_id = :workspace_id AND user_id = :user_id
                ORDER BY created_at DESC
                """
            ),
            {"workspace_id": workspace_id, "user_id": user_id},
        ).fetchall()
        saved_queries = [
            {
                "id": row[0],
                "name": row[1],
                "query_payload": _safe_json_load(row[2], {}),
                "created_at": _normalize_dt(row[3]),
            }
            for row in rows
        ]

    compare_history_rows: List[Dict[str, Any]] = []
    if include_compare_history:
        rows = db.execute(
            text(
                """
                SELECT id, region_a, region_b, floats_a, floats_b, profiles_a, profiles_b, start_date, end_date, created_at
                FROM study_compare_sessions
                WHERE workspace_id = :workspace_id AND user_id = :user_id
                ORDER BY created_at DESC
                LIMIT :history_limit
                """
            ),
            {"workspace_id": workspace_id, "user_id": user_id, "history_limit": history_limit},
        ).fetchall()
        compare_history_rows = [
            {
                "id": row[0],
                "region_a": row[1],
                "region_b": row[2],
                "floats_a": row[3],
                "floats_b": row[4],
                "profiles_a": row[5],
                "profiles_b": row[6],
                "start_date": row[7],
                "end_date": row[8],
                "created_at": _normalize_dt(row[9]),
            }
            for row in rows
        ]

    timeline_history_rows: List[Dict[str, Any]] = []
    if include_timeline_history:
        rows = db.execute(
            text(
                """
                SELECT id, label, request_payload, created_at
                FROM study_timeline_runs
                WHERE workspace_id = :workspace_id AND user_id = :user_id
                ORDER BY created_at DESC
                LIMIT :history_limit
                """
            ),
            {"workspace_id": workspace_id, "user_id": user_id, "history_limit": history_limit},
        ).fetchall()
        timeline_history_rows = [
            {
                "id": row[0],
                "label": row[1],
                "request_payload": _safe_json_load(row[2], {}),
                "created_at": _normalize_dt(row[3]),
            }
            for row in rows
        ]

    return {
        "workspace": {
            "id": workspace_row[0],
            "name": workspace_row[1],
            "description": workspace_row[2],
            "created_at": _normalize_dt(workspace_row[3]),
            "updated_at": _normalize_dt(workspace_row[4]),
        },
        "notes": notes,
        "saved_queries": saved_queries,
        "compare_history": compare_history_rows,
        "timeline_history": timeline_history_rows,
    }


def _build_python_notebook_payload(snapshot: Dict[str, Any], workspace_id: str, version_id: Optional[str]) -> Dict[str, Any]:
    workspace = snapshot.get("workspace", {})
    notes = snapshot.get("notes", [])
    saved_queries = snapshot.get("saved_queries", [])
    compare_history = snapshot.get("compare_history", [])
    timeline_history = snapshot.get("timeline_history", [])
    notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# FloatChat Study Notebook\n",
                    f"- workspace_id: `{workspace_id}`\n",
                    f"- version_id: `{version_id or 'live'}`\n",
                    f"- workspace_name: `{workspace.get('name', 'unknown')}`\n",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "import json\n",
                    "from pprint import pprint\n",
                    "\n",
                    "# Replace this with API call output when running connected workflow\n",
                    "snapshot = ",
                    json.dumps(snapshot, ensure_ascii=True),
                    "\n",
                    "pprint(snapshot['workspace'])\n",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "print('notes', len(snapshot.get('notes', [])))\n",
                    "print('saved_queries', len(snapshot.get('saved_queries', [])))\n",
                    "print('compare_history', len(snapshot.get('compare_history', [])))\n",
                    "print('timeline_history', len(snapshot.get('timeline_history', [])))\n",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# Template: replay compare requests\n",
                    "for item in snapshot.get('compare_history', [])[:5]:\n",
                    "    print(item.get('region_a'), 'vs', item.get('region_b'))\n",
                ],
            },
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "version": "3.x",
            },
            "floatchat": {
                "workspace_id": workspace_id,
                "version_id": version_id,
                "counts": {
                    "notes": len(notes),
                    "saved_queries": len(saved_queries),
                    "compare_history": len(compare_history),
                    "timeline_history": len(timeline_history),
                },
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    filename = f"floatchat_workspace_{workspace_id}_{version_id or 'live'}.ipynb"
    return {"filename": filename, "content": json.dumps(notebook, ensure_ascii=True), "format": "ipynb"}


def _build_r_script_payload(snapshot: Dict[str, Any], workspace_id: str, version_id: Optional[str]) -> Dict[str, Any]:
    escaped_snapshot = json.dumps(snapshot, ensure_ascii=True).replace("'", "\\'")
    script_lines = [
        "# FloatChat Workspace Repro Script (R)\n",
        f"workspace_id <- '{workspace_id}'\n",
        f"version_id <- '{version_id or 'live'}'\n",
        "\n",
        "# Snapshot payload embedded for reproducibility\n",
        f"snapshot_json <- '{escaped_snapshot}'\n",
        "library(jsonlite)\n",
        "snapshot <- fromJSON(snapshot_json)\n",
        "print(snapshot$workspace)\n",
        "cat('notes:', length(snapshot$notes), '\\n')\n",
        "cat('saved_queries:', length(snapshot$saved_queries), '\\n')\n",
        "\n",
        "# Template: inspect compare history\n",
        "if (!is.null(snapshot$compare_history)) {\n",
        "  print(head(snapshot$compare_history, 5))\n",
        "}\n",
    ]
    filename = f"floatchat_workspace_{workspace_id}_{version_id or 'live'}.R"
    return {"filename": filename, "content": "".join(script_lines), "format": "r_script"}


@router.get("/workspaces")
async def list_workspaces(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ensure_study_tables(db)
    rows = db.execute(
        text(
            """
            SELECT id, name, description, created_at, updated_at, role, owned
            FROM (
                SELECT
                    w.id,
                    w.name,
                    w.description,
                    w.created_at,
                    w.updated_at,
                    'owner' AS role,
                    1 AS owned
                FROM study_workspaces w
                WHERE w.user_id = :user_id

                UNION ALL

                SELECT
                    w.id,
                    w.name,
                    w.description,
                    w.created_at,
                    w.updated_at,
                    m.role AS role,
                    0 AS owned
                FROM study_workspaces w
                JOIN study_workspace_members m ON m.workspace_id = w.id
                WHERE m.user_id = :user_id
                  AND m.status = 'active'
            ) t
            ORDER BY created_at DESC
            """
        ),
        {"user_id": current_user["id"]},
    ).fetchall()
    return [
        {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "created_at": _normalize_dt(row[3]),
            "updated_at": _normalize_dt(row[4]),
            "role": row[5],
            "owned": bool(row[6]),
        }
        for row in rows
    ]


@router.post("/workspaces")
async def create_workspace(
    payload: WorkspaceCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ensure_study_tables(db)
    workspace_id = str(uuid.uuid4())
    db.execute(
        text(
            """
            INSERT INTO study_workspaces (id, user_id, name, description)
            VALUES (:id, :user_id, :name, :description)
            """
        ),
        {
            "id": workspace_id,
            "user_id": current_user["id"],
            "name": payload.name.strip(),
            "description": payload.description.strip() if payload.description else None,
        },
    )
    db.execute(
        text(
            """
            INSERT INTO study_workspace_members (id, workspace_id, user_id, role, status)
            VALUES (:id, :workspace_id, :user_id, 'owner', 'active')
            """
        ),
        {"id": str(uuid.uuid4()), "workspace_id": workspace_id, "user_id": current_user["id"]},
    )
    db.commit()
    return {"id": workspace_id, "name": payload.name.strip(), "description": payload.description}


@router.post("/workspaces/{workspace_id}/clone")
async def clone_workspace(
    workspace_id: str,
    payload: WorkspaceCloneRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ensure_study_tables(db)
    _require_workspace_role(db, workspace_id, current_user["id"], ["owner", "editor", "viewer"])
    source_row = db.execute(
        text(
            """
            SELECT id, name, description
            FROM study_workspaces
            WHERE id = :workspace_id
            """
        ),
        {"workspace_id": workspace_id},
    ).first()
    if not source_row:
        raise HTTPException(status_code=404, detail="Workspace not found")

    source_name = source_row[1]
    cloned_name = payload.name.strip() if payload.name else f"{source_name} (Copy)"
    clone_id = str(uuid.uuid4())
    db.execute(
        text(
            """
            INSERT INTO study_workspaces (id, user_id, name, description)
            VALUES (:id, :user_id, :name, :description)
            """
        ),
        {
            "id": clone_id,
            "user_id": current_user["id"],
            "name": cloned_name,
            "description": source_row[2],
        },
    )
    db.execute(
        text(
            """
            INSERT INTO study_workspace_members (id, workspace_id, user_id, role, status)
            VALUES (:id, :workspace_id, :user_id, 'owner', 'active')
            """
        ),
        {"id": str(uuid.uuid4()), "workspace_id": clone_id, "user_id": current_user["id"]},
    )

    notes_cloned = 0
    if payload.include_notes:
        source_notes = db.execute(
            text(
                """
                SELECT content
                FROM study_notes
                WHERE workspace_id = :workspace_id
                ORDER BY created_at ASC
                """
            ),
            {"workspace_id": workspace_id},
        ).fetchall()
        for row in source_notes:
            db.execute(
                text(
                    """
                    INSERT INTO study_notes (id, workspace_id, user_id, content)
                    VALUES (:id, :workspace_id, :user_id, :content)
                    """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "workspace_id": clone_id,
                    "user_id": current_user["id"],
                    "content": row[0],
                },
            )
            notes_cloned += 1

    queries_cloned = 0
    if payload.include_queries:
        source_queries = db.execute(
            text(
                """
                SELECT name, query_payload
                FROM study_saved_queries
                WHERE workspace_id = :workspace_id
                ORDER BY created_at ASC
                """
            ),
            {"workspace_id": workspace_id},
        ).fetchall()
        for row in source_queries:
            db.execute(
                text(
                    """
                    INSERT INTO study_saved_queries (id, workspace_id, user_id, name, query_payload)
                    VALUES (:id, :workspace_id, :user_id, :name, :query_payload)
                    """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "workspace_id": clone_id,
                    "user_id": current_user["id"],
                    "name": row[0],
                    "query_payload": row[1],
                },
            )
            queries_cloned += 1

    db.commit()
    return {
        "id": clone_id,
        "name": cloned_name,
        "source_workspace_id": workspace_id,
        "notes_cloned": notes_cloned,
        "queries_cloned": queries_cloned,
    }


@router.get("/workspaces/{workspace_id}/members")
async def list_workspace_members(
    workspace_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ensure_study_tables(db)
    _require_workspace_role(db, workspace_id, current_user["id"], ["owner", "editor", "viewer"])
    owner_id = _workspace_owner_id(db, workspace_id)

    member_rows = db.execute(
        text(
            """
            SELECT user_id, role, status, created_at, updated_at
            FROM study_workspace_members
            WHERE workspace_id = :workspace_id
            ORDER BY created_at ASC
            """
        ),
        {"workspace_id": workspace_id},
    ).fetchall()
    members = [
        {
            "user_id": row[0],
            "role": row[1],
            "status": row[2],
            "created_at": _normalize_dt(row[3]),
            "updated_at": _normalize_dt(row[4]),
            "is_owner": bool(owner_id and row[0] == owner_id),
        }
        for row in member_rows
    ]
    return members


@router.post("/workspaces/{workspace_id}/members")
async def add_workspace_member(
    workspace_id: str,
    payload: WorkspaceMemberInviteRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ensure_study_tables(db)
    _require_workspace_role(db, workspace_id, current_user["id"], ["owner"])
    target = _resolve_auth_user(db, payload.user_identifier)
    if not target:
        raise HTTPException(status_code=404, detail="Target user not found")

    owner_id = _workspace_owner_id(db, workspace_id)
    if owner_id and target["id"] == owner_id:
        raise HTTPException(status_code=400, detail="Workspace owner already has full access")

    db.execute(
        text(
            """
            DELETE FROM study_workspace_members
            WHERE workspace_id = :workspace_id
              AND user_id = :user_id
            """
        ),
        {"workspace_id": workspace_id, "user_id": target["id"]},
    )
    db.execute(
        text(
            """
            INSERT INTO study_workspace_members (id, workspace_id, user_id, role, status)
            VALUES (:id, :workspace_id, :user_id, :role, 'active')
            """
        ),
        {
            "id": str(uuid.uuid4()),
            "workspace_id": workspace_id,
            "user_id": target["id"],
            "role": payload.role,
        },
    )
    db.commit()
    return {
        "workspace_id": workspace_id,
        "user_id": target["id"],
        "email": target["email"],
        "username": target["username"],
        "role": payload.role,
        "status": "active",
    }


@router.patch("/workspaces/{workspace_id}/members/{member_user_id}")
async def update_workspace_member(
    workspace_id: str,
    member_user_id: str,
    payload: WorkspaceMemberUpdateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ensure_study_tables(db)
    _require_workspace_role(db, workspace_id, current_user["id"], ["owner"])
    owner_id = _workspace_owner_id(db, workspace_id)
    if owner_id and member_user_id == owner_id:
        raise HTTPException(status_code=400, detail="Owner role cannot be modified")

    result = db.execute(
        text(
            """
            UPDATE study_workspace_members
            SET role = :role, status = :status, updated_at = CURRENT_TIMESTAMP
            WHERE workspace_id = :workspace_id AND user_id = :user_id
            """
        ),
        {
            "role": payload.role,
            "status": payload.status,
            "workspace_id": workspace_id,
            "user_id": member_user_id,
        },
    )
    db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Workspace member not found")
    return {"success": True}


@router.delete("/workspaces/{workspace_id}/members/{member_user_id}")
async def remove_workspace_member(
    workspace_id: str,
    member_user_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ensure_study_tables(db)
    _require_workspace_role(db, workspace_id, current_user["id"], ["owner"])
    owner_id = _workspace_owner_id(db, workspace_id)
    if owner_id and member_user_id == owner_id:
        raise HTTPException(status_code=400, detail="Owner cannot be removed")

    result = db.execute(
        text(
            """
            DELETE FROM study_workspace_members
            WHERE workspace_id = :workspace_id AND user_id = :user_id
            """
        ),
        {"workspace_id": workspace_id, "user_id": member_user_id},
    )
    db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Workspace member not found")
    return {"success": True}


@router.patch("/workspaces/{workspace_id}")
async def update_workspace(
    workspace_id: str,
    payload: WorkspaceUpdateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ensure_study_tables(db)
    _require_workspace_role(db, workspace_id, current_user["id"], ["owner", "editor"])

    if payload.name is not None:
        db.execute(
            text(
                """
                UPDATE study_workspaces
                SET name = :name, updated_at = CURRENT_TIMESTAMP
                WHERE id = :workspace_id AND user_id = :user_id
                """
            ),
            {"name": payload.name.strip(), "workspace_id": workspace_id, "user_id": current_user["id"]},
        )
    if payload.description is not None:
        db.execute(
            text(
                """
                UPDATE study_workspaces
                SET description = :description, updated_at = CURRENT_TIMESTAMP
                WHERE id = :workspace_id AND user_id = :user_id
                """
            ),
            {
                "description": payload.description.strip() if payload.description else None,
                "workspace_id": workspace_id,
                "user_id": current_user["id"],
            },
        )
    db.commit()
    return {"success": True}


@router.delete("/workspaces/{workspace_id}")
async def delete_workspace(
    workspace_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ensure_study_tables(db)
    _require_workspace_role(db, workspace_id, current_user["id"], ["owner"])

    db.execute(
        text("DELETE FROM study_notes WHERE workspace_id = :workspace_id AND user_id = :user_id"),
        {"workspace_id": workspace_id, "user_id": current_user["id"]},
    )
    db.execute(
        text("DELETE FROM study_saved_queries WHERE workspace_id = :workspace_id AND user_id = :user_id"),
        {"workspace_id": workspace_id, "user_id": current_user["id"]},
    )
    db.execute(
        text("DELETE FROM study_compare_sessions WHERE workspace_id = :workspace_id AND user_id = :user_id"),
        {"workspace_id": workspace_id, "user_id": current_user["id"]},
    )
    db.execute(
        text("DELETE FROM study_timeline_runs WHERE workspace_id = :workspace_id AND user_id = :user_id"),
        {"workspace_id": workspace_id, "user_id": current_user["id"]},
    )
    db.execute(
        text("DELETE FROM study_workspace_versions WHERE workspace_id = :workspace_id"),
        {"workspace_id": workspace_id},
    )
    db.execute(
        text("DELETE FROM study_workspace_members WHERE workspace_id = :workspace_id"),
        {"workspace_id": workspace_id},
    )
    db.execute(
        text("DELETE FROM study_workspaces WHERE id = :workspace_id AND user_id = :user_id"),
        {"workspace_id": workspace_id, "user_id": current_user["id"]},
    )
    db.commit()
    return {"success": True}


@router.get("/workspaces/{workspace_id}/notes")
async def list_notes(
    workspace_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ensure_study_tables(db)
    _require_workspace_role(db, workspace_id, current_user["id"], ["owner", "editor"])

    rows = db.execute(
        text(
            """
            SELECT id, content, created_at
            FROM study_notes
            WHERE workspace_id = :workspace_id AND user_id = :user_id
            ORDER BY created_at DESC
            """
        ),
        {"workspace_id": workspace_id, "user_id": current_user["id"]},
    ).fetchall()
    return [{"id": row[0], "content": row[1], "created_at": _normalize_dt(row[2])} for row in rows]


@router.get("/workspaces/{workspace_id}/notes/search")
async def search_notes(
    workspace_id: str,
    q: str = Query(..., min_length=1, max_length=120),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ensure_study_tables(db)
    _require_workspace_role(db, workspace_id, current_user["id"], ["owner", "editor"])

    rows = db.execute(
        text(
            """
            SELECT id, content, created_at
            FROM study_notes
            WHERE workspace_id = :workspace_id
              AND user_id = :user_id
              AND LOWER(content) LIKE :needle
            ORDER BY created_at DESC
            LIMIT :limit
            """
        ),
        {
            "workspace_id": workspace_id,
            "user_id": current_user["id"],
            "needle": f"%{q.strip().lower()}%",
            "limit": limit,
        },
    ).fetchall()
    return [{"id": row[0], "content": row[1], "created_at": _normalize_dt(row[2])} for row in rows]


@router.post("/workspaces/{workspace_id}/notes")
async def create_note(
    workspace_id: str,
    payload: NoteCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ensure_study_tables(db)
    _require_workspace_role(db, workspace_id, current_user["id"], ["owner", "editor"])

    note_id = str(uuid.uuid4())
    db.execute(
        text(
            """
            INSERT INTO study_notes (id, workspace_id, user_id, content)
            VALUES (:id, :workspace_id, :user_id, :content)
            """
        ),
        {"id": note_id, "workspace_id": workspace_id, "user_id": current_user["id"], "content": payload.content.strip()},
    )
    db.commit()
    return {"id": note_id, "content": payload.content.strip()}


@router.get("/workspaces/{workspace_id}/dashboard")
async def workspace_dashboard(
    workspace_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ensure_study_tables(db)
    if not _workspace_exists(db, workspace_id, current_user["id"]):
        raise HTTPException(status_code=404, detail="Workspace not found")

    workspace_row = db.execute(
        text(
            """
            SELECT id, name, description, created_at, updated_at
            FROM study_workspaces
            WHERE id = :workspace_id AND user_id = :user_id
            """
        ),
        {"workspace_id": workspace_id, "user_id": current_user["id"]},
    ).first()

    notes_count = int(
        db.execute(
            text("SELECT COUNT(*) FROM study_notes WHERE workspace_id = :workspace_id AND user_id = :user_id"),
            {"workspace_id": workspace_id, "user_id": current_user["id"]},
        ).scalar()
        or 0
    )
    query_count = int(
        db.execute(
            text(
                "SELECT COUNT(*) FROM study_saved_queries WHERE workspace_id = :workspace_id AND user_id = :user_id"
            ),
            {"workspace_id": workspace_id, "user_id": current_user["id"]},
        ).scalar()
        or 0
    )
    compare_count = int(
        db.execute(
            text(
                "SELECT COUNT(*) FROM study_compare_sessions WHERE workspace_id = :workspace_id AND user_id = :user_id"
            ),
            {"workspace_id": workspace_id, "user_id": current_user["id"]},
        ).scalar()
        or 0
    )
    timeline_count = int(
        db.execute(
            text("SELECT COUNT(*) FROM study_timeline_runs WHERE workspace_id = :workspace_id AND user_id = :user_id"),
            {"workspace_id": workspace_id, "user_id": current_user["id"]},
        ).scalar()
        or 0
    )
    version_count = int(
        db.execute(
            text(
                "SELECT COUNT(*) FROM study_workspace_versions WHERE workspace_id = :workspace_id"
            ),
            {"workspace_id": workspace_id},
        ).scalar()
        or 0
    )

    recent_notes = db.execute(
        text(
            """
            SELECT id, content, created_at
            FROM study_notes
            WHERE workspace_id = :workspace_id AND user_id = :user_id
            ORDER BY created_at DESC
            LIMIT 5
            """
        ),
        {"workspace_id": workspace_id, "user_id": current_user["id"]},
    ).fetchall()

    recent_queries = db.execute(
        text(
            """
            SELECT id, name, created_at
            FROM study_saved_queries
            WHERE workspace_id = :workspace_id AND user_id = :user_id
            ORDER BY created_at DESC
            LIMIT 5
            """
        ),
        {"workspace_id": workspace_id, "user_id": current_user["id"]},
    ).fetchall()

    latest_compare = db.execute(
        text(
            """
            SELECT created_at, region_a, region_b, delta_profiles
            FROM (
                SELECT
                    created_at,
                    region_a,
                    region_b,
                    (profiles_a - profiles_b) AS delta_profiles
                FROM study_compare_sessions
                WHERE workspace_id = :workspace_id AND user_id = :user_id
                ORDER BY created_at DESC
                LIMIT 1
            ) t
            """
        ),
        {"workspace_id": workspace_id, "user_id": current_user["id"]},
    ).first()

    latest_timeline = db.execute(
        text(
            """
            SELECT created_at, label
            FROM study_timeline_runs
            WHERE workspace_id = :workspace_id AND user_id = :user_id
            ORDER BY created_at DESC
            LIMIT 1
            """
        ),
        {"workspace_id": workspace_id, "user_id": current_user["id"]},
    ).first()

    return {
        "workspace": {
            "id": workspace_row[0],
            "name": workspace_row[1],
            "description": workspace_row[2],
            "created_at": _normalize_dt(workspace_row[3]),
            "updated_at": _normalize_dt(workspace_row[4]),
        },
        "counts": {
            "notes": notes_count,
            "saved_queries": query_count,
            "compare_sessions": compare_count,
            "timeline_runs": timeline_count,
            "versions": version_count,
        },
        "recent_notes": [
            {"id": row[0], "content": row[1], "created_at": _normalize_dt(row[2])}
            for row in recent_notes
        ],
        "recent_queries": [
            {"id": row[0], "name": row[1], "created_at": _normalize_dt(row[2])}
            for row in recent_queries
        ],
        "latest_compare": (
            {
                "created_at": _normalize_dt(latest_compare[0]),
                "region_a": latest_compare[1],
                "region_b": latest_compare[2],
                "delta_profiles": latest_compare[3],
            }
            if latest_compare
            else None
        ),
        "latest_timeline": (
            {
                "created_at": _normalize_dt(latest_timeline[0]),
                "label": latest_timeline[1],
            }
            if latest_timeline
            else None
        ),
    }


@router.get("/workspaces/{workspace_id}/snapshot")
async def workspace_snapshot(
    workspace_id: str,
    include_notes: bool = Query(default=True),
    include_queries: bool = Query(default=True),
    include_compare_history: bool = Query(default=True),
    include_timeline_history: bool = Query(default=True),
    history_limit: int = Query(default=20, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ensure_study_tables(db)
    _require_workspace_role(db, workspace_id, current_user["id"], ["owner", "editor", "viewer"])
    return _build_workspace_snapshot(
        db=db,
        workspace_id=workspace_id,
        user_id=current_user["id"],
        include_notes=include_notes,
        include_queries=include_queries,
        include_compare_history=include_compare_history,
        include_timeline_history=include_timeline_history,
        history_limit=history_limit,
    )


@router.post("/workspaces/{workspace_id}/versions")
async def create_workspace_version(
    workspace_id: str,
    payload: WorkspaceVersionCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ensure_study_tables(db)
    _require_workspace_role(db, workspace_id, current_user["id"], ["owner", "editor"])
    snapshot = _build_workspace_snapshot(
        db=db,
        workspace_id=workspace_id,
        user_id=current_user["id"],
        include_notes=payload.include_notes,
        include_queries=payload.include_queries,
        include_compare_history=payload.include_compare_history,
        include_timeline_history=payload.include_timeline_history,
        history_limit=payload.history_limit,
    )

    snapshot_payload = json.dumps(snapshot, ensure_ascii=True)
    snapshot_hash = hashlib.sha256(snapshot_payload.encode("utf-8")).hexdigest()
    version_id = str(uuid.uuid4())
    db.execute(
        text(
            """
            INSERT INTO study_workspace_versions (id, workspace_id, user_id, label, snapshot_hash, snapshot_payload)
            VALUES (:id, :workspace_id, :user_id, :label, :snapshot_hash, :snapshot_payload)
            """
        ),
        {
            "id": version_id,
            "workspace_id": workspace_id,
            "user_id": current_user["id"],
            "label": payload.label.strip() if payload.label else None,
            "snapshot_hash": snapshot_hash,
            "snapshot_payload": snapshot_payload,
        },
    )
    db.commit()
    return {
        "id": version_id,
        "workspace_id": workspace_id,
        "label": payload.label.strip() if payload.label else None,
        "snapshot_hash": snapshot_hash,
        "counts": _snapshot_counts(snapshot),
    }


@router.get("/workspaces/{workspace_id}/versions")
async def list_workspace_versions(
    workspace_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ensure_study_tables(db)
    _require_workspace_role(db, workspace_id, current_user["id"], ["owner", "editor", "viewer"])

    rows = db.execute(
        text(
            """
            SELECT id, label, snapshot_hash, snapshot_payload, created_at
            FROM study_workspace_versions
            WHERE workspace_id = :workspace_id
            ORDER BY created_at DESC
            LIMIT :limit
            """
        ),
        {"workspace_id": workspace_id, "limit": limit},
    ).fetchall()

    response = []
    for row in rows:
        snapshot = _safe_json_load(row[3], {})
        response.append(
            {
                "id": row[0],
                "label": row[1],
                "snapshot_hash": row[2],
                "created_at": _normalize_dt(row[4]),
                "counts": _snapshot_counts(snapshot),
            }
        )
    return response


@router.get("/workspaces/{workspace_id}/versions/{version_id}")
async def get_workspace_version(
    workspace_id: str,
    version_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ensure_study_tables(db)
    _require_workspace_role(db, workspace_id, current_user["id"], ["owner", "editor", "viewer"])
    row = db.execute(
        text(
            """
            SELECT id, label, snapshot_hash, snapshot_payload, created_at
            FROM study_workspace_versions
            WHERE id = :version_id AND workspace_id = :workspace_id
            """
        ),
        {"version_id": version_id, "workspace_id": workspace_id},
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Workspace version not found")

    snapshot = _safe_json_load(row[3], {})
    return {
        "id": row[0],
        "workspace_id": workspace_id,
        "label": row[1],
        "snapshot_hash": row[2],
        "created_at": _normalize_dt(row[4]),
        "counts": _snapshot_counts(snapshot),
        "snapshot": snapshot,
    }


@router.post("/workspaces/{workspace_id}/versions/{version_id}/restore")
async def restore_workspace_version(
    workspace_id: str,
    version_id: str,
    payload: WorkspaceVersionRestoreRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ensure_study_tables(db)
    _require_workspace_role(db, workspace_id, current_user["id"], ["owner", "editor"])

    row = db.execute(
        text(
            """
            SELECT snapshot_payload
            FROM study_workspace_versions
            WHERE id = :version_id AND workspace_id = :workspace_id
            """
        ),
        {"version_id": version_id, "workspace_id": workspace_id},
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Workspace version not found")

    snapshot = _safe_json_load(row[0], {})
    notes = snapshot.get("notes", [])
    saved_queries = snapshot.get("saved_queries", [])
    compare_history = snapshot.get("compare_history", [])
    timeline_history = snapshot.get("timeline_history", [])
    planned = {
        "notes": len(notes) if payload.restore_notes else 0,
        "saved_queries": len(saved_queries) if payload.restore_queries else 0,
        "compare_history": len(compare_history) if payload.restore_compare_history else 0,
        "timeline_history": len(timeline_history) if payload.restore_timeline_history else 0,
    }

    if payload.dry_run:
        return {
            "success": True,
            "dry_run": True,
            "mode": payload.mode,
            "workspace_id": workspace_id,
            "version_id": version_id,
            "planned_restore": planned,
        }

    try:
        if payload.restore_notes:
            db.execute(
                text("DELETE FROM study_notes WHERE workspace_id = :workspace_id AND user_id = :user_id"),
                {"workspace_id": workspace_id, "user_id": current_user["id"]},
            )
            for note in notes:
                db.execute(
                    text(
                        """
                        INSERT INTO study_notes (id, workspace_id, user_id, content, created_at)
                        VALUES (:id, :workspace_id, :user_id, :content, :created_at)
                        """
                    ),
                    {
                        "id": str(uuid.uuid4()),
                        "workspace_id": workspace_id,
                        "user_id": current_user["id"],
                        "content": str(note.get("content", ""))[:5000],
                        "created_at": note.get("created_at"),
                    },
                )

        if payload.restore_queries:
            db.execute(
                text("DELETE FROM study_saved_queries WHERE workspace_id = :workspace_id AND user_id = :user_id"),
                {"workspace_id": workspace_id, "user_id": current_user["id"]},
            )
            for saved_query in saved_queries:
                db.execute(
                    text(
                        """
                        INSERT INTO study_saved_queries (id, workspace_id, user_id, name, query_payload, created_at)
                        VALUES (:id, :workspace_id, :user_id, :name, :query_payload, :created_at)
                        """
                    ),
                    {
                        "id": str(uuid.uuid4()),
                        "workspace_id": workspace_id,
                        "user_id": current_user["id"],
                        "name": str(saved_query.get("name", "Recovered Query"))[:160],
                        "query_payload": json.dumps(_safe_json_load(saved_query.get("query_payload"), {}), ensure_ascii=True),
                        "created_at": saved_query.get("created_at"),
                    },
                )

        if payload.restore_compare_history:
            db.execute(
                text("DELETE FROM study_compare_sessions WHERE workspace_id = :workspace_id AND user_id = :user_id"),
                {"workspace_id": workspace_id, "user_id": current_user["id"]},
            )
            for compare in compare_history:
                db.execute(
                    text(
                        """
                        INSERT INTO study_compare_sessions (
                            id, workspace_id, user_id, region_a, region_b, floats_a, floats_b, profiles_a, profiles_b,
                            start_date, end_date, created_at
                        )
                        VALUES (
                            :id, :workspace_id, :user_id, :region_a, :region_b, :floats_a, :floats_b, :profiles_a, :profiles_b,
                            :start_date, :end_date, :created_at
                        )
                        """
                    ),
                    {
                        "id": str(uuid.uuid4()),
                        "workspace_id": workspace_id,
                        "user_id": current_user["id"],
                        "region_a": str(compare.get("region_a", "unknown"))[:64],
                        "region_b": str(compare.get("region_b", "unknown"))[:64],
                        "floats_a": int(compare.get("floats_a") or 0),
                        "floats_b": int(compare.get("floats_b") or 0),
                        "profiles_a": int(compare.get("profiles_a") or 0),
                        "profiles_b": int(compare.get("profiles_b") or 0),
                        "start_date": compare.get("start_date"),
                        "end_date": compare.get("end_date"),
                        "created_at": compare.get("created_at"),
                    },
                )

        if payload.restore_timeline_history:
            db.execute(
                text("DELETE FROM study_timeline_runs WHERE workspace_id = :workspace_id AND user_id = :user_id"),
                {"workspace_id": workspace_id, "user_id": current_user["id"]},
            )
            for timeline in timeline_history:
                db.execute(
                    text(
                        """
                        INSERT INTO study_timeline_runs (id, workspace_id, user_id, label, request_payload, created_at)
                        VALUES (:id, :workspace_id, :user_id, :label, :request_payload, :created_at)
                        """
                    ),
                    {
                        "id": str(uuid.uuid4()),
                        "workspace_id": workspace_id,
                        "user_id": current_user["id"],
                        "label": str(timeline.get("label", ""))[:120] or None,
                        "request_payload": json.dumps(_safe_json_load(timeline.get("request_payload"), {}), ensure_ascii=True),
                        "created_at": timeline.get("created_at"),
                    },
                )

        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to restore workspace version: {exc}") from exc

    return {
        "success": True,
        "dry_run": False,
        "mode": payload.mode,
        "workspace_id": workspace_id,
        "version_id": version_id,
        "restored": planned,
    }


@router.get("/workspaces/{workspace_id}/repro-package")
async def workspace_repro_package(
    workspace_id: str,
    version_id: Optional[str] = Query(default=None),
    include_notes: bool = Query(default=True),
    include_queries: bool = Query(default=True),
    include_compare_history: bool = Query(default=True),
    include_timeline_history: bool = Query(default=True),
    history_limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ensure_study_tables(db)
    _require_workspace_role(db, workspace_id, current_user["id"], ["owner", "editor", "viewer"])

    snapshot: Dict[str, Any]
    version_meta: Dict[str, Any] = {"id": None, "label": None, "snapshot_hash": None, "created_at": None}
    if version_id:
        row = db.execute(
            text(
                """
                SELECT id, label, snapshot_hash, snapshot_payload, created_at
                FROM study_workspace_versions
                WHERE id = :version_id AND workspace_id = :workspace_id
                """
            ),
            {"version_id": version_id, "workspace_id": workspace_id},
        ).first()
        if not row:
            raise HTTPException(status_code=404, detail="Workspace version not found")
        snapshot = _safe_json_load(row[3], {})
        version_meta = {
            "id": row[0],
            "label": row[1],
            "snapshot_hash": row[2],
            "created_at": _normalize_dt(row[4]),
        }
    else:
        snapshot = _build_workspace_snapshot(
            db=db,
            workspace_id=workspace_id,
            user_id=current_user["id"],
            include_notes=include_notes,
            include_queries=include_queries,
            include_compare_history=include_compare_history,
            include_timeline_history=include_timeline_history,
            history_limit=history_limit,
        )

    return _build_repro_package_response(snapshot=snapshot, workspace_id=workspace_id, version_meta=version_meta)


@router.get("/workspaces/{workspace_id}/notebook-template")
async def workspace_notebook_template(
    workspace_id: str,
    language: Literal["python", "r"] = Query(default="python"),
    version_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ensure_study_tables(db)
    _require_workspace_role(db, workspace_id, current_user["id"], ["owner", "editor", "viewer"])
    snapshot: Dict[str, Any]
    if version_id:
        row = db.execute(
            text(
                """
                SELECT snapshot_payload
                FROM study_workspace_versions
                WHERE id = :version_id AND workspace_id = :workspace_id
                """
            ),
            {"version_id": version_id, "workspace_id": workspace_id},
        ).first()
        if not row:
            raise HTTPException(status_code=404, detail="Workspace version not found")
        snapshot = _safe_json_load(row[0], {})
    else:
        snapshot = _build_workspace_snapshot(
            db=db,
            workspace_id=workspace_id,
            user_id=current_user["id"],
            include_notes=True,
            include_queries=True,
            include_compare_history=True,
            include_timeline_history=True,
            history_limit=100,
        )

    if language == "python":
        payload = _build_python_notebook_payload(snapshot=snapshot, workspace_id=workspace_id, version_id=version_id)
    else:
        payload = _build_r_script_payload(snapshot=snapshot, workspace_id=workspace_id, version_id=version_id)

    return {
        "workspace_id": workspace_id,
        "version_id": version_id,
        "language": language,
        **payload,
    }


@router.post("/workspaces/{workspace_id}/repro-package/jobs")
async def queue_workspace_repro_package_job(
    workspace_id: str,
    payload: ReproPackageJobRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ensure_study_tables(db)
    if not _workspace_exists(db, workspace_id, current_user["id"]):
        raise HTTPException(status_code=404, detail="Workspace not found")

    queue = get_job_queue()
    job_payload = {
        "workspace_id": workspace_id,
        "user_id": current_user["id"],
        "version_id": payload.version_id,
    }

    def _job_handler(job_data: Dict[str, Any], progress: Any) -> Dict[str, Any]:
        progress(10, "Preparing workspace snapshot")
        session = SessionLocal()
        try:
            version_meta = {"id": None, "label": None, "snapshot_hash": None, "created_at": None}
            snapshot: Dict[str, Any]
            version_id = job_data.get("version_id")
            if version_id:
                row = session.execute(
                    text(
                        """
                        SELECT id, label, snapshot_hash, snapshot_payload, created_at
                        FROM study_workspace_versions
                        WHERE id = :version_id AND workspace_id = :workspace_id
                        """
                    ),
                    {
                        "version_id": version_id,
                        "workspace_id": job_data["workspace_id"],
                    },
                ).first()
                if not row:
                    raise RuntimeError("Workspace version not found for async repro package")
                snapshot = _safe_json_load(row[3], {})
                version_meta = {
                    "id": row[0],
                    "label": row[1],
                    "snapshot_hash": row[2],
                    "created_at": _normalize_dt(row[4]),
                }
            else:
                snapshot = _build_workspace_snapshot(
                    db=session,
                    workspace_id=job_data["workspace_id"],
                    user_id=job_data["user_id"],
                    include_notes=True,
                    include_queries=True,
                    include_compare_history=True,
                    include_timeline_history=True,
                    history_limit=200,
                )

            progress(65, "Building repro package")
            package = _build_repro_package_response(
                snapshot=snapshot,
                workspace_id=job_data["workspace_id"],
                version_meta=version_meta,
            )
            progress(95, "Finalizing")
            return package
        finally:
            session.close()

    job = queue.submit("study.repro_package", job_payload, _job_handler)
    return job


@router.get("/workspaces/{workspace_id}/jobs")
async def list_workspace_jobs(
    workspace_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ensure_study_tables(db)
    if not _workspace_exists(db, workspace_id, current_user["id"]):
        raise HTTPException(status_code=404, detail="Workspace not found")
    jobs = get_job_queue().list(limit=limit)
    filtered = [
        job
        for job in jobs
        if (job.get("payload_meta") or {}).get("workspace_id") == workspace_id
        and (job.get("payload_meta") or {}).get("user_id") == current_user["id"]
    ]
    return filtered


@router.get("/workspaces/{workspace_id}/jobs/{job_id}")
async def get_workspace_job(
    workspace_id: str,
    job_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ensure_study_tables(db)
    if not _workspace_exists(db, workspace_id, current_user["id"]):
        raise HTTPException(status_code=404, detail="Workspace not found")
    job = get_job_queue().get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    payload_meta = job.get("payload_meta") or {}
    if payload_meta.get("workspace_id") != workspace_id or payload_meta.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.delete("/notes/{note_id}")
async def delete_note(
    note_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ensure_study_tables(db)
    result = db.execute(
        text("DELETE FROM study_notes WHERE id = :note_id AND user_id = :user_id"),
        {"note_id": note_id, "user_id": current_user["id"]},
    )
    db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"success": True}


@router.get("/workspaces/{workspace_id}/queries")
async def list_saved_queries(
    workspace_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ensure_study_tables(db)
    if not _workspace_exists(db, workspace_id, current_user["id"]):
        raise HTTPException(status_code=404, detail="Workspace not found")

    rows = db.execute(
        text(
            """
            SELECT id, name, query_payload, created_at
            FROM study_saved_queries
            WHERE workspace_id = :workspace_id AND user_id = :user_id
            ORDER BY created_at DESC
            """
        ),
        {"workspace_id": workspace_id, "user_id": current_user["id"]},
    ).fetchall()
    return [
        {
            "id": row[0],
            "name": row[1],
            "query_payload": json.loads(row[2]),
            "created_at": _normalize_dt(row[3]),
        }
        for row in rows
    ]


@router.post("/workspaces/{workspace_id}/queries")
async def create_saved_query(
    workspace_id: str,
    payload: SavedQueryCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ensure_study_tables(db)
    if not _workspace_exists(db, workspace_id, current_user["id"]):
        raise HTTPException(status_code=404, detail="Workspace not found")

    query_id = str(uuid.uuid4())
    db.execute(
        text(
            """
            INSERT INTO study_saved_queries (id, workspace_id, user_id, name, query_payload)
            VALUES (:id, :workspace_id, :user_id, :name, :query_payload)
            """
        ),
        {
            "id": query_id,
            "workspace_id": workspace_id,
            "user_id": current_user["id"],
            "name": payload.name.strip(),
            "query_payload": json.dumps(payload.query_payload, ensure_ascii=True),
        },
    )
    db.commit()
    return {"id": query_id, "name": payload.name.strip(), "query_payload": payload.query_payload}


def _count_floats_and_profiles(
    db: Session,
    bbox: Optional[BBox],
    start_date: Optional[str],
    end_date: Optional[str],
) -> Dict[str, int]:
    params: Dict[str, Any] = {}
    float_query = "SELECT COUNT(*) FROM argo_floats WHERE 1=1"
    if bbox:
        float_query += " AND last_longitude BETWEEN :min_lon AND :max_lon AND last_latitude BETWEEN :min_lat AND :max_lat"
        params.update(
            {"min_lon": bbox.min_lon, "max_lon": bbox.max_lon, "min_lat": bbox.min_lat, "max_lat": bbox.max_lat}
        )
    if start_date:
        float_query += " AND last_location_date >= :start_date"
        params["start_date"] = start_date
    if end_date:
        float_query += " AND last_location_date <= :end_date"
        params["end_date"] = end_date
    floats_count = int(db.execute(text(float_query), params).scalar() or 0)

    profile_params: Dict[str, Any] = {}
    profile_query = "SELECT COUNT(*) FROM argo_profiles WHERE 1=1"
    profile_query += _bbox_where("bbox", bbox, profile_params)
    if start_date:
        profile_query += " AND profile_date >= :start_date"
        profile_params["start_date"] = start_date
    if end_date:
        profile_query += " AND profile_date <= :end_date"
        profile_params["end_date"] = end_date
    profiles_count = int(db.execute(text(profile_query), profile_params).scalar() or 0)

    return {"floats": floats_count, "profiles": profiles_count}


def _safe_std(count: int, mean: Optional[float], mean_sq: Optional[float]) -> Optional[float]:
    if count <= 1 or mean is None or mean_sq is None:
        return None
    variance = max(0.0, float(mean_sq) - float(mean) * float(mean))
    return math.sqrt(variance)


def _measurement_stats(
    db: Session,
    bbox: Optional[BBox],
    start_date: Optional[str],
    end_date: Optional[str],
) -> Dict[str, Optional[float]]:
    params: Dict[str, Any] = {}
    query = """
        SELECT
            COUNT(m.temperature) AS temp_count,
            AVG(m.temperature) AS temp_mean,
            AVG(m.temperature * m.temperature) AS temp_mean_sq,
            COUNT(m.salinity) AS sal_count,
            AVG(m.salinity) AS sal_mean,
            AVG(m.salinity * m.salinity) AS sal_mean_sq
        FROM argo_measurements m
        JOIN argo_profiles p ON m.profile_id = p.id
        WHERE 1=1
    """
    query += _bbox_where("stats_bbox", bbox, params)
    if start_date:
        query += " AND p.profile_date >= :start_date"
        params["start_date"] = start_date
    if end_date:
        query += " AND p.profile_date <= :end_date"
        params["end_date"] = end_date

    row = db.execute(text(query), params).first()
    temp_count = int(row[0] or 0)
    temp_mean = float(row[1]) if row[1] is not None else None
    temp_mean_sq = float(row[2]) if row[2] is not None else None
    sal_count = int(row[3] or 0)
    sal_mean = float(row[4]) if row[4] is not None else None
    sal_mean_sq = float(row[5]) if row[5] is not None else None

    return {
        "temperature_count": temp_count,
        "temperature_mean": temp_mean,
        "temperature_std": _safe_std(temp_count, temp_mean, temp_mean_sq),
        "salinity_count": sal_count,
        "salinity_mean": sal_mean,
        "salinity_std": _safe_std(sal_count, sal_mean, sal_mean_sq),
    }


def _compare_metric_stats(
    metric_name: str,
    count_a: int,
    mean_a: Optional[float],
    std_a: Optional[float],
    count_b: int,
    mean_b: Optional[float],
    std_b: Optional[float],
) -> Dict[str, Any]:
    metric_response: Dict[str, Any] = {
        "metric": metric_name,
        "available": False,
        "count_a": int(count_a),
        "count_b": int(count_b),
        "mean_a": mean_a,
        "mean_b": mean_b,
        "delta": None,
        "confidence_interval_95": None,
        "p_value_approx": None,
        "effect_size_cohen_d": None,
        "anomaly_score": None,
        "interpretation": "Insufficient data for statistical comparison.",
    }
    if not (
        count_a >= 2
        and count_b >= 2
        and mean_a is not None
        and mean_b is not None
        and std_a is not None
        and std_b is not None
    ):
        return metric_response

    delta = float(mean_a) - float(mean_b)
    se = math.sqrt((float(std_a) ** 2 / count_a) + (float(std_b) ** 2 / count_b))
    z_score = delta / se if se > 0 else 0.0
    p_value = float(math.erfc(abs(z_score) / math.sqrt(2.0))) if se > 0 else 1.0
    ci_low = delta - 1.96 * se
    ci_high = delta + 1.96 * se
    pooled_denom = max(1, count_a + count_b - 2)
    pooled_sd = math.sqrt(
        max(
            0.0,
            (((count_a - 1) * (float(std_a) ** 2)) + ((count_b - 1) * (float(std_b) ** 2))) / pooled_denom,
        )
    )
    cohen_d = (delta / pooled_sd) if pooled_sd > 0 else 0.0
    anomaly_score = abs(z_score)

    if anomaly_score >= 3.0:
        interpretation = "Strong anomaly signal (|z| >= 3)."
    elif anomaly_score >= 2.0:
        interpretation = "Moderate anomaly signal (|z| >= 2)."
    elif anomaly_score >= 1.0:
        interpretation = "Mild anomaly signal (|z| >= 1)."
    else:
        interpretation = "Low anomaly signal."

    metric_response.update(
        {
            "available": True,
            "delta": round(delta, 6),
            "confidence_interval_95": {
                "lower": round(ci_low, 6),
                "upper": round(ci_high, 6),
            },
            "p_value_approx": round(p_value, 6),
            "effect_size_cohen_d": round(cohen_d, 6),
            "anomaly_score": round(anomaly_score, 6),
            "interpretation": interpretation,
        }
    )
    return metric_response


@router.post("/compare/run")
async def run_compare(
    payload: CompareRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ensure_study_tables(db)
    if payload.workspace_id:
        _require_workspace_role(db, payload.workspace_id, current_user["id"], ["owner", "editor"])

    metrics_a = _count_floats_and_profiles(db, payload.bbox_a, payload.start_date, payload.end_date)
    metrics_b = _count_floats_and_profiles(db, payload.bbox_b, payload.start_date, payload.end_date)
    measurement_a = _measurement_stats(db, payload.bbox_a, payload.start_date, payload.end_date)
    measurement_b = _measurement_stats(db, payload.bbox_b, payload.start_date, payload.end_date)
    temperature_stats = _compare_metric_stats(
        "temperature",
        int(measurement_a.get("temperature_count") or 0),
        measurement_a.get("temperature_mean"),
        measurement_a.get("temperature_std"),
        int(measurement_b.get("temperature_count") or 0),
        measurement_b.get("temperature_mean"),
        measurement_b.get("temperature_std"),
    )
    salinity_stats = _compare_metric_stats(
        "salinity",
        int(measurement_a.get("salinity_count") or 0),
        measurement_a.get("salinity_mean"),
        measurement_a.get("salinity_std"),
        int(measurement_b.get("salinity_count") or 0),
        measurement_b.get("salinity_mean"),
        measurement_b.get("salinity_std"),
    )

    result = {
        "region_a": payload.region_a,
        "region_b": payload.region_b,
        "floats_a": metrics_a["floats"],
        "floats_b": metrics_b["floats"],
        "profiles_a": metrics_a["profiles"],
        "profiles_b": metrics_b["profiles"],
        "delta_floats": metrics_a["floats"] - metrics_b["floats"],
        "delta_profiles": metrics_a["profiles"] - metrics_b["profiles"],
        "statistics": {
            "temperature": temperature_stats,
            "salinity": salinity_stats,
        },
    }
    insights: List[str] = []
    if metrics_b["floats"] > 0:
        ratio = round(metrics_a["floats"] / metrics_b["floats"], 3)
        insights.append(f"Float coverage ratio (A/B) is {ratio}.")
    if metrics_b["profiles"] > 0:
        profile_ratio = round(metrics_a["profiles"] / metrics_b["profiles"], 3)
        insights.append(f"Profile density ratio (A/B) is {profile_ratio}.")
    if temperature_stats.get("available"):
        p_value = float(temperature_stats.get("p_value_approx") or 1.0)
        if p_value < 0.05:
            insights.append("Temperature difference appears statistically significant (approx p < 0.05).")
        else:
            insights.append("Temperature difference is not statistically strong (approx p >= 0.05).")
    if salinity_stats.get("available"):
        p_value = float(salinity_stats.get("p_value_approx") or 1.0)
        if p_value < 0.05:
            insights.append("Salinity difference appears statistically significant (approx p < 0.05).")
        else:
            insights.append("Salinity difference is not statistically strong (approx p >= 0.05).")
    if not insights:
        insights.append("Baseline comparison complete; one or both regions have zero baseline counts.")
    result["insights"] = insights

    if payload.save_session:
        session_id = str(uuid.uuid4())
        db.execute(
            text(
                """
                INSERT INTO study_compare_sessions (
                    id, workspace_id, user_id, region_a, region_b,
                    floats_a, floats_b, profiles_a, profiles_b, start_date, end_date
                )
                VALUES (
                    :id, :workspace_id, :user_id, :region_a, :region_b,
                    :floats_a, :floats_b, :profiles_a, :profiles_b, :start_date, :end_date
                )
                """
            ),
            {
                "id": session_id,
                "workspace_id": payload.workspace_id,
                "user_id": current_user["id"],
                "region_a": payload.region_a,
                "region_b": payload.region_b,
                "floats_a": metrics_a["floats"],
                "floats_b": metrics_b["floats"],
                "profiles_a": metrics_a["profiles"],
                "profiles_b": metrics_b["profiles"],
                "start_date": payload.start_date,
                "end_date": payload.end_date,
            },
        )
        db.commit()
        result["session_id"] = session_id

    return result


@router.get("/compare/history")
async def compare_history(
    workspace_id: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ensure_study_tables(db)
    params: Dict[str, Any] = {"limit": limit}
    query = """
        SELECT id, workspace_id, region_a, region_b, floats_a, floats_b, profiles_a, profiles_b, start_date, end_date, created_at
        FROM study_compare_sessions
        WHERE 1=1
    """
    if workspace_id:
        _require_workspace_role(db, workspace_id, current_user["id"], ["owner", "editor", "viewer"])
        query += " AND workspace_id = :workspace_id"
        params["workspace_id"] = workspace_id
    else:
        query += " AND user_id = :user_id"
        params["user_id"] = current_user["id"]
    query += " ORDER BY created_at DESC LIMIT :limit"
    rows = db.execute(text(query), params).fetchall()
    return [
        {
            "id": row[0],
            "workspace_id": row[1],
            "region_a": row[2],
            "region_b": row[3],
            "floats_a": row[4],
            "floats_b": row[5],
            "profiles_a": row[6],
            "profiles_b": row[7],
            "start_date": row[8],
            "end_date": row[9],
            "created_at": _normalize_dt(row[10]),
        }
        for row in rows
    ]


@router.post("/timeline/profiles")
async def profile_timeline(
    payload: TimelineRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ensure_study_tables(db)
    if payload.workspace_id:
        _require_workspace_role(db, payload.workspace_id, current_user["id"], ["owner", "editor"])

    params: Dict[str, Any] = {}
    query = "SELECT profile_date FROM argo_profiles WHERE 1=1"
    query += _bbox_where("bbox", payload.bbox, params)
    if payload.start_date:
        query += " AND profile_date >= :start_date"
        params["start_date"] = payload.start_date
    if payload.end_date:
        query += " AND profile_date <= :end_date"
        params["end_date"] = payload.end_date

    rows = db.execute(text(query), params).fetchall()
    series = _aggregate_profile_timeline(rows)

    run_id = str(uuid.uuid4())
    db.execute(
        text(
            """
            INSERT INTO study_timeline_runs (id, workspace_id, user_id, label, request_payload)
            VALUES (:id, :workspace_id, :user_id, :label, :request_payload)
            """
        ),
        {
            "id": run_id,
            "workspace_id": payload.workspace_id,
            "user_id": current_user["id"],
            "label": payload.label,
            "request_payload": json.dumps(payload.model_dump(), ensure_ascii=True),
        },
    )
    db.commit()

    return {"id": run_id, "series": series, "points": len(series)}


@router.get("/timeline/history")
async def timeline_history(
    workspace_id: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ensure_study_tables(db)
    params: Dict[str, Any] = {"limit": limit}
    query = """
        SELECT id, workspace_id, label, request_payload, created_at
        FROM study_timeline_runs
        WHERE 1=1
    """
    if workspace_id:
        _require_workspace_role(db, workspace_id, current_user["id"], ["owner", "editor", "viewer"])
        query += " AND workspace_id = :workspace_id"
        params["workspace_id"] = workspace_id
    else:
        query += " AND user_id = :user_id"
        params["user_id"] = current_user["id"]
    query += " ORDER BY created_at DESC LIMIT :limit"

    rows = db.execute(text(query), params).fetchall()
    return [
        {
            "id": row[0],
            "workspace_id": row[1],
            "label": row[2],
            "request_payload": json.loads(row[3]),
            "created_at": _normalize_dt(row[4]),
        }
        for row in rows
    ]
