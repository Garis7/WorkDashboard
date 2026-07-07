---
# このプロパティは、Claude Codeが関連するドキュメントの更新を検知するために必要です。消去しないでください。
---

# WorkDashboard — マネージャー向けチーム運営支援 Web アプリ

共有ルールの要約。詳細は `.claude/rules/` を参照。

## 技術スタック
- Python 3.12+ (`.python-version` = 3.12), uv
- Ruff, pytest, pre-commit
- FastAPI + Jinja2 + htmx 2.x
- SQLAlchemy 2.x + Alembic + SQLite
- PicoCSS v2
- レイヤード構成: Router → Service → Repository → Model
  （`src/work_dashboard/` 配下: `routers/` `services/` `repositories/` `models/`）

## 基本原則
- 既存コードと既存慣習を優先し、変更は小さく保つ
- 振る舞い変更には対応テストを追加・更新
- 完了前に `make check-all`（format / lint / test）を通す
  - typecheck は未導入（Makefile でスキップ中）。導入したらここを更新
- I/O、外部API、永続化、例外境界、重い処理にはログ
- 最適化は計測後に行う

## 実装フロー
1. 既存コード・関連テスト・`docs/`（requirements / data_model / screens）を確認
2. 影響範囲・テスト方針を短く整理してから小さく実装
3. テスト追加・更新（`tests/unit/` `tests/integration/`）
4. `make check-all`

## よく使うコマンド
```bash
make setup        # uv sync + pre-commit install
make check-all    # format + lint + test
make run          # uvicorn 起動 (port 8000)
make migrate      # alembic upgrade head
uv add package_name
uv add --dev package_name
uv run pytest
```

## コーディング規約
- 実装コードは `src/work_dashboard/`、テストは `tests/`
- 現代的な型構文（`X | None`、組み込みジェネリクス）を使用
- Docstring は NumPy 形式
- 命名: PascalCase / snake_case / UPPER_SNAKE / `_prefix`

## 分割ルール（`.claude/rules/`）
- testing.md / logging.md / performance.md
- github.md / review.md / database.md / frontend.md

## 自己改善エコシステム
環境の維持・改善はユーザーレベルの `/self-improve` スキル（3 モード）で行う。モデル非依存。
- `decay` — 既存資産 7 系統（CLAUDE.md / rules / skills / memory / hooks / settings / commands）の腐敗検知
- `distill` — セッションの教訓を lint > rules/CLAUDE.md > skill > memory の優先順で定着
- `harvest` — 蒸留元台帳（`~/.claude/self-improvement/sources.md`）を巡回し新知見を取り込み

原則: 採用より**見送り判断の記録**が資産。全判断を `~/.claude/self-improvement/decisions.md` に残す。
