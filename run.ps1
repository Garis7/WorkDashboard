# WorkDashboard script
# Usage: .\run.ps1 <command>
#
#   .\run.ps1 run        Start app (http://localhost:8000)
#   .\run.ps1 migrate    Apply DB migrations
#   .\run.ps1 test       Run tests
#   .\run.ps1 check-all  format + lint + test

param([string]$Command = "help")

Set-Location $PSScriptRoot

$UV = "C:\Users\user4\AppData\Local\Python\pythoncore-3.14-64\Scripts\uv.exe"

switch ($Command) {
    "setup" {
        & $UV sync
    }
    "run" {
        & $UV run alembic upgrade head
        & $UV run uvicorn work_dashboard.main:app --reload --host 127.0.0.1 --port 8000
    }
    "migrate" {
        & $UV run alembic upgrade head
    }
    "migration" {
        $msg = Read-Host "Migration name"
        & $UV run alembic revision --autogenerate -m $msg
    }
    "format" {
        & $UV run ruff format src tests
    }
    "lint" {
        & $UV run ruff check src tests --fix
    }
    "test" {
        & $UV run pytest -v
    }
    "check-all" {
        & $UV run ruff format src tests
        & $UV run ruff check src tests --fix
        & $UV run pytest -v
    }
    default {
        Write-Host ""
        Write-Host "Usage: .\run.ps1 <command>"
        Write-Host ""
        Write-Host "  run        Start app (http://localhost:8000)"
        Write-Host "  migrate    Apply DB migrations"
        Write-Host "  migration  Generate new migration file"
        Write-Host "  format     ruff format"
        Write-Host "  lint       ruff check"
        Write-Host "  test       pytest"
        Write-Host "  check-all  format + lint + test"
        Write-Host ""
    }
}
