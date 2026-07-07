---
# このプロパティは、Claude Codeが関連するドキュメントの更新を検知するために必要です。消去しないでください。
---

# WorkDashboard — Claude Code 作業指針

マネージャー向けチーム運営支援の個人用 FastAPI アプリ。
リポジトリ: https://github.com/Garis7/WorkDashboard
仕様は `docs/`（requirements / data_model / screens）、共有ルールは `.claude/rules/`（testing / logging / performance / github / review / database / frontend）。

## 必須ルール（最優先・違反不可）
1. いきなりコードを書かない。まず仕様の曖昧さを洗い出し、影響範囲・テスト方針を短く整理する
2. 設計判断では実装方針を3つ比較して採用案を選び、バグが出やすい箇所とテスト観点を先に挙げる
3. 画面・データ仕様は推測せず `docs/` と実物（既存テンプレート・DB）で確認してから書く
4. 既存慣習を優先し、変更は小さく保つ。clever より決定的でデバッグしやすい実装
5. 振る舞い変更には `tests/` のテストを追加・更新（t-wada流TDD: `testing.md`）
6. 完了前に `make check-all`（format / lint / test）を通す。UI 変更は実アプリ起動での動作確認まで
7. I/O・外部API・DB・例外境界・重い処理にはログ
8. 最適化は計測後

## 固有の注意（共有ルールより優先）
- Python は **3.12**（`.python-version`）。テンプレート由来の「3.14+」に引きずられない
- typecheck は未導入（Makefile でスキップ中）。Hypothesis / `tests/property/` も未導入
- `make` が無いシェル（Git Bash 等）では Makefile の中身どおり `uv run ...` に読み替え
- アプリ再起動が反映されない時は、旧 python プロセスがポート8000を握っている可能性。`Get-NetTCPConnection -LocalPort 8000` で占有 PID を特定して停止する
- git 識別情報はリポジトリローカル設定済み（Garis7 / GitHub noreply）

## 構成（`src/work_dashboard/`）
- レイヤ: Router (`routers/`) → Service (`services/`) → Repository (`repositories/`) → Model (`models/`)
- 描画: `templates/`（Jinja2 + htmx 2.x + PicoCSS v2、CDN 読込）/ `static/css/app.css`
- 画面: `/`（dashboard）/ members / tasks。基盤: `main.py` / `database.py` / `utils.py`
- 周辺: `alembic/` / `docs/` / `tests/`（unit / integration）。起動補助: `start.bat` / `run.ps1`

## スタック / コマンド
Python 3.12+ / uv / FastAPI / Jinja2 / SQLAlchemy 2.x + Alembic + SQLite / htmx 2.x / PicoCSS v2 / pytest / Ruff / pre-commit

```bash
make setup      # uv sync + pre-commit install
make check-all  # format + lint + test
make run        # uvicorn 起動 (port 8000)
make migrate    # alembic upgrade head
```

## 規約
- Ruff: `line-length=100` / `select=["E","F","I","UP","B","SIM","ANN"]`（tests は ANN 除外、B008 は ignore）。型は `X | None`, `list[T]`。Docstring は NumPy 形式。命名: PascalCase / snake_case / UPPER_SNAKE / `_prefix`
- 設計=Opus、実装=Sonnet（`opusplan` / 実装のみは `/model sonnet`）
- サブエージェント: 検索・単純処理=Haiku、実装・レビュー=Sonnet、設計=Opus
- effort: 単純作業=低 / 設計・デバッグ=高。Workflow はコスト最大ゆえ明示依頼時のみ

## 自己改善エコシステム（モデル非依存の運用）
- ①腐敗検知: 月1目安で `/decay-check`（CLAUDE.md・rules・skills・memory・hooks・settings・commands の7系統監査）
- ②教訓定着: セッション終盤に `/retro`（教訓を lint / CLAUDE.md / skill / memory へ仕分け）
- ③外部蒸留: 月1目安で `/distill`（`~/.claude/self-improvement/sources.md` の巡回。**見送り判断の記録が資産**）
- 本書は 60 行以内を維持。足すときは先に削る
