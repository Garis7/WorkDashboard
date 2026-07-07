# データベース / ORM

SQLAlchemy 2.x + Alembic + SQLite を前提とする。

## 原則
- StrEnum カラムは `EnumColumn` (TypeDecorator) を使う
- Alembic + SQLite では `with op.batch_alter_table()` を使う
- マイグレーション作成前に既存データとの互換性を確認する
- セッション管理は Repository 層に集約し、Router/Service から直接触らない
- `select()` / `scalars()` の 2.x スタイルを使う
- テストでは in-memory SQLite (`sqlite://`) を使い、本番DBに触らない
- Enum 値の追加・変更時は既存レコードへの影響を確認する

## 落とし穴
- `Mapped[MyEnum]` だけでは DB 値は enum に変換されない
- `mapped_column(String(...))` では DB から `str` が返る
- SQLAlchemy の `Enum(...)` 型は SQLite では扱いにくいことがある
- Alembic autogenerate は TypeDecorator の変更を検出しない場合がある
