---
description: 実験結果の検証（テスト＆バリデーション）と集計分析を実行
allowed-tools: Bash
---

# 検証・集計

実験完了後のトライアル検証とデータ集計を実行します。

## 前提条件

このコマンドを実行する前に、以下が完了していることを確認してください：

1. `git checkout HEAD -- CLAUDE.md tests/ scripts/verify_trials.py scripts/validate_local.py scripts/analyze_results.py` で全ファイルが復元済み
2. Claude Code が再起動済み（CLAUDE.md の変更を反映するため）

## Step 1: テスト＆バリデーション

各トライアルの結果 JSON にテスト・検証フィールドを追加します。

```bash
python3 scripts/verify_trials.py
```

**出力を確認**して、全トライアルのテスト結果と検証スコアが正常であることを確認してください。

## Step 2: 結果集計

```bash
python3 scripts/analyze_results.py
```
