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
