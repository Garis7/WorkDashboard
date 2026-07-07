"""ダッシュボード ルーター。"""

import logging
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from work_dashboard.database import get_db
from work_dashboard.models.task import Task

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """ダッシュボード: 期限超過・期限近接タスクを表示する。"""
    today = date.today()
    deadline_limit = today + timedelta(days=7)

    overdue = db.scalars(
        select(Task)
        .where(Task.done_at.is_(None), Task.deadline < today)
        .options(selectinload(Task.member), selectinload(Task.mission))
        .order_by(Task.deadline.asc())
    ).all()

    upcoming = db.scalars(
        select(Task)
        .where(Task.done_at.is_(None), Task.deadline >= today, Task.deadline <= deadline_limit)
        .options(selectinload(Task.member), selectinload(Task.mission))
        .order_by(Task.deadline.asc())
    ).all()

    logger.info("Dashboard: overdue=%d upcoming=%d", len(overdue), len(upcoming))

    templates = request.app.state.templates
    return templates.TemplateResponse(
        request,
        "dashboard/index.html",
        {"overdue": overdue, "upcoming": upcoming, "today": today},
    )
