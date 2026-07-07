"""DB 接続・セッション管理。"""

import logging
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

logger = logging.getLogger(__name__)

# プロジェクトルート直下の work_dashboard.db を使用
_DB_PATH = Path(__file__).resolve().parents[2] / "work_dashboard.db"
_DATABASE_URL = f"sqlite:///{_DB_PATH}"

engine = create_engine(
    _DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_conn: object, _connection_record: object) -> None:
    """SQLite の外部キー制約を有効化する。"""
    cursor = dbapi_conn.cursor()  # type: ignore[union-attr]
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI の Depends で使用するセッションジェネレーター。"""
    db = SessionLocal()
    try:
        logger.debug("DB session opened")
        yield db
    finally:
        db.close()
        logger.debug("DB session closed")
