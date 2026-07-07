"""Alembic マイグレーション環境設定。"""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Alembic Config オブジェクト
alembic_config = context.config

if alembic_config.config_file_name is not None:
    fileConfig(alembic_config.config_file_name)

# モデルの MetaData を autogenerate に使用
from work_dashboard.database import _DATABASE_URL  # noqa: E402
from work_dashboard.models import Base  # noqa: E402, F401  (全モデルをインポート)

alembic_config.set_main_option("sqlalchemy.url", _DATABASE_URL)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """オフラインモード（URL のみ）でマイグレーションを実行する。"""
    url = alembic_config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,  # SQLite の ALTER TABLE 対応
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """オンラインモード（Engine 接続）でマイグレーションを実行する。"""
    connectable = engine_from_config(
        alembic_config.get_section(alembic_config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,  # SQLite の ALTER TABLE 対応
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
