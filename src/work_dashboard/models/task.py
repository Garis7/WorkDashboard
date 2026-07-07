"""Task モデル。"""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from work_dashboard.models.base import Base


class Task(Base):
    """タスク。Teams / Slack 等で発生した依頼を記録する。

    mission_id は nullable: Must に紐づかないタスクも登録可能。
    done_at が null の場合は未完了。
    """

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"), nullable=False, index=True)
    mission_id: Mapped[int | None] = mapped_column(
        ForeignKey("musts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    deadline: Mapped[date] = mapped_column(Date, nullable=False)
    conversation_location: Mapped[str | None] = mapped_column(String(1000))
    materials_url: Mapped[str | None] = mapped_column(Text)
    done_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    member: Mapped["Member"] = relationship("Member", back_populates="tasks")  # noqa: F821
    mission: Mapped["Must | None"] = relationship(  # noqa: F821
        "Must", back_populates="tasks"
    )
