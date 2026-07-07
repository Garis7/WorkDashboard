# GitHub運用

## 原則
- 変更は小さく、目的が明確な単位に分ける
- 既存 workflow / Makefile の流儀を尊重
- CI を壊す変更を避ける
- 完了前に必要な test / lint / typecheck を通す

## PR
- 背景、変更点、影響範囲、確認方法を書く
- タイトルは具体的にする
- 破壊的変更や移行が必要なら明記

## よく使うコマンド
```bash
make pr TITLE="x" BODY="y"
make issue TITLE="x" BODY="y"
make check-all
```
