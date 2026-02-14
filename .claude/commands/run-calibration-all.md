---
description: 全レベルのキャリブレーションを自動再開方式で順次実行
allowed-tools: Read, Bash, Write, Glob
---

# 全レベル・キャリブレーション（自動再開方式）

全レベル（baseline, 30%, 50%, 80%, 90%）のキャリブレーションを順次実行します。
`/clear` はCLI組み込みコマンドのため自動実行できません。
代わりに **未測定の最初のレベルを自動検出** して実行します。

## ユーザーの操作

全レベル完了まで以下を繰り返すだけ：

```
/run-calibration-all  →  チャンク読み込み  →  /context  →  記録  →  /clear  →  繰り返し
```

## 定数

- プロジェクトルート: `/Users/naoto.hamada/github/ham/claude-code-context-experiment`
- キャリブレーションディレクトリ: `{project_root}/calibration/`
- チャンクディレクトリ: `{project_root}/noise_chunks/`

## レベル定義（実行順序）

```
levels = [
  { name: "baseline", nominal: 0,  chunks: 0,   file: "calibration_baseline.json" },
  { name: "30%",      nominal: 30, chunks: 48,  file: "calibration_30%.json" },
  { name: "50%",      nominal: 50, chunks: 80,  file: "calibration_50%.json" },
  { name: "80%",      nominal: 80, chunks: 128, file: "calibration_80%.json" },
  { name: "90%",      nominal: 90, chunks: 144, file: "calibration_90%.json" }
]
```

## 実行手順

### Step 1: 進捗確認

キャリブレーションディレクトリの既存ファイルを確認：

```bash
mkdir -p /Users/naoto.hamada/github/ham/claude-code-context-experiment/calibration
```

```
Glob: calibration/calibration_*.json
```

既存ファイルから完了済みレベルを特定し、**未測定の最初のレベル**を決定する。

進捗をユーザーに表示：

```
## キャリブレーション進捗

| Level    | Chunks | Status |
|----------|--------|--------|
| baseline | 0      | ✅ 完了 (XX%) |  ← JSON が存在
| 30%      | 48     | ⬜ 未測定     |  ← 次のターゲット
| 50%      | 80     | ⬜ 未測定     |
| 80%      | 128    | ⬜ 未測定     |
| 90%      | 144    | ⬜ 未測定     |

次のレベル: **30%**（48 chunks）
```

**全レベル完了の場合**: Step 6（テーブル生成）に直接進む。

### Step 2: チャンク読み込み

#### baseline の場合

チャンク読み込みは不要。すぐにユーザーへ `/context` 実行を依頼：

```
baseline レベル（チャンク 0 個）です。
`/context` を実行してください。
```

#### baseline 以外の場合

対象レベルのチャンク数に応じて `noise_chunks/chunk_{i}.txt` を Read ツールで読み込む。

- **30%**: chunk_0.txt ~ chunk_47.txt（48個）
- **50%**: chunk_0.txt ~ chunk_79.txt（80個）
- **80%**: chunk_0.txt ~ chunk_127.txt（128個）
- **90%**: chunk_0.txt ~ chunk_143.txt（144個）

**読み込み方法**: 10個ずつバッチで並列読み込み（Read ツールを10個同時に呼ぶ）。

全チャンク読み込み完了後：

```
全 {N} チャンクの読み込みが完了しました。
`/context` を実行してください。
```

### Step 3: /context 出力の待機と解析

ユーザーが `/context` を実行すると、出力がコンテキストに表示される。

出力例（ANSIカラーコード付き）：
```
claude-opus-4-6 · 41k/200k tokens (21%)
```

この出力から以下を抽出：
- **used_tokens**: `41k` → `41000`（k を 1000 倍に変換）
- **total_tokens**: `200k` → `200000`
- **used_percent**: `21`（%の数値）

また、カテゴリ別の内訳も抽出（可能な範囲で）：
- **Messages トークン数**
- **Free space トークン数**

### Step 4: 結果を JSON に保存

```bash
mkdir -p /Users/naoto.hamada/github/ham/claude-code-context-experiment/calibration
```

以下を `calibration/calibration_{level_name}.json` に Write ツールで保存：

```json
{
  "level": "{level_name}",
  "nominal_percent": {nominal},
  "chunks_read": {chunks},
  "measured_used_tokens": {used_tokens},
  "measured_total_tokens": {total_tokens},
  "measured_percent": {used_percent},
  "messages_tokens": {messages_tokens_or_null},
  "free_tokens": {free_tokens_or_null},
  "timestamp": "{ISO8601}",
  "note": "Measured in main CLI window with /context command"
}
```

### Step 5: 次のステップを案内

残りのレベルを確認し、案内を表示：

```
## ✅ {level_name} 測定完了

結果: {chunks_read} chunks → 実測 {measured_percent}%（名目 {nominal_percent}%）

## 進捗

| Level    | Chunks | Status |
|----------|--------|--------|
| baseline | 0      | ✅ XX% |
| 30%      | 48     | ✅ XX% |
| 50%      | 80     | ⬜ 未測定 |  ← 次
| 80%      | 128    | ⬜ 未測定 |
| 90%      | 144    | ⬜ 未測定 |

### 次のステップ

1. `/clear` でコンテキストをクリア
2. `/run-calibration-all` で次のレベルを自動実行
```

**全レベル完了の場合**: Step 6 に進む。

### Step 6: キャリブレーションテーブル生成

全5レベルの JSON を読み込み、`calibration/README.md` にサマリーテーブルを生成：

```markdown
# Context Calibration Table

チャンク数と実際のコンテキストウィンドウ占有率のマッピングテーブル。
メインCLIウィンドウで `/context` コマンドにより実測。

## Results

| Level | Chunks | Nominal % | Measured % | Used Tokens | Total Tokens | Delta | Date |
|-------|--------|-----------|------------|-------------|--------------|-------|------|
| baseline | 0 | 0% | XX.X% | XXk | 200k | +XX.X% | YYYY-MM-DD |
| 30% | 48 | 30% | XX.X% | XXk | 200k | +XX.X% | YYYY-MM-DD |
| 50% | 80 | 50% | XX.X% | XXk | 200k | +XX.X% | YYYY-MM-DD |
| 80% | 128 | 80% | XX.X% | XXk | 200k | +XX.X% | YYYY-MM-DD |
| 90% | 144 | 90% | XX.X% | XXk | 200k | +XX.X% | YYYY-MM-DD |

Delta = Measured % - Nominal %（固定オーバーヘッドと会話による差分）

## Notes

- Measured in main CLI window (claude-opus-4-6, 200k context)
- Agent workers have similar but not identical overhead (different system tools, no skills)
- Autocompact buffer size varies; measurements are approximate
- Each level measured in a fresh session after `/clear`
```

完了メッセージ：

```
## 🎉 全レベルのキャリブレーション完了！

calibration/README.md にサマリーテーブルを生成しました。
各レベルの詳細は calibration/calibration_{level}.json を参照してください。
```

## 注意事項

- `/context` の出力にはANSIカラーコードが含まれます。数値の抽出時に注意してください
- トークン数の表記: `41k` = 41000, `200k` = 200000, `21.9k` = 21900 のように変換
- Autocompact buffer は可変のため、測定値は参考値です
- 同一セッションで複数レベルを測定しないでください（前のチャンクが残るため）
- `/clear` 後はコマンド名 `/run-calibration-all` だけ入力すれば自動的に次のレベルに進みます
