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
├── docs/
│   └── fizzbuzz_spec.md              # 設計書（9関数+隠し指示）
├── tests/
│   └── test_fizzbuzz.py              # テストコード
├── scripts/
│   ├── analyze_results.py            # 結果分析
│   ├── validate_local.py             # 検証ロジック
│   ├── generate_noise_chunks.py      # ノイズチャンク生成
│   └── generate_context_claudemd.py  # CLAUDE.md バリアント生成
├── noise_chunks/                     # コンテキスト消費用ノイズファイル
├── claude_md_variants/               # レベル別 CLAUDE.md バリアント
│   ├── CLAUDE.md.original            # オリジナル（ノイズなし）
│   ├── CLAUDE.md.30pct               # 30% コンテキスト消費用
│   ├── CLAUDE.md.50pct               # 50% コンテキスト消費用
│   └── CLAUDE.md.80pct               # 80% コンテキスト消費用
├── prompts/
│   └── implementation_prompt.txt     # 実装依頼プロンプト
├── .claude/
│   ├── agents/
│   │   ├── experiment-team-worker.md # チームワーカーエージェント
│   │   └── commit-creator.md         # コミット作成エージェント
│   └── commands/
│       └── run-experiment-team.md    # チームベース実験実行スキル
├── CLAUDE.md                         # 実験時はバリアントに切り替え
├── workspaces/                       # 試行別ワークスペース（.gitignoreで除外）
│   └── trial_{level}_{number}/
│       └── src/fizzbuzz.py
└── results/                          # 結果保存（.gitignoreで除外）
```

---

## 実験手法

### コンテキスト注入方式

ルートの `CLAUDE.md` をレベル別のバリアントに切り替えることで、ワーカー起動時に自動的にコンテキストが消費される。ワーカー側でのチャンク読み込みは不要。

### コンテキストレベル

| レベル | CLAUDE.md バリアント | 目標消費率 |
|--------|---------------------|-----------|
| 30%    | `claude_md_variants/CLAUDE.md.30pct` | ~30% |
| 50%    | `claude_md_variants/CLAUDE.md.50pct` | ~50% |
| 80%    | `claude_md_variants/CLAUDE.md.80pct` | ~80% |

### 実行アーキテクチャ

Claude Code のチーム機能（TeamCreate / TaskCreate / SendMessage）を使用：

1. チームリーダーが CLAUDE.md を切り替え、`/context` でコンテキスト消費量を検証
2. タスクを事前登録し、各ワーカーに1対1で割り当て
3. ワーカーを並列起動（1トライアル1ワーカー）
4. 各ワーカーが独立したコンテキストで FizzBuzz 実装タスクを実行
5. 結果を `results/trial_*.json` に個別保存

---

## 実行方法

### 事前準備

```bash
# 依存関係のインストール
pip install -r requirements.txt

# ノイズチャンクの生成（初回のみ）
python scripts/generate_noise_chunks.py

# CLAUDE.md バリアントの生成（初回のみ）
python scripts/generate_context_claudemd.py --all
```

### 実験実行

Claude Code で以下のスキルを実行：

```
/run-experiment-team
```

パラメータの入力を求められるので、以下を指定：

1. **コンテキストレベル**: `30%`, `50%`, `80%` のいずれか
2. **試行範囲**: 開始番号と終了番号（例: 1-5）
3. **ワーカー数**: 同時起動するワーカー数（推奨: 試行数と同数）

**実行フロー:**

1. CLAUDE.md を対象レベルのバリアントに切り替え確認
2. `/context` でコンテキスト消費量を検証（許容範囲外なら中断）
3. チーム作成 → タスク登録 → ワーカー並列起動
4. 全ワーカー完了後、クリーンアップ → 結果集計

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

### 5. コンテキスト測定
- `measured_context_percent`: チームリーダーが `/context` で測定した消費率
- `target_context_percent`: 目標コンテキスト消費率

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

【隠し指示の遵守率】

30%:
  _sorted_divisors変数名         ████████████████████ 100.0%
  STATS_VERSION定数              ████████████████████ 100.0%
  ...
```

---

## 制限事項

- コンテキスト消費量の正確な制御は困難（±数%の誤差を許容）
- Claude Code のバージョンアップにより結果が変わる可能性
- 応答時間にはClaudeの入力トークン処理時間を含む
- 80%超のコンテキスト消費はautocompactにより正確な測定が困難

---

## 変更履歴

| 日付 | バージョン | 変更内容 |
|------|------------|----------|
| 2026-02-14 | 4.0 | CLAUDE.md バリアント方式に移行、チームベース実行に一本化 |
| 2026-02-01 | 3.1 | ワークスペース分離、/context測定、1試行1エージェント必須化 |
| 2025-02-01 | 3.0 | サブエージェントによる並列実行サポート追加、CLI引数対応 |
| 2024-12-31 | 2.1 | 段階的アプローチ実装、詳細エラー記録追加 |
| 2024-12-31 | 2.0 | 単一プロンプト方式に変更、フォーマッター関数追加、隠し指示チェック追加 |
| 2024-12-26 | 1.0 | 初版作成 |
