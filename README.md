# コンテキスト消費がClaude Codeの挙動に与える影響の検証実験

## 実験概要

### 目的

Claude Codeにおけるコンテキストウィンドウの消費量が、以下の指標に与える影響を定量的に検証する。

- 実装タスクの成功率
- 仕様書の指示遵守率（特に中間部分に埋め込まれた指示）
- 応答時間

### 仮説

| 仮説 | 内容 |
|------|------|
| H1 | コンテキスト消費量が増加すると、テスト成功率が低下する |
| H2 | コンテキスト消費量が増加すると、仕様書中間部分の指示遵守率が低下する |
| H3 | コンテキスト消費量が増加すると、応答時間が増加する |
| H4 | 複数関数の実装において、後半の関数ほど品質が低下する |

---

## 実験タスク

### FizzBuzz拡張実装（9関数）

| 関数 | 概要 |
|------|------|
| `fizzbuzz` | 基本のFizzBuzz判定 |
| `fizzbuzz_range` | 範囲指定のFizzBuzz |
| `fizzbuzz_custom` | カスタムルールでの判定 |
| `fizzbuzz_stats` | 統計情報の集計 |
| `fizzbuzz_generator` | 無限ジェネレーター |
| `fizzbuzz_json` | JSON形式出力 |
| `fizzbuzz_csv` | CSV形式出力 |
| `fizzbuzz_markdown_table` | Markdown表形式出力 |
| `fizzbuzz_grouped` | タイプ別グループ化 |

### 隠し指示チェック（8項目）

仕様書の中間部分に埋め込まれた指示をClaudeが遵守するかを検証：

| 対象関数 | 隠し指示 |
|----------|----------|
| `fizzbuzz_custom` | `_sorted_divisors` 変数名を使用 |
| `fizzbuzz_stats` | `STATS_VERSION = "1.0"` 定数を定義 |
| `fizzbuzz_stats` | `# Uses STATS_VERSION` コメント |
| `fizzbuzz_generator` | docstringに `infinite sequence` を含める |
| `fizzbuzz_json` | `ensure_ascii=False` オプション |
| `fizzbuzz_csv` | `_header_row` 変数名を使用 |
| `fizzbuzz_markdown_table` | `_format_table_row` ヘルパー関数 |
| `fizzbuzz_grouped` | `GROUP_KEYS` 定数を定義 |

### 秘密メッセージ（プロンプト指示）

| 項目 | 内容 |
|------|------|
| ヘッダー | `# EXPERIMENT-ID: MAGIC-7392` |
| フッター | `# Verified: BLUE-ELEPHANT` |
| 各関数docstring | `ref: XYZ-999` |

---

## ディレクトリ構成

```
claude-code-context-experiment/
├── src/
│   └── fizzbuzz.py                   # 実装対象（毎回削除、.gitignoreで除外）
├── docs/
│   └── fizzbuzz_spec.md              # 設計書（9関数+隠し指示）
├── tests/
│   └── test_fizzbuzz.py              # テストコード
├── scripts/
│   ├── experiment_runner.py          # 実験ランナー（単一/バッチ/並列対応）
│   ├── analyze_results.py            # 結果分析
│   ├── validate_local.py             # 検証ロジック
│   └── generate_noise_chunks.py      # ノイズチャンク生成
├── noise_chunks/                     # コンテキスト消費用ノイズファイル（200個）
├── prompts/
│   └── implementation_prompt.txt     # 実装依頼プロンプト
├── .claude/
│   ├── agents/
│   │   └── context-experiment-runner.md  # 並列実行用サブエージェント
│   └── commands/
│       └── run-experiment-parallel.md    # 並列実行スキル
├── workspaces/                       # 試行別ワークスペース（並列実行時、.gitignoreで除外）
│   └── trial_{level}_{number}/
│       └── src/fizzbuzz.py
└── results/                          # 結果保存（.gitignoreで除外）
```

---

## 実験手法

### 単一プロンプト方式（30%, 50%, 80%）

コンテキスト消費をシミュレートするため、ノイズコンテンツを直接プロンプトに含める方式を採用。

```
[ノイズチャンク1]
[ノイズチャンク2]
...
[ノイズチャンクN]

docs/fizzbuzz_spec.md を読んで、src/fizzbuzz.py を実装してください。
```

### 段階的アプローチ（90%以上）

Claude CLIには `Prompt is too long` というプロンプト長制限があり、約92%以上のコンテキストで単一プロンプト方式が失敗する。これを回避するため、`--resume` オプションを使用した段階的コンテキスト構築を採用。

```
[Batch 1] → 20 chunks → session_id取得
[Batch 2] → 20 chunks → --resume session_id で継続
...
[Batch N] → 残りのchunks
[Final]   → タスク送信 → コード生成
```

**特徴：**
- 20チャンクずつバッチで送信
- 各バッチで「確認しました」のみ応答を要求
- セッションIDを引き継いでコンテキストを蓄積
- 最後にタスクを送信してコード生成

### コンテキストレベル

| 条件名 | チャンク数 | 目標消費率 | 方式 |
|--------|-----------|-----------|------|
| 30% | 48 | ~30% | 単一プロンプト |
| 50% | 80 | ~50% | 単一プロンプト |
| 80% | 128 | ~80% | 単一プロンプト |
| 90% | 144 | ~90% | 段階的アプローチ |

---

## 実行方法

### 事前準備

```bash
# 依存関係のインストール
pip install -r requirements.txt

# ノイズチャンクの生成（初回のみ）
python scripts/generate_noise_chunks.py
```

### 実験実行

#### 方法1: 並列実行（推奨）

Claude Codeのサブエージェント機能を使用して、独立したコンテキストで並列実行。

```bash
# Claude Codeでスキルを実行
/run-experiment-parallel
```

各サブエージェントが独立したコンテキストを持つため、実験の目的（コンテキスト消費の影響検証）に最適。

**並列実行の仕組み:**
- `context-experiment-runner` エージェントを複数同時起動
- **1試行1エージェント（MUST）**: コンテキスト分離を保証するため、各エージェントは1試行のみ実行
- **ワークスペース分離**: 各試行は `workspaces/trial_{level}_{number}/` に実装を生成（ファイル競合防止）
- **コンテキスト測定**: `/context` コマンドで実際の消費量を記録
- 結果は `results/trial_*.json` に個別保存

#### 方法2: 単一試行/バッチ実行

```bash
# 単一試行（例: 30%レベル、試行1）
python scripts/experiment_runner.py --single --level "30%" --trial 1

# バッチ実行（例: 30%レベル、試行1-10）
python scripts/experiment_runner.py --batch --level "30%" --batch-start 1 --batch-end 10

# 対話型フル実行（直列、400試行）
python scripts/experiment_runner.py
```

### 結果分析

```bash
python scripts/analyze_results.py
```

---

## 検証項目

### 1. テスト成功率
- pytest による全テストケースの成功/失敗

### 2. 秘密スコア（0.0〜1.0）
- ヘッダー、フッター、ref タグの存在確認

### 3. 隠し指示スコア（0.0〜1.0）
- 8つの隠し指示の遵守率

### 4. 関数別成功率
- 9つの関数それぞれの実装成否

### 5. コンテキスト測定（/context コマンド）
- `context_used_tokens`: 使用トークン数
- `context_total_tokens`: 総トークン数
- `context_percent`: 消費率（%）
- `context_raw_output`: `/context` コマンドの生出力

### 6. 詳細エラー情報
- `cli_returncode`: CLIの終了コード
- `cli_stderr`: 標準エラー出力
- `cli_stdout_preview`: 標準出力のプレビュー
- `use_incremental`: 段階的アプローチ使用フラグ
- `session_id`: CLIセッションID

---

## 出力レポート例

```
======================================================================
コンテキスト消費影響実験 - 結果レポート
======================================================================

【条件別サマリー】

Level       N   Target   Actual  Pass Rate   Secret   Hidden     Time
------------------------------------------------------------------------------
30%         5    30.0%    30.9%    100.0%     1.00     1.00    60.5s
50%         5    50.0%    51.4%    100.0%     1.00     1.00    71.2s
80%         5    80.0%    81.9%    100.0%     1.00     1.00    95.9s
90%         5    90.0%    92.1%    100.0%     1.00     1.00   137.1s

【隠し指示の遵守率】

30%:
  _sorted_divisors変数名         ████████████████████ 100.0%
  STATS_VERSION定数              ████████████████████ 100.0%
  ...
```

---

## 制限事項

- コンテキスト消費量の正確な制御は困難（±2%の誤差を許容）
- Claude Code のバージョンアップにより結果が変わる可能性
- 応答時間にはClaudeの入力トークン処理時間を含む
- **CLI制限**: 単一プロンプトは約92%で `Prompt is too long` エラー

---

## 変更履歴

| 日付 | バージョン | 変更内容 |
|------|------------|----------|
| 2026-02-01 | 3.1 | ワークスペース分離、/context測定、1試行1エージェント必須化 |
| 2025-02-01 | 3.0 | サブエージェントによる並列実行サポート追加、CLI引数対応 |
| 2024-12-31 | 2.1 | 90%コンテキストレベル追加、段階的アプローチ実装、詳細エラー記録追加 |
| 2024-12-31 | 2.0 | 単一プロンプト方式に変更、フォーマッター関数追加、隠し指示チェック追加 |
| 2024-12-26 | 1.0 | 初版作成 |
