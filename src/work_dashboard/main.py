"""FastAPI アプリケーションのエントリポイント。"""

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from work_dashboard.routers import dashboard, members, tasks

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="WorkDashboard", version="0.1.0")

# Static files
_STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")

# Templates（グローバルで使えるよう app.state に保持）
_TEMPLATES_DIR = Path(__file__).parent / "templates"
app.state.templates = Jinja2Templates(directory=_TEMPLATES_DIR)

# Routers
app.include_router(dashboard.router)
app.include_router(members.router)
app.include_router(tasks.router)

logger.info("WorkDashboard started")
