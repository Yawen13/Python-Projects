import os
from pathlib import Path

# Load .env before other imports that depend on environment variables
_env_path = Path(__file__).resolve().parent.parent / ".env"
if _env_path.exists():
    with open(_env_path, encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _key, _, _val = _line.partition("=")
                os.environ.setdefault(_key.strip(), _val.strip().strip("\"'"))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import Dict, List
from pydantic import BaseModel
from backend.db import (
    init_db,
    get_all_tickets,
    get_ticket,
    add_ticket,
    update_ticket_status,
    update_ticket_suggestion,
    get_ticket_stats,
)
from backend.ai_classifier import classify_description, generate_suggestion

app = FastAPI(title="IT 智能报修台")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


STATUSES = ["待处理", "处理中", "已完成"]


class TicketCreate(BaseModel):
    description: str


class Ticket(BaseModel):
    id: int
    description: str
    category: str
    status: str
    created_at: str


class TicketStatusUpdate(BaseModel):
    status: str


class TicketStats(BaseModel):
    total: int
    by_category: Dict[str, int]
    by_status: Dict[str, int]


@app.on_event("startup")
def on_startup():
    init_db()


@app.post("/api/tickets", response_model=Ticket)
def create_ticket(ticket: TicketCreate):
    description = ticket.description.strip()
    if not description:
        raise HTTPException(status_code=400, detail="故障描述不能为空")

    category = classify_description(description)
    ticket_id = add_ticket(description, category)
    row = get_ticket(ticket_id)
    return Ticket(
        id=row["id"],
        description=row["description"],
        category=row["category"],
        status=row["status"],
        created_at=row["created_at"],
    )


@app.get("/api/tickets", response_model=List[Ticket])
def list_tickets():
    rows = get_all_tickets()
    return [
        Ticket(
            id=row["id"],
            description=row["description"],
            category=row["category"],
            status=row["status"],
            created_at=row["created_at"],
        )
        for row in rows
    ]


@app.patch("/api/tickets/{ticket_id}/status", response_model=Ticket)
def change_ticket_status(ticket_id: int, payload: TicketStatusUpdate):
    if payload.status not in STATUSES:
        raise HTTPException(status_code=400, detail="无效的工单状态")
    row = get_ticket(ticket_id)
    if row is None:
        raise HTTPException(status_code=404, detail="工单不存在")
    update_ticket_status(ticket_id, payload.status)
    updated = get_ticket(ticket_id)
    return Ticket(
        id=updated["id"],
        description=updated["description"],
        category=updated["category"],
        status=updated["status"],
        created_at=updated["created_at"],
    )


@app.get("/api/tickets/stats", response_model=TicketStats)
def ticket_stats():
    rows = get_ticket_stats()
    total = 0
    by_category: Dict[str, int] = {}
    by_status: Dict[str, int] = {}
    for row in rows:
        count = row["count"]
        total += count
        by_category[row["category"]] = by_category.get(row["category"], 0) + count
        by_status[row["status"]] = by_status.get(row["status"], 0) + count
    return TicketStats(total=total, by_category=by_category, by_status=by_status)


class TicketSuggestion(BaseModel):
    suggestion: str


@app.get("/api/tickets/{ticket_id}/suggestion", response_model=TicketSuggestion)
def get_ticket_suggestion(ticket_id: int):
    row = get_ticket(ticket_id)
    if row is None:
        raise HTTPException(status_code=404, detail="工单不存在")
    suggestion = row["suggestion"]
    if suggestion:
        return TicketSuggestion(suggestion=suggestion)
    suggestion = generate_suggestion(row["description"], row["category"])
    update_ticket_suggestion(ticket_id, suggestion)
    return TicketSuggestion(suggestion=suggestion)


@app.get("/")
def read_index():
    html_file = Path(__file__).resolve().parent.parent / "frontend" / "index.html"
    return FileResponse(html_file)
