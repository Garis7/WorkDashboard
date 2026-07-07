"""タスク管理ルーター。"""

import logging
from datetime import date, datetime

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from work_dashboard.database import get_db
from work_dashboard.models.member import Member
from work_dashboard.models.task import Task
from work_dashboard.models.wcm import WCM, Must
from work_dashboard.utils import current_period

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks")


@router.get("/", response_class=HTMLResponse)
def task_list(
    request: Request,
    show_done: bool = False,
    member_id: int | None = None,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """タスク一覧。メンバーフィルタ・完了フィルタ対応。"""
    stmt = (
        select(Task)
        .options(selectinload(Task.member), selectinload(Task.mission))
        .order_by(Task.done_at.asc().nulls_first(), Task.deadline.asc())
    )
    if not show_done:
        stmt = stmt.where(Task.done_at.is_(None))
    if member_id:
        stmt = stmt.where(Task.member_id == member_id)
    tasks = db.scalars(stmt).all()

    members = db.scalars(
        select(Member).where(Member.active.is_(True)).order_by(Member.is_self.desc(), Member.name)
    ).all()

    templates = request.app.state.templates
    return templates.TemplateResponse(
        request,
        "tasks/list.html",
        {
            "tasks": tasks,
            "show_done": show_done,
            "today": date.today(),
            "members": members,
            "selected_member_id": member_id,
        },
    )


@router.get("/new", response_class=HTMLResponse)
def new_task_form(
    request: Request,
    mission_id: int | None = None,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """タスク新規作成フォーム。"""
    members = db.scalars(
        select(Member).where(Member.active.is_(True)).order_by(Member.is_self.desc(), Member.name)
    ).all()

    period = current_period()
    preselect_member_id: int | None = None
    missions: list[Must] = []

    if mission_id:
        must = db.get(Must, mission_id)
        if must:
            preselect_member_id = must.wcm.member_id
            missions = db.scalars(
                select(Must)
                .join(WCM)
                .where(WCM.member_id == preselect_member_id, WCM.period == period)
                .order_by(Must.order_)
            ).all()

    templates = request.app.state.templates
    return templates.TemplateResponse(
        request,
        "tasks/form.html",
        {
            "task": None,
            "members": members,
            "missions": missions,
            "preselect_member_id": preselect_member_id,
            "preselect_mission_id": mission_id,
            "current_period": period,
        },
    )


@router.post("/", response_class=RedirectResponse)
def create_task(
    name: str = Form(...),
    member_id: int = Form(...),
    deadline: date = Form(...),
    mission_id: int | None = Form(None),
    conversation_location: str | None = Form(None),
    materials_url: str | None = Form(None),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    """タスク新規作成。"""
    task = Task(
        name=name.strip(),
        member_id=member_id,
        deadline=deadline,
        mission_id=mission_id or None,
        conversation_location=conversation_location or None,
        materials_url=materials_url or None,
    )
    db.add(task)
    db.commit()
    logger.info("Task created: id=%d name=%s deadline=%s", task.id, task.name, task.deadline)
    return RedirectResponse(url="/tasks", status_code=303)


@router.get("/{task_id}/edit", response_class=HTMLResponse)
def edit_task_form(
    request: Request,
    task_id: int,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """タスク編集フォーム。"""
    task = db.get(Task, task_id)
    if task is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Task not found")

    members = db.scalars(
        select(Member).where(Member.active.is_(True)).order_by(Member.is_self.desc(), Member.name)
    ).all()

    period = current_period()
    missions = db.scalars(
        select(Must)
        .join(WCM)
        .where(WCM.member_id == task.member_id, WCM.period == period)
        .order_by(Must.order_)
    ).all()

    templates = request.app.state.templates
    return templates.TemplateResponse(
        request,
        "tasks/form.html",
        {
            "task": task,
            "members": members,
            "missions": missions,
            "preselect_member_id": task.member_id,
            "preselect_mission_id": task.mission_id,
            "current_period": period,
        },
    )


@router.post("/{task_id}/edit", response_class=RedirectResponse)
def update_task(
    task_id: int,
    name: str = Form(...),
    member_id: int = Form(...),
    deadline: date = Form(...),
    mission_id: int | None = Form(None),
    conversation_location: str | None = Form(None),
    materials_url: str | None = Form(None),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    """タスク更新。"""
    task = db.get(Task, task_id)
    if task is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Task not found")

    task.name = name.strip()
    task.member_id = member_id
    task.deadline = deadline
    task.mission_id = mission_id or None
    task.conversation_location = conversation_location or None
    task.materials_url = materials_url or None
    db.commit()
    logger.info("Task updated: id=%d name=%s", task.id, task.name)
    return RedirectResponse(url="/tasks", status_code=303)


@router.post("/{task_id}/done", response_class=RedirectResponse)
def complete_task(
    task_id: int,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    """タスクを完了にする。"""
    task = db.get(Task, task_id)
    if task is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Task not found")

    task.done_at = datetime.now()
    db.commit()
    logger.info("Task completed: id=%d", task.id)
    return RedirectResponse(url="/tasks", status_code=303)


@router.post("/{task_id}/delete", response_class=RedirectResponse)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    """タスク削除。"""
    task = db.get(Task, task_id)
    if task is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()
    logger.info("Task deleted: id=%d", task_id)
    return RedirectResponse(url="/tasks", status_code=303)


@router.get("/api/missions", response_class=HTMLResponse)
def missions_for_member(
    request: Request,
    member_id: int,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """htmx: メンバー選択時に Mission のセレクトを返す。"""
    period = current_period()
    missions = db.scalars(
        select(Must)
        .join(WCM)
        .where(WCM.member_id == member_id, WCM.period == period)
        .order_by(Must.order_)
    ).all()

    templates = request.app.state.templates
    return templates.TemplateResponse(
        request,
        "partials/mission_options.html",
        {"missions": missions},
    )
