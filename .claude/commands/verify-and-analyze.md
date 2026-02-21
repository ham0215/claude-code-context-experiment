---
description: 実験結果の検証（テスト＆バリデーション）と集計分析を実行
allowed-tools: Bash
---

# 検証・集計

実験完了後のトライアル検証とデータ集計を実行します。

## Step 0: テスト/検証ファイルの復元

実験中に隠蔽されたテスト・検証ファイルを git から復元します。

```bash
git checkout HEAD -- tests/test_fizzbuzz.py tests/test_validate_local.py tests/test_analyze_results.py tests/conftest.py scripts/verify_trials.py scripts/validate_local.py scripts/analyze_results.py
```

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
