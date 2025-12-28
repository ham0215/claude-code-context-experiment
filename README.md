# コンテキスト消費がClaude Codeの挙動に与える影響の検証実験

## 1. 実験概要

### 1.1 目的

Claude Codeにおけるコンテキストウィンドウの消費量が、以下の指標に与える影響を定量的に検証する。

- 実装タスクの成功率
- 初期指示の記憶保持率（コンテキストドリフト）
- 応答時間

### 1.2 仮説

| 仮説 | 内容 |
|------|------|
| H1 | コンテキスト消費量が増加すると、テスト成功率が低下する |
| H2 | コンテキスト消費量が増加すると、初期指示の記憶率が低下する |
| H3 | コンテキスト消費量が増加すると、応答時間が増加する |
| H4 | 複数関数の実装において、後半の関数ほど品質が低下する |

---

## 2. 実験条件

### 2.1 コンテキストレベル

| 条件名 | 目標範囲 | 試行数 |
|--------|----------|--------|
| 20% | 15-25% | 100回 |
| 40% | 35-45% | 100回 |
| 60% | 55-65% | 100回 |
| 80% | 75-85% | 100回 |

**合計: 400試行**

### 2.2 ランダム化

- 全400試行の実行順序をランダム化
- 時間帯による影響を分散させる

---

## 3. ディレクトリ構成

```
claude-code-context-experiment/
├── .claude/
│   └── settings.json                 # Claude Code設定（tests/を読み取り禁止）
├── src/
│   └── fizzbuzz.py                   # 実装対象（毎回削除）
├── docs/
│   └── fizzbuzz_spec.md              # 設計書（Claudeが参照）
├── tests/
│   └── test_fizzbuzz.py              # テストコード（Claudeは読めない）
│
├── scripts/                          # 実験スクリプト
│   ├── experiment_runner.py          # メイン実行スクリプト
│   ├── context_controller.py         # コンテキスト調整
│   ├── validate_local.py             # 検証ロジック
│   ├── analyze_results.py            # 結果分析
│   └── calibration.py                # 事前キャリブレーション
│
├── noise_chunks/                     # コンテキスト消費用ノイズファイル
│   ├── chunk_0.txt
│   ├── chunk_1.txt
│   └── ...
│
├── prompts/
│   ├── implementation_prompt.txt     # 実装依頼プロンプト
│   └── noise_prompt_template.txt     # ノイズ投入用テンプレート
│
└── results/                          # 結果保存（.gitignoreで除外）
    ├── results.json                  # 全結果の累積
    ├── trial_20%_001.json            # 個別試行結果
    └── analysis_chart.png            # 分析グラフ
```

---

## 4. 設定ファイル

### 4.1 .claude/settings.json

```json
{
  "permissions": {
    "deny": [
      "Read(tests/**)",
      "View(tests/**)",
      "Glob(tests/**)",
      "Grep(tests/**)"
    ]
  }
}
```

**目的**: テストコードをClaudeが参照できないようにし、テストに基づいた「カンニング」を防止する。

### 4.2 .gitignore

```gitignore
# 実験結果（git管理外で保持）
results/
*.log

# Python
__pycache__/
*.pyc
.pytest_cache/

# 一時ファイル
*.tmp
```

---

## 5. 実装タスク仕様

### 5.1 docs/fizzbuzz_spec.md

```markdown
# FizzBuzz拡張仕様書

## 概要

FizzBuzzの基本機能と拡張機能を実装する。

## 実装する関数一覧

### 1. fizzbuzz(n: int) -> str

基本のFizzBuzz判定を行う。

- 3の倍数: "Fizz"
- 5の倍数: "Buzz"
- 15の倍数: "FizzBuzz"
- それ以外: 数字を文字列で返す

**例外処理**: n が負の数または0の場合は `ValueError` を送出

### 2. fizzbuzz_range(start: int, end: int) -> list[str]

指定範囲のFizzBuzz結果をリストで返す。

- start から end まで（両端含む）
- start > end の場合は空リストを返す

### 3. fizzbuzz_custom(n: int, rules: dict[int, str]) -> str

カスタムルールでFizzBuzz判定を行う。

- rules: {除数: 出力文字列} の辞書
- 複数ルールに該当する場合は、除数の小さい順に連結
- どのルールにも該当しない場合は数字を文字列で返す

**例**:
```python
fizzbuzz_custom(15, {3: "Fizz", 5: "Buzz"})  # -> "FizzBuzz"
fizzbuzz_custom(7, {7: "Seven"})              # -> "Seven"
```

### 4. fizzbuzz_stats(start: int, end: int) -> dict[str, int]

指定範囲のFizzBuzz統計情報を返す。

**戻り値**:
```python
{
    "fizz": int,      # "Fizz"の出現回数
    "buzz": int,      # "Buzz"の出現回数
    "fizzbuzz": int,  # "FizzBuzz"の出現回数
    "number": int     # 数字の出現回数
}
```

### 5. fizzbuzz_generator(start: int = 1) -> Generator[str, None, None]

FizzBuzz結果を返す無限ジェネレーター。

- start から開始し、1ずつ増加
- `StopIteration` は発生しない（無限）

## 共通仕様

- すべての関数で型ヒントを使用すること
- すべての関数にdocstringを記述すること
- 入力値バリデーションを適切に行うこと
- PEP 8スタイルに準拠すること
```

### 5.2 実装例（期待される出力）

```python
# src/fizzbuzz.py
# EXPERIMENT-ID: MAGIC-7392

"""FizzBuzz implementation module with extended functionality."""

from typing import Generator


def fizzbuzz(n: int) -> str:
    """
    Return FizzBuzz result for a single number.

    Args:
        n: A positive integer to evaluate

    Returns:
        "Fizz", "Buzz", "FizzBuzz", or the number as string

    Raises:
        ValueError: If n is less than or equal to 0

    ref: XYZ-999
    """
    if n <= 0:
        raise ValueError("n must be a positive integer")

    if n % 15 == 0:
        return "FizzBuzz"
    elif n % 3 == 0:
        return "Fizz"
    elif n % 5 == 0:
        return "Buzz"
    else:
        return str(n)


def fizzbuzz_range(start: int, end: int) -> list[str]:
    """
    Return FizzBuzz results for a range of numbers.

    ref: XYZ-999
    """
    # ... 実装 ...


def fizzbuzz_custom(n: int, rules: dict[int, str]) -> str:
    """
    Return FizzBuzz result with custom rules.

    ref: XYZ-999
    """
    # ... 実装 ...


def fizzbuzz_stats(start: int, end: int) -> dict[str, int]:
    """
    Return statistics for FizzBuzz results in a range.

    ref: XYZ-999
    """
    # ... 実装 ...


def fizzbuzz_generator(start: int = 1) -> Generator[str, None, None]:
    """
    Generate infinite FizzBuzz sequence.

    ref: XYZ-999
    """
    # ... 実装 ...


# Verified: BLUE-ELEPHANT
```

---

## 6. 秘密メッセージ（コンテキストドリフト検証）

### 6.1 指示内容

実装依頼時に以下の指示を含める。

| 項目 | 指示内容 | 埋め込み場所 |
|------|----------|--------------|
| ヘッダーID | `EXPERIMENT-ID: MAGIC-7392` | ファイル先頭コメント |
| フッター検証 | `Verified: BLUE-ELEPHANT` | ファイル末尾コメント |
| 関数タグ | `ref: XYZ-999` | 各関数のdocstring内 |

### 6.2 検証方法

```python
def validate_secrets(filepath: Path, expected_functions: int = 5) -> dict:
    content = filepath.read_text()

    return {
        "has_header": "EXPERIMENT-ID: MAGIC-7392" in content,
        "has_footer": "Verified: BLUE-ELEPHANT" in content,
        "ref_count": content.count("ref: XYZ-999"),
        "expected_refs": expected_functions
    }
```

### 6.3 秘密スコア計算

```
secret_score = (has_header + has_footer + min(ref_count/expected_refs, 1.0)) / 3
```

| スコア | 解釈 |
|--------|------|
| 1.0 | 完全記憶（全指示を遵守） |
| 0.67-0.99 | 部分的ドリフト |
| 0.34-0.66 | 重度のドリフト |
| 0-0.33 | ほぼ完全忘却 |

---

## 7. 実装依頼プロンプト

### 7.1 prompts/implementation_prompt.txt

```markdown
docs/fizzbuzz_spec.md を読んで、src/fizzbuzz.py を実装してください。

## 必ず守る指示

1. ファイルの先頭に以下のコメントを必ず含めること:
   `# EXPERIMENT-ID: MAGIC-7392`

2. ファイルの末尾に以下のコメントを必ず含めること:
   `# Verified: BLUE-ELEPHANT`

3. すべての関数のdocstringに以下を必ず含めること:
   `ref: XYZ-999`

4. 仕様書に記載された5つの関数をすべて実装すること

5. テストファイルは参照せず、仕様書のみに基づいて実装すること
```

---

## 8. コンテキスト制御

### 8.1 事前キャリブレーション

実験前に、ノイズチャンク1つあたりのコンテキスト消費量を測定する。

```python
def calibrate() -> float:
    """1チャンクあたりの平均コンテキスト増加率を返す"""
    clear_context()
    baseline = get_context_percent()

    increases = []
    for i in range(10):
        before = get_context_percent()
        inject_noise_chunk(i)
        after = get_context_percent()
        increases.append(after - before)

        if after > 85:
            break

    return sum(increases) / len(increases)
```

### 8.2 目標範囲への調整

```python
def adjust_to_target(target_min: int, target_max: int) -> int:
    """目標範囲に到達するまでノイズを投入"""

    clear_context()
    current = get_context_percent()
    chunk_id = 0

    while current < target_min:
        inject_noise_chunk(chunk_id)
        current = get_context_percent()
        chunk_id += 1

        # オーバーシュート時はリトライ
        if current > target_max:
            return adjust_to_target(target_min, target_max)

    return current
```

### 8.3 ノイズチャンクの内容

各チャンクは約10,000トークン相当のテキスト。内容は実験タスクと無関係なもの（例: Lorem ipsum、技術ドキュメントの抜粋など）。

---

## 9. 測定項目

### 9.1 主要指標

| 指標 | 測定方法 | 単位 |
|------|----------|------|
| テスト成功率 | pytest の exit code | bool |
| 秘密スコア | ファイル内検索 | 0.0-1.0 |
| 応答時間 | タスク開始から完了まで | 秒 |

### 9.2 補助指標

| 指標 | 測定方法 | 単位 |
|------|----------|------|
| 開始時コンテキスト | /context コマンド | % |
| 終了時コンテキスト | /context コマンド | % |
| テスト通過数 | pytest 詳細出力 | 個 |
| 関数別成功 | テスト結果パース | bool×5 |

### 9.3 結果データ構造

```json
{
  "trial_id": "40%_042",
  "context_level": "40%",
  "context_actual_start": 38,
  "context_actual_end": 52,
  "timestamp": "2025-12-26T10:30:00Z",
  "elapsed_seconds": 18.5,

  "test_passed": true,
  "tests_total": 25,
  "tests_passed": 25,

  "secret_header": true,
  "secret_footer": true,
  "secret_refs": 5,
  "secret_score": 1.0,

  "func_results": {
    "fizzbuzz": true,
    "fizzbuzz_range": true,
    "fizzbuzz_custom": true,
    "fizzbuzz_stats": true,
    "fizzbuzz_generator": true
  }
}
```

---

## 10. 実験手順

### 10.1 事前準備

1. リポジトリのセットアップ
2. `.claude/settings.json` でテストコードへのアクセスを禁止
3. キャリブレーション実行（ノイズ量の調整）
4. ノイズチャンクファイルの生成

### 10.2 各試行の流れ

```
1. 実装ファイル削除 (rm src/fizzbuzz.py)
2. Claudeコンテキストクリア (/clear)
3. コンテキストを目標レベルに調整（ノイズ投入）
4. 開始時コンテキスト記録
5. 実装依頼プロンプト実行
6. 終了時コンテキスト記録
7. pytest実行
8. 秘密メッセージ検証
9. 結果をJSONに保存
10. 次の試行へ
```

### 10.3 実行コマンド

```bash
# キャリブレーション
python scripts/calibration.py

# 実験実行（約3-6時間）
python scripts/experiment_runner.py

# 結果分析
python scripts/analyze_results.py
```

---

## 11. 統計分析

### 11.1 検定手法

| 分析内容 | 検定手法 | 有意水準 |
|----------|----------|----------|
| 条件間の成功率比較 | カイ二乗検定 | α = 0.05 |
| 秘密スコアの比較 | t検定 / Mann-Whitney U | α = 0.05 |
| コンテキストと成功率の傾向 | 線形回帰 | α = 0.05 |
| 極端条件の比較 (20% vs 80%) | カイ二乗検定 | α = 0.05 |

### 11.2 効果量

- オッズ比（成功率の比較）
- Cohen's d（連続変数の比較）
- R²（傾向の説明力）

### 11.3 出力レポート

```
======================================================================
コンテキスト消費影響実験 - 結果レポート
======================================================================

【条件別サマリー】
              test_passed              secret_score
                      sum count  mean         mean   std
context_level
20%                    95   100  0.95        0.92  0.09
40%                    91   100  0.91        0.87  0.11
60%                    84   100  0.84        0.79  0.13
80%                    72   100  0.72        0.65  0.19

【テスト成功率の傾向分析】
  傾き: -0.0038 (コンテキスト1%増加あたり)
  R²: 0.987
  p値: 0.0064
  結論: コンテキスト増加に伴い成功率が有意に低下

【20% vs 80% の比較】
  成功率差: 23ポイント
  χ² = 18.45
  p < 0.001
  結論: 有意差あり

【秘密メッセージ記憶率】
  20%条件: 92.3%
  80%条件: 65.4%
  t = 8.72, p < 0.001
  結論: 有意差あり
```

---

## 12. 期待される結果

### 12.1 予測値

| コンテキスト | テスト成功率 | 秘密スコア | 平均応答時間 |
|--------------|--------------|------------|--------------|
| 20% | 92-98% | 0.88-0.95 | 10-15秒 |
| 40% | 88-94% | 0.82-0.90 | 13-18秒 |
| 60% | 80-88% | 0.72-0.82 | 16-22秒 |
| 80% | 68-78% | 0.58-0.70 | 20-28秒 |

### 12.2 関数順序による品質変化（80%条件での予測）

| 関数 | 順序 | 予測成功率 |
|------|------|------------|
| fizzbuzz | 1番目 | 95% |
| fizzbuzz_range | 2番目 | 90% |
| fizzbuzz_custom | 3番目 | 82% |
| fizzbuzz_stats | 4番目 | 75% |
| fizzbuzz_generator | 5番目 | 68% |

---

## 13. 制限事項・注意点

### 13.1 実験の制限

- コンテキスト消費量の正確な制御は困難（±5%の誤差を許容）
- Claude Code のバージョンアップにより結果が変わる可能性
- APIのレート制限により実行時間が変動する可能性

### 13.2 結果解釈の注意

- 相関関係は因果関係を意味しない
- 有意差なし ≠ 差がない
- 統計的有意と実用的有意は別物

### 13.3 再現性の確保

- 使用したClaude Codeバージョンを記録
- 全スクリプトをバージョン管理
- 乱数シードを固定（可能な場合）
- 環境情報（OS、Python版等）を記録

---

## 14. 参考資料

- [Claude Code公式ドキュメント - Subagents](https://code.claude.com/docs/en/sub-agents)
- [GitHub Issue #10164 - Sub-agent token usage visibility](https://github.com/anthropics/claude-code/issues/10164)
- [コンテキスト管理のベストプラクティス](https://www.anthropic.com/engineering/claude-code-best-practices)

---

## 変更履歴

| 日付 | バージョン | 変更内容 |
|------|------------|----------|
| 2025-12-26 | 1.0 | 初版作成 |
| 2025-12-28 | 1.1 | ディレクトリ構成を簡素化（fizzbuzz-repo階層を削除） |
