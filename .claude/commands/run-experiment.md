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

## 2. コンテキスト準備と消費量確認

コンテキストを準備した後、`/context` コマンドを実行して現在のコンテキスト消費量を確認してください。

確認した結果は以下のファイルに記録してください：

```bash
# 結果ディレクトリがなければ作成
mkdir -p results

# コンテキスト消費量を記録（例：30%レベルの場合）
echo "$(date '+%Y-%m-%d %H:%M:%S') - Context Level: 30% - Usage: [/contextの結果を記入]" >> results/context_usage.log
```

※ 各コンテキストレベル（30%, 50%, 80%, 90%）ごとに記録を行ってください

## 3. 実験実行

```bash
python scripts/experiment_runner.py
```

※ 確認プロンプトで `y` を入力して実験を開始

## 4. 実験完了後

実験が完了したら結果を分析：

```bash
python scripts/analyze_results.py
```

## 注意事項

- 実験は300試行（30%, 50%, 80% × 各100回）を自動実行します
- 結果は `results/` ディレクトリに保存されます
- 中断した場合は `resume_from` パラメータで再開可能です
