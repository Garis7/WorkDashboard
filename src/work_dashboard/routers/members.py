"""メンバー管理・WCM / Must 管理ルーター。"""

import logging
from datetime import date

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from work_dashboard.database import get_db
from work_dashboard.models.member import Member
from work_dashboard.models.task import Task
from work_dashboard.models.wcm import WCM, Must
from work_dashboard.utils import current_period, period_label

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/members")


# ---------------------------------------------------------------------------
# メンバー CRUD
# ---------------------------------------------------------------------------


@router.get("/", response_class=HTMLResponse)
def member_list(
    request: Request,
    show_inactive: bool = False,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """メンバー一覧。"""
    stmt = select(Member)
    if not show_inactive:
        stmt = stmt.where(Member.active.is_(True))
    stmt = stmt.order_by(Member.is_self.desc(), Member.name)
    members = db.scalars(stmt).all()

    templates = request.app.state.templates
    return templates.TemplateResponse(
        request,
        "members/list.html",
        {"members": members, "show_inactive": show_inactive},
    )


@router.get("/new", response_class=HTMLResponse)
def new_member_form(request: Request) -> HTMLResponse:
    """メンバー新規作成フォーム。"""
    templates = request.app.state.templates
    return templates.TemplateResponse(request, "members/form.html", {"member": None})


@router.post("/", response_class=RedirectResponse)
def create_member(
    name: str = Form(...),
    is_self: bool = Form(False),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    """メンバー新規作成。"""
    member = Member(name=name.strip(), is_self=is_self, active=True)
    db.add(member)
    db.commit()
    logger.info("Member created: id=%d name=%s", member.id, member.name)
    return RedirectResponse(url="/members", status_code=303)


@router.get("/{member_id}/edit", response_class=HTMLResponse)
def edit_member_form(
    request: Request,
    member_id: int,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """メンバー編集フォーム。"""
    member = db.get(Member, member_id)
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found")

    templates = request.app.state.templates
    return templates.TemplateResponse(request, "members/form.html", {"member": member})


@router.post("/{member_id}/edit", response_class=RedirectResponse)
def update_member(
    member_id: int,
    name: str = Form(...),
    is_self: bool = Form(False),
    active: bool = Form(True),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    """メンバー更新。"""
    member = db.get(Member, member_id)
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found")

    member.name = name.strip()
    member.is_self = is_self
    member.active = active
    db.commit()
    logger.info("Member updated: id=%d name=%s", member.id, member.name)
    return RedirectResponse(url="/members", status_code=303)


# ---------------------------------------------------------------------------
# メンバー詳細 (WCM + タスク)
# ---------------------------------------------------------------------------


@router.get("/{member_id}", response_class=HTMLResponse)
def member_detail(
    request: Request,
    member_id: int,
    period: str | None = None,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """メンバー詳細: WCM 表示・編集 + タスク一覧。"""
    member = db.get(Member, member_id)
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found")

    # 存在する period の降順一覧
    periods: list[str] = list(
        db.scalars(
            select(WCM.period).where(WCM.member_id == member_id).order_by(WCM.period.desc())
        ).all()
    )

    cur_period = current_period()
    selected_period = period or cur_period
    is_current = selected_period == cur_period

    # 選択期の WCM を取得（なければ None）
    wcm: WCM | None = db.scalar(
        select(WCM)
        .where(WCM.member_id == member_id, WCM.period == selected_period)
        .options(selectinload(WCM.musts))
    )

    # このメンバーの未完了タスク
    tasks = db.scalars(
        select(Task)
        .where(Task.member_id == member_id, Task.done_at.is_(None))
        .options(selectinload(Task.mission))
        .order_by(Task.deadline.asc())
    ).all()

    templates = request.app.state.templates
    return templates.TemplateResponse(
        request,
        "members/detail.html",
        {
            "member": member,
            "wcm": wcm,
            "periods": periods,
            "selected_period": selected_period,
            "is_current": is_current,
            "cur_period": cur_period,
            "period_label": period_label,
            "tasks": tasks,
            "today": date.today(),
        },
    )


# ---------------------------------------------------------------------------
# WCM 作成・Will/Can 編集
# ---------------------------------------------------------------------------


@router.post("/{member_id}/wcm/init", response_class=RedirectResponse)
def init_wcm(
    member_id: int,
    period: str = Form(...),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    """指定期の WCM レコードを新規作成する。"""
    member = db.get(Member, member_id)
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found")

    existing = db.scalar(select(WCM).where(WCM.member_id == member_id, WCM.period == period))
    if not existing:
        wcm = WCM(member_id=member_id, period=period)
        db.add(wcm)
        db.commit()
        logger.info("WCM created: member_id=%d period=%s", member_id, period)

    return RedirectResponse(url=f"/members/{member_id}?period={period}", status_code=303)


@router.post("/{member_id}/wcm/{wcm_id}/will-can", response_class=RedirectResponse)
def update_will_can(
    member_id: int,
    wcm_id: int,
    will: str = Form(""),
    can: str = Form(""),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    """Will / Can を保存する。"""
    wcm = db.get(WCM, wcm_id)
    if wcm is None or wcm.member_id != member_id:
        raise HTTPException(status_code=404, detail="WCM not found")

    wcm.will = will.strip() or None
    wcm.can = can.strip() or None
    db.commit()
    logger.info("WCM will/can updated: wcm_id=%d", wcm_id)
    return RedirectResponse(url=f"/members/{member_id}?period={wcm.period}", status_code=303)


# ---------------------------------------------------------------------------
# Must CRUD
# ---------------------------------------------------------------------------


@router.post("/{member_id}/wcm/{wcm_id}/musts", response_class=RedirectResponse)
def create_must(
    member_id: int,
    wcm_id: int,
    theme: str = Form(...),
    sub_theme: str = Form(""),
    mission: str = Form(...),
    criteria: str = Form(""),
    progress: str = Form(""),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    """Must 行を追加する。"""
    wcm = db.get(WCM, wcm_id)
    if wcm is None or wcm.member_id != member_id:
        raise HTTPException(status_code=404, detail="WCM not found")

    # 現在の最大 order_ + 10 で末尾追加
    max_order = db.scalar(
        select(Must.order_).where(Must.wcm_id == wcm_id).order_by(Must.order_.desc()).limit(1)
    )
    new_order = (max_order or 0) + 10

    must = Must(
        wcm_id=wcm_id,
        theme=theme.strip(),
        sub_theme=sub_theme.strip() or None,
        mission=mission.strip(),
        criteria=criteria.strip() or None,
        progress=progress.strip() or None,
        order_=new_order,
    )
    db.add(must)
    db.commit()
    logger.info("Must created: id=%d wcm_id=%d mission=%s", must.id, wcm_id, must.mission)
    return RedirectResponse(url=f"/members/{member_id}?period={wcm.period}", status_code=303)


@router.get("/{member_id}/wcm/{wcm_id}/musts/{must_id}/edit", response_class=HTMLResponse)
def edit_must_form(
    request: Request,
    member_id: int,
    wcm_id: int,
    must_id: int,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Must 編集フォーム。"""
    must = db.get(Must, must_id)
    if must is None or must.wcm_id != wcm_id:
        raise HTTPException(status_code=404, detail="Must not found")
    wcm = db.get(WCM, wcm_id)
    if wcm is None or wcm.member_id != member_id:
        raise HTTPException(status_code=404, detail="WCM not found")

    templates = request.app.state.templates
    return templates.TemplateResponse(
        request,
        "members/must_form.html",
        {"must": must, "member_id": member_id, "wcm": wcm},
    )


@router.post("/{member_id}/wcm/{wcm_id}/musts/{must_id}/edit", response_class=RedirectResponse)
def update_must(
    member_id: int,
    wcm_id: int,
    must_id: int,
    theme: str = Form(...),
    sub_theme: str = Form(""),
    mission: str = Form(...),
    criteria: str = Form(""),
    progress: str = Form(""),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    """Must 行を更新する。"""
    must = db.get(Must, must_id)
    if must is None or must.wcm_id != wcm_id:
        raise HTTPException(status_code=404, detail="Must not found")
    wcm = db.get(WCM, wcm_id)
    if wcm is None or wcm.member_id != member_id:
        raise HTTPException(status_code=404, detail="WCM not found")

    must.theme = theme.strip()
    must.sub_theme = sub_theme.strip() or None
    must.mission = mission.strip()
    must.criteria = criteria.strip() or None
    must.progress = progress.strip() or None
    db.commit()
    logger.info("Must updated: id=%d", must_id)
    return RedirectResponse(url=f"/members/{member_id}?period={wcm.period}", status_code=303)


@router.post("/{member_id}/wcm/{wcm_id}/musts/{must_id}/delete", response_class=RedirectResponse)
def delete_must(
    member_id: int,
    wcm_id: int,
    must_id: int,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    """Must 行を削除する。"""
    must = db.get(Must, must_id)
    if must is None or must.wcm_id != wcm_id:
        raise HTTPException(status_code=404, detail="Must not found")
    wcm = db.get(WCM, wcm_id)
    if wcm is None or wcm.member_id != member_id:
        raise HTTPException(status_code=404, detail="WCM not found")

    db.delete(must)
    db.commit()
    logger.info("Must deleted: id=%d", must_id)
    return RedirectResponse(url=f"/members/{member_id}?period={wcm.period}", status_code=303)


@router.post("/{member_id}/wcm/{wcm_id}/musts/{must_id}/move", response_class=RedirectResponse)
def move_must(
    member_id: int,
    wcm_id: int,
    must_id: int,
    direction: str = Form(...),  # "up" or "down"
    db: Session = Depends(get_db),
) -> RedirectResponse:
    """Must 行の表示順を上下に移動する（order_ の値を隣と交換）。"""
    wcm = db.get(WCM, wcm_id)
    if wcm is None or wcm.member_id != member_id:
        raise HTTPException(status_code=404, detail="WCM not found")

    musts = db.scalars(select(Must).where(Must.wcm_id == wcm_id).order_by(Must.order_)).all()

    idx = next((i for i, m in enumerate(musts) if m.id == must_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Must not found")

    if direction == "up" and idx > 0:
        musts[idx].order_, musts[idx - 1].order_ = (
            musts[idx - 1].order_,
            musts[idx].order_,
        )
        db.commit()
        logger.info("Must moved up: id=%d", must_id)
    elif direction == "down" and idx < len(musts) - 1:
        musts[idx].order_, musts[idx + 1].order_ = (
            musts[idx + 1].order_,
            musts[idx].order_,
        )
        db.commit()
        logger.info("Must moved down: id=%d", must_id)

    return RedirectResponse(url=f"/members/{member_id}?period={wcm.period}", status_code=303)
