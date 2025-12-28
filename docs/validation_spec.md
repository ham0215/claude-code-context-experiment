# 検証仕様書

## 秘密メッセージ検証

### 検証対象

| 項目 | 指示内容 | 埋め込み場所 |
|------|----------|--------------|
| ヘッダーID | `EXPERIMENT-ID: MAGIC-7392` | ファイル先頭コメント |
| フッター検証 | `Verified: BLUE-ELEPHANT` | ファイル末尾コメント |
| 関数タグ | `ref: XYZ-999` | 各関数のdocstring内 |

### 検証コード

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

### 秘密スコア計算

```
secret_score = (has_header + has_footer + min(ref_count/expected_refs, 1.0)) / 3
```

| スコア | 解釈 |
|--------|------|
| 1.0 | 完全記憶（全指示を遵守） |
| 0.67-0.99 | 部分的ドリフト |
| 0.34-0.66 | 重度のドリフト |
| 0-0.33 | ほぼ完全忘却 |

## 測定項目

### 主要指標

| 指標 | 測定方法 | 単位 |
|------|----------|------|
| テスト成功率 | pytest の exit code | bool |
| 秘密スコア | ファイル内検索 | 0.0-1.0 |
| 応答時間 | タスク開始から完了まで | 秒 |

### 補助指標

| 指標 | 測定方法 | 単位 |
|------|----------|------|
| 開始時コンテキスト | /context コマンド | % |
| 終了時コンテキスト | /context コマンド | % |
| テスト通過数 | pytest 詳細出力 | 個 |
| 関数別成功 | テスト結果パース | bool×5 |

## 結果データ構造

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
