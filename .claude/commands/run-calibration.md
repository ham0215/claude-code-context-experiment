---
description: チャンク数→実コンテキスト占有率のキャリブレーションテーブルを作成
allowed-tools: Read, Bash, Write
---

# コンテキスト・キャリブレーション

ノイズチャンクを読み込み、`/context` でコンテキストウィンドウ占有率を実測するキャリブレーション用コマンドです。

## 重要な制約

- **このコマンドはメインウィンドウで実行する必要があります**（`/context` はCLI組み込みコマンドのため）
- **1レベルにつき1セッション**: 正確な測定のため、各レベルは `/clear` 後または新規セッションで実行してください
- チャンクを読み込むだけで、FizzBuzz実装は行いません

## コンテキストレベル

| レベル | 読み込むチャンク数 | 名目消費率 |
|--------|-------------------|-----------|
| baseline | 0 chunks       | 0%        |
| 30%    | 48 chunks         | ~30%      |
| 50%    | 80 chunks         | ~50%      |
| 80%    | 128 chunks        | ~80%      |
| 90%    | 144 chunks        | ~90%      |

## 使い方

ユーザーから以下のパラメータを確認してください：

1. **レベル**: `baseline`, `30%`, `50%`, `80%`, `90%` のいずれか（複数選択可）

## 実行手順

### Step 1: ベースライン測定（レベル = baseline の場合）

チャンクを一切読み込まず、ユーザーに以下を依頼：

```
チャンク読み込み前のベースラインを測定します。
`/context` を実行してください。
```

ユーザーが `/context` を実行したら、出力からトークン数と占有率を記録して Step 3 に進む。

### Step 2: チャンク読み込み（baseline 以外）

レベルに応じたチャンク数を Read ツールで読み込む。

- プロジェクトルート: `/Users/naoto.hamada/github/ham/claude-code-context-experiment`
- チャンクファイル: `noise_chunks/chunk_{i}.txt`（i は 0 始まり）

| レベル | 読み込み範囲 |
|--------|-------------|
| 30%   | chunk_0.txt ~ chunk_47.txt (48個) |
| 50%   | chunk_0.txt ~ chunk_79.txt (80個) |
| 80%   | chunk_0.txt ~ chunk_127.txt (128個) |
| 90%   | chunk_0.txt ~ chunk_143.txt (144個) |

**読み込み方法**: 10個ずつバッチで並列読み込み。全チャンク読み込み後、ユーザーに以下を依頼：

```
全 {N} チャンクの読み込みが完了しました。
`/context` を実行してください。
```

### Step 3: 結果記録

ユーザーが `/context` を実行した出力から以下を抽出：

- `total_tokens`: 合計トークン数（例: 200k の場合 200000）
- `used_tokens`: 使用トークン数（例: 41k の場合 41000）
- `used_percent`: 占有率（例: 21%）
- `free_tokens`: 空き容量
- `messages_tokens`: Messages カテゴリのトークン数

結果を JSON ファイルに保存：

```
{project_root}/calibration/calibration_{level}.json
```

フォーマット:
```json
{
  "level": "30%",
  "nominal_percent": 30,
  "chunks_read": 48,
  "measured_used_tokens": 85000,
  "measured_total_tokens": 200000,
  "measured_percent": 42.5,
  "messages_tokens": 60000,
  "free_tokens": 115000,
  "timestamp": "2026-02-14T...",
  "note": "Measured in main CLI window with /context command"
}
```

保存前にディレクトリを作成：
```bash
mkdir -p /Users/naoto.hamada/github/ham/claude-code-context-experiment/calibration
```

### Step 4: 次のレベルへの案内

測定完了後、次のレベルがある場合はユーザーに案内：

```
{level} の測定が完了しました。

結果: {chunks_read} chunks → {measured_percent}%（名目 {nominal_percent}%）

次のレベルを測定するには、コンテキストをリセットしてから再実行してください：
1. `/clear` でコンテキストをクリア
2. `/run-calibration` で次のレベルを選択
```

### Step 5: キャリブレーションテーブル生成

全レベル測定後（または既存の calibration JSON が揃っている場合）、サマリーテーブルを生成：

既存の calibration JSON を確認：
```
calibration/calibration_baseline.json
calibration/calibration_30%.json
calibration/calibration_50%.json
calibration/calibration_80%.json
calibration/calibration_90%.json
```

存在するファイルをすべて読み込み、以下のマークダウンテーブルを `calibration/README.md` に保存：

```markdown
# Context Calibration Table

| Level | Chunks | Nominal % | Measured % | Used Tokens | Total Tokens | Date |
|-------|--------|-----------|------------|-------------|--------------|------|
| baseline | 0 | 0% | XX% | XXk | 200k | YYYY-MM-DD |
| 30% | 48 | 30% | XX% | XXk | 200k | YYYY-MM-DD |
| 50% | 80 | 50% | XX% | XXk | 200k | YYYY-MM-DD |
| 80% | 128 | 80% | XX% | XXk | 200k | YYYY-MM-DD |
| 90% | 144 | 90% | XX% | XXk | 200k | YYYY-MM-DD |

Note: Measured in main CLI window. Agent workers have similar but not identical overhead.
```

## 注意事項

- `/context` の出力にはANSIカラーコードが含まれます。トークン数を正確にパースしてください
- Autocompact buffer は可変のため、測定値は参考値です
- メインウィンドウとワーカーでは固定オーバーヘッド（tools, agents等）が若干異なります
- 同一セッションで複数レベルを測定しないでください（前のチャンクが残るため）
