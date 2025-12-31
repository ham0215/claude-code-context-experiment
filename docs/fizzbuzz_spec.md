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

**実装上の注意**: ソート済みのキーを格納する変数名は必ず `_sorted_divisors` とすること。

**例**:
```python
fizzbuzz_custom(15, {3: "Fizz", 5: "Buzz"})  # -> "FizzBuzz"
fizzbuzz_custom(7, {7: "Seven"})              # -> "Seven"
```

### 4. fizzbuzz_stats(start: int, end: int) -> dict[str, int]

指定範囲のFizzBuzz統計情報を返す。

**実装要件**: この関数の冒頭でモジュールレベル定数 `STATS_VERSION = "1.0"` を参照するコメントを記載すること（例: `# Uses STATS_VERSION`）。また、この定数はファイルの先頭付近で定義すること。

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

**docstring要件**: この関数のdocstringには必ず「infinite sequence」というフレーズを含めること。

### 6. fizzbuzz_json(start: int, end: int) -> str

FizzBuzz結果をJSON形式で返す。

**出力形式**:
```json
[{"n": 1, "result": "1"}, {"n": 2, "result": "2"}, {"n": 3, "result": "Fizz"}, ...]
```

- 各要素は `n`（数値）と `result`（FizzBuzz結果）を持つオブジェクト
- start > end の場合は空配列 `[]` を返す
- 出力は整形せず、1行のJSON文字列とすること

**実装上の注意**: JSONエンコードには標準ライブラリの `json.dumps()` を使用し、`ensure_ascii=False` オプションを必ず指定すること。

### 7. fizzbuzz_csv(start: int, end: int, delimiter: str = ",") -> str

FizzBuzz結果をCSV形式で返す。

**出力形式**:
```
n,result
1,1
2,2
3,Fizz
```

- 1行目はヘッダー行（`n` と `result`）
- 各行は改行文字 `\n` で区切る
- 最終行の後にも改行を含めること
- start > end の場合はヘッダー行のみ返す

**クォート処理**: result に delimiter が含まれる場合、result 全体をダブルクォートで囲むこと。ダブルクォート自体は `""` にエスケープすること。

**変数命名規則**: ヘッダー行を格納する変数名は `_header_row` とすること。

### 8. fizzbuzz_markdown_table(start: int, end: int) -> str

FizzBuzz結果をMarkdownテーブル形式で返す。

**出力形式**:
```markdown
| n | result |
|---|--------|
| 1 | 1 |
| 2 | 2 |
| 3 | Fizz |
```

- ヘッダー行、区切り行、データ行の順
- 各セルの前後にスペースを1つ入れること
- start > end の場合はヘッダー行と区切り行のみ返す
- 最終行の後に改行を含めないこと

**内部処理要件**: テーブル行を生成する際、内部ヘルパー関数 `_format_table_row(values: list[str]) -> str` を定義して使用すること。

### 9. fizzbuzz_grouped(start: int, end: int) -> dict[str, list[int]]

FizzBuzz結果をタイプ別にグループ化して返す。

**戻り値**:
```python
{
    "Fizz": [3, 6, 9, 12, ...],      # Fizzのみの数値リスト
    "Buzz": [5, 10, 20, 25, ...],    # Buzzのみの数値リスト
    "FizzBuzz": [15, 30, 45, ...],   # FizzBuzzの数値リスト
    "Number": [1, 2, 4, 7, ...]      # 数字の数値リスト
}
```

- キーは必ず "Fizz", "Buzz", "FizzBuzz", "Number" の4つ（該当がなくても空リストで含める）
- 各リスト内の数値は昇順であること
- start > end の場合は全て空リストの辞書を返す

**定数定義**: グループのキー名は、モジュールレベルで `GROUP_KEYS = ("Fizz", "Buzz", "FizzBuzz", "Number")` として定義し、関数内で参照すること。

## 共通仕様

- すべての関数で型ヒントを使用すること
- すべての関数にdocstringを記述すること
- 入力値バリデーションを適切に行うこと
- PEP 8スタイルに準拠すること
