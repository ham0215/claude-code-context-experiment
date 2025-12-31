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
│   ├── experiment_runner.py          # 実験ランナー（単一プロンプト方式）
│   ├── analyze_results.py            # 結果分析
│   ├── validate_local.py             # 検証ロジック
│   └── generate_noise_chunks.py      # ノイズチャンク生成
├── noise_chunks/                     # コンテキスト消費用ノイズファイル（200個）
├── prompts/
│   └── implementation_prompt.txt     # 実装依頼プロンプト
└── results/                          # 結果保存（.gitignoreで除外）
```

---

## 実験手法

### 単一プロンプト方式

コンテキスト消費をシミュレートするため、ノイズコンテンツを直接プロンプトに含める方式を採用。

```
[ノイズチャンク1]
[ノイズチャンク2]
...
[ノイズチャンクN]

docs/fizzbuzz_spec.md を読んで、src/fizzbuzz.py を実装してください。
```

### コンテキストレベル

| 条件名 | チャンク数 | 目標消費率 |
|--------|-----------|-----------|
| 30% | 48 | ~30% |
| 50% | 80 | ~50% |
| 80% | 128 | ~80% |

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

```bash
# 実験実行
cd scripts && python experiment_runner.py

# 結果分析
python analyze_results.py
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

---

## 出力レポート例

```
======================================================================
コンテキスト消費影響実験 - 結果レポート
======================================================================

【条件別サマリー】

Level       N   Target   Actual  Pass Rate   Secret   Hidden     Time
------------------------------------------------------------------------------
30%         5    30.0%    30.7%     100.0%     1.00     0.75    45.2s
50%         5    50.0%    51.2%      80.0%     0.93     0.50    58.3s
80%         5    80.0%    81.7%      60.0%     0.87     0.25    89.1s

【隠し指示の遵守率】

30%:
  _sorted_divisors変数名         ████████████████████ 100.0%
  STATS_VERSION定数              ████████████████░░░░  80.0%
  ...
```

---

## 制限事項

- コンテキスト消費量の正確な制御は困難（±2%の誤差を許容）
- Claude Code のバージョンアップにより結果が変わる可能性
- 応答時間にはClaudeの入力トークン処理時間を含む

---

## 変更履歴

| 日付 | バージョン | 変更内容 |
|------|------------|----------|
| 2024-12-31 | 2.0 | 単一プロンプト方式に変更、フォーマッター関数追加、隠し指示チェック追加 |
| 2024-12-26 | 1.0 | 初版作成 |
