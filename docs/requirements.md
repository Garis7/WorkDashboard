# WorkDashboard 要件定義書

## 1. 概要

マネージャー個人がローカル環境で利用する、チーム運営支援 Web アプリ。
メンバーごとの Will / Can / Must を半期単位で管理し、Teams / Slack 等で流れてくる依頼をタスクとして記録・可視化する。

## 2. 目的

- メンバーの WCM（Will / Can / Must）を一元管理し、半期ごとの変化を追える状態にする
- 各種チャネルで発生するタスクを一箇所に集約し、期限管理の抜け漏れを防ぐ
- 「今、期限が近いタスクは何か」を開いてすぐ把握できる

## 3. スコープ

### 対象
- メンバーマスタの管理（CRUD）
- WCM の管理（半期単位、過去期は read-only）
- Must を Task から参照できるようにする
- タスクマスタの管理（CRUD）
- ダッシュボードでの期限近接・期限超過タスク表示

### 対象外
- 他ユーザーとの共有・マルチユーザー対応
- 認証・認可
- Teams / Slack API との自動連携（手入力で URL を貼る運用）
- 資料ファイルそのものの保存（URL のみ保持）
- モバイル対応（PC ブラウザ想定）
- 通知機能（メール・プッシュ等）

## 4. 利用者

- マネージャー本人 1 名のみ
- 自身も Member レコードとして登録し、`is_self = true` フラグで識別する

## 5. 機能要件

### 5.1 メンバー管理
- 登録 / 編集 / 無効化（`active=false`）
- 一覧表示（`active=true` のみデフォルト表示、トグルで全件表示）
- 属性: `name`, `is_self`, `active`

### 5.2 WCM 管理
- メンバー詳細画面から期を選択して WCM を閲覧
- 現行期は編集可能、過去期は read-only
- period 表記: `FY202504`, `FY202510`, `FY202604` ...（FY + 開始年月 4 桁）
  - 会社の半期は 4 月 / 10 月開始
- Will / Can: 各 1 フィールドの自由記述（Markdown 可）
- Must: 1 行 = 1 ミッション、以下の列を持つ
  - ① theme（大項目・テーマ）
  - ② sub_theme（中項目）
  - ③ mission（個別のミッション）
  - ④ criteria（達成基準）
  - ⑤ progress（現在の進捗状況、自由記述）
- Must は 1 メンバー × 1 period に対して複数行追加可能
- 表示順制御のため `order` 列を持つ

### 5.3 タスク管理
- 登録 / 編集 / 削除
- 属性
  - `name`: タスク名
  - `member_id`: 担当メンバー（必須）
  - `mission_id`: Must③への参照（**任意**、未紐づけ可）
  - `deadline`: 期限日
  - `conversation_location`: 会話場所（Teams / Slack の URL 等）
  - `materials_url`: 資料 URL（SharePoint / OneDrive / ローカルパス等）
  - `done_at`: 完了日時（null = 未完了）
- 一覧: デフォルトは未完了のみ、「完了含む」トグルで全件表示
- 完了操作: 一覧・詳細から 1 クリックで `done_at = now()`

### 5.4 ダッシュボード（トップ画面）
- **期限超過セクション**: `deadline < today` かつ未完了のタスク一覧（強調表示）
- **期限近接セクション**: `today <= deadline <= today + 7日` かつ未完了のタスク一覧
- 表示件数上限なし、`deadline` 昇順
- 完了済みタスクは表示しない

## 6. 非機能要件

- ローカル環境（`uv run` で起動）で単一プロセス動作
- データは SQLite ファイルに保存（バックアップはファイルコピーで可）
- 初回起動時に DB を自動作成（Alembic マイグレーション）
- レスポンスはローカル想定で体感遅延なし（数百ミリ秒以内）
- PicoCSS v2 ベースで最低限の見やすさを確保
- htmx によるサーバーサイドレンダリング
- 個人情報・秘密情報はログ出力しない（`.claude/rules/logging.md`）

## 7. 技術スタック

`CLAUDE.md` の方針に従う。

- Python 3.14+ / uv
- FastAPI + Jinja2 + htmx 2.x
- SQLAlchemy 2.x + Alembic + SQLite
- PicoCSS v2
- Ruff / pytest / Hypothesis / pre-commit
- レイヤード構成: Router → Service → Repository → Model

## 8. 画面一覧（概要）

詳細は [screens.md](screens.md) を参照。

- `/` ダッシュボード
- `/members` メンバー一覧
- `/members/{id}` メンバー詳細（WCM 閲覧・編集、期切替）
- `/tasks` タスク一覧
- `/tasks/new`, `/tasks/{id}/edit` タスク登録・編集

## 9. データモデル（概要）

詳細は [data_model.md](data_model.md) を参照。

```
Member (1) ── (N) WCM ── (N) Must
                              └── (0..N) Task
Member (1) ───────────────────── (N) Task
```

## 10. 想定外のリスク / 留意事項

- 半期切替時、現行期から次期への Must コピー運用が必要になる可能性あり
  （MVP では手動で新規追加、将来「前期からコピー」ボタン検討）
- 1 ミッションに複数の達成基準がある場合、現状は `criteria` に改行区切りで書く想定
- 資料 URL のリンク切れ検知は行わない
