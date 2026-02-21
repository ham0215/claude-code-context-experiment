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

### 隠し指示チェック（9項目）

仕様書またはCLAUDE.mdに埋め込まれた指示をClaudeが遵守するかを検証：

| 対象関数 | 隠し指示 | 出典 |
|----------|----------|------|
| `fizzbuzz_custom` | `_sorted_divisors` 変数名を使用 | CLAUDE.mdのみ |
| `fizzbuzz_stats` | `STATS_VERSION = "1.0"` 定数を定義 | 仕様書 |
| `fizzbuzz_stats` | `# Uses STATS_VERSION` コメント | 仕様書 |
| `fizzbuzz_generator` | docstringに `infinite sequence` を含める | 仕様書 |
| `fizzbuzz_json` | `ensure_ascii=False` オプション | 仕様書 |
| `fizzbuzz_csv` | `_header_row` 変数名を使用 | 仕様書 |
| `fizzbuzz_markdown_table` | `_format_table_row` ヘルパー関数 | 仕様書 |
| `fizzbuzz_grouped` | `GROUP_KEYS` 定数を定義 | 仕様書 |
| 全関数 | NumPy形式docstring（Google形式は禁止） | CLAUDE.mdのみ |

**「CLAUDE.mdのみ」の項目について:**

タスクプロンプトにはCLAUDE.mdへの言及がなく、仕様書にも記載されていない。Claudeがコンテキスト内のCLAUDE.md規約を自発的に読み取り・遵守するかを測定する。特にNumPy形式docstringはClaudeのデフォルト（Google形式）と競合するため、コンテキスト消費量が増えるほど無視されやすいことが期待される。

### 秘密メッセージ（CLAUDE.md埋め込み）

CLAUDE.mdのノイズチャンク内に「プロジェクト規約」として埋め込まれた指示：

| 項目 | 内容 | 埋め込み位置 |
|------|------|-------------|
| ヘッダー | `# EXPERIMENT-ID: MAGIC-7392` | 20% |
| 変数命名規約 | `_sorted_divisors` プレフィックス | 35% |
| docstring参照タグ | `ref: XYZ-999` | 45% |
| docstring形式 | NumPy形式を必須、Google形式を禁止 | 60% |
| フッター | `# Verified: BLUE-ELEPHANT` | 80% |

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
│   ├── verify_trials.py              # トライアル検証（テスト実行+スコア付与）
│   ├── hide_test_files.sh            # テスト/検証ファイル隠蔽（カンニング防止）
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
│       ├── run-experiment-team.md    # チームベース実験実行スキル
│       └── verify-and-analyze.md     # 検証・集計スキル
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

### 設計上の工夫（v4.2）

タスクプロンプトからCLAUDE.mdへの明示的言及を排除し、Claudeが自発的にCLAUDE.md規約を遵守するかを測定する。また、Claudeの学習デフォルト（Google形式docstring）と競合する指示をCLAUDE.mdに埋め込むことで、コンテキスト消費量による注意力低下を検出しやすくした。

### コンテキストレベル

| レベル | CLAUDE.md バリアント | 目標消費率 |
|--------|---------------------|-----------|
| 30%    | `claude_md_variants/CLAUDE.md.30pct` | ~30% |
| 50%    | `claude_md_variants/CLAUDE.md.50pct` | ~50% |
| 80%    | `claude_md_variants/CLAUDE.md.80pct` | ~80% |

### 実行アーキテクチャ

Claude Code のチーム機能（TeamCreate / TaskCreate / SendMessage）を使用：

1. チームリーダーが CLAUDE.md を切り替え、テスト/検証ファイルを隠蔽
2. `/context` でコンテキスト消費量を検証
3. タスクを事前登録し、各ワーカーに1対1で割り当て
4. ワーカーを並列起動（1トライアル1ワーカー）
5. 各ワーカーが独立したコンテキストで FizzBuzz 実装タスクを実行
6. 結果を `results/trial_*.json` に個別保存
7. 手動で `git checkout` を実行し CLAUDE.md とテスト/検証ファイルを復元、Claude Code を再起動
8. `/verify-and-analyze` でテスト・集計

### カンニング防止

ワーカーがテストファイルや検証スクリプトを読み取って「正解」を知ることを防止する仕組み:

| 防御層 | 手段 | 効果 |
|--------|------|------|
| ファイル隠蔽 | `scripts/hide_test_files.sh` でワーキングツリーから削除 | `Read` ツールでファイルを読めない |
| git コマンド禁止 | ワーカーエージェントの `disallowedTools: Bash(git *)` | `git checkout` 等による復元をシステムレベルで拒否 |

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
2. テスト/検証ファイルをワーキングツリーから隠蔽（カンニング防止）
3. `/context` でコンテキスト消費量を検証（許容範囲外なら中断）
4. チーム作成 → タスク登録 → ワーカー並列起動
5. 全ワーカー完了後、クリーンアップ
6. **手動で `git checkout` を実行して CLAUDE.md とテスト/検証ファイルを復元**
7. **Claude Code を再起動**（CLAUDE.md の変更を反映するため）
8. `/verify-and-analyze` で検証・集計

### 検証・集計

実験完了後、ファイルを復元してから検証・集計を実行:

```bash
# 1. ファイル復元
git checkout HEAD -- CLAUDE.md tests/test_fizzbuzz.py tests/test_validate_local.py tests/test_analyze_results.py tests/conftest.py scripts/verify_trials.py scripts/validate_local.py scripts/analyze_results.py

# 2. Claude Code を再起動

# 3. 検証・集計スキルを実行
/verify-and-analyze
```

**実行内容:**

1. `scripts/verify_trials.py` で各トライアルのテスト・検証を実行（結果JSONにスコアを付与）
2. `scripts/analyze_results.py` で集計レポートを生成

---

## 検証項目

### 1. テスト成功率
- pytest による全テストケースの成功/失敗

### 2. 秘密スコア（0.0〜1.0）
- ヘッダー、フッター、ref タグの存在確認

### 3. 隠し指示スコア（0.0〜1.0）
- 9つの隠し指示の遵守率（うち2つはCLAUDE.mdのみに記載）

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
