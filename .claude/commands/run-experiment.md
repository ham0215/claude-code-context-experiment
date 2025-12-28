---
description: コンテキスト消費実験を開始する
allowed-tools: Bash, Read, Write, Edit
---

# コンテキスト消費実験の実行

以下の手順で実験を実行してください：

## 1. キャリブレーション（必要に応じて）

キャリブレーション結果が存在するか確認し、なければ実行：

```bash
python scripts/calibration.py
```

※ 対話的な確認が出た場合は `y` を入力

## 2. 実験実行

```bash
python scripts/experiment_runner.py
```

※ 確認プロンプトで `y` を入力して実験を開始

## 3. 実験完了後

実験が完了したら結果を分析：

```bash
python scripts/analyze_results.py
```

## 注意事項

- 実験は300試行（30%, 50%, 80% × 各100回）を自動実行します
- 結果は `results/` ディレクトリに保存されます
- 中断した場合は `resume_from` パラメータで再開可能です
