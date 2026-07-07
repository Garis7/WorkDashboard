# テスト戦略（TDD）

t-wada流TDDを基本とする。

## 原則
- 振る舞い変更には対応テストを追加または更新する
- 再現可能な不具合は先に再現テストを作る
- 完了前に対象テスト、または `make test` を実行する
- 新機能・重要修正は TDD を優先する
- 単体テストを基本に、必要なら統合テストで補強する
- バグ修正では回帰テストを追加する
- 正常系・異常系・境界値を最低限カバーする

## サイクル
🔴 Red » 🟢 Green » 🔵 Refactor

## テスト種別
- `tests/unit/`
- `tests/integration/`
- `tests/property/`（Hypothesis 導入後に使用。現在は未導入）

## 実行コマンド
```bash
uv run pytest
make test
make test-cov
```
