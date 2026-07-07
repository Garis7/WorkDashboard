"""WCM (Will / Can / Must) モデル。"""

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from work_dashboard.models.base import Base


class WCM(Base):
    """メンバーの半期ごとの Will / Can / Must。

    period は "FY202504" 形式（FY + 開始年月4桁）。
    UNIQUE (member_id, period) で 1 メンバー × 1 期 = 1 レコード。
    """

    __tablename__ = "wcms"
    __table_args__ = (UniqueConstraint("member_id", "period", name="uq_wcm_member_period"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(
        ForeignKey("members.id", ondelete="CASCADE"), nullable=False
    )
    period: Mapped[str] = mapped_column(String(10), nullable=False)
    will: Mapped[str | None] = mapped_column(Text)
    can: Mapped[str | None] = mapped_column(Text)

    member: Mapped["Member"] = relationship("Member", back_populates="wcms")  # noqa: F821
    musts: Mapped[list["Must"]] = relationship(  # noqa: F821
        "Must", back_populates="wcm", cascade="all, delete-orphan", order_by="Must.order_"
    )


class Must(Base):
    """Must の個別ミッション行。

    ① theme, ② sub_theme, ③ mission, ④ criteria, ⑤ progress の 5 属性を持つ。
    """

    __tablename__ = "musts"

    id: Mapped[int] = mapped_column(primary_key=True)
    wcm_id: Mapped[int] = mapped_column(
        ForeignKey("wcms.id", ondelete="CASCADE"), nullable=False, index=True
    )
    theme: Mapped[str] = mapped_column(String(200), nullable=False)
    sub_theme: Mapped[str | None] = mapped_column(String(200))
    mission: Mapped[str] = mapped_column(String(300), nullable=False)
    criteria: Mapped[str | None] = mapped_column(Text)
    progress: Mapped[str | None] = mapped_column(Text)
    order_: Mapped[int] = mapped_column(default=0, nullable=False)

    wcm: Mapped["WCM"] = relationship("WCM", back_populates="musts")
    tasks: Mapped[list["Task"]] = relationship(  # noqa: F821
        "Task", back_populates="mission"
    )
