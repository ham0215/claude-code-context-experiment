# コンテキスト消費がClaude Codeの挙動に与える影響の検証実験

## 実験概要

### 目的

Claude Codeにおけるコンテキストウィンドウの消費量が、以下の指標に与える影響を定量的に検証する。

- 実装タスクの成功率
- 初期指示の記憶保持率（コンテキストドリフト）
- 応答時間

### 仮説

| 仮説 | 内容 |
|------|------|
| H1 | コンテキスト消費量が増加すると、テスト成功率が低下する |
| H2 | コンテキスト消費量が増加すると、初期指示の記憶率が低下する |
| H3 | コンテキスト消費量が増加すると、応答時間が増加する |
| H4 | 複数関数の実装において、後半の関数ほど品質が低下する |

---

## ディレクトリ構成

```
claude-code-context-experiment/
├── .claude/
│   └── settings.json                 # Claude Code設定（tests/を読み取り禁止）
├── src/
│   └── fizzbuzz.py                   # 実装対象（毎回削除）
├── docs/
│   ├── fizzbuzz_spec.md              # 設計書（Claudeが参照）
│   ├── experiment_config.json        # 実験設定
│   └── validation_spec.md            # 検証仕様
├── tests/
│   └── test_fizzbuzz.py              # テストコード（Claudeは読めない）
├── scripts/                          # 実験スクリプト
├── noise_chunks/                     # コンテキスト消費用ノイズファイル
├── prompts/                          # プロンプトテンプレート
└── results/                          # 結果保存（.gitignoreで除外）
```

---

## 実験手順

### 事前準備

1. リポジトリのセットアップ
2. `.claude/settings.json` でテストコードへのアクセスを禁止
3. キャリブレーション実行（ノイズ量の調整）
4. ノイズチャンクファイルの生成

### 各試行の流れ

1. Claudeコンテキストクリア (/clear)
2. コンテキストを目標レベルに調整（ノイズ投入）
3. 開始時コンテキスト記録
4. 実装依頼プロンプト実行
5. 終了時コンテキスト記録
6. pytest実行
7. 秘密メッセージ検証
8. 結果をJSONに保存
9. 実装ファイル削除（クリーンアップ）
10. 次の試行へ

### 実行コマンド

```bash
# キャリブレーション
python scripts/calibration.py

# 実験実行
python scripts/experiment_runner.py

# 結果分析
python scripts/analyze_results.py
```

---

## 実験条件

詳細は `docs/experiment_config.json` を参照。

| 条件名 | 目標範囲 | 試行数 |
|--------|----------|--------|
| 30% | 25-35% | 100回 |
| 50% | 45-55% | 100回 |
| 80% | 75-85% | 100回 |

**合計: 300試行**

---

## 統計分析

### 検定手法

| 分析内容 | 検定手法 | 有意水準 |
|----------|----------|----------|
| 条件間の成功率比較 | カイ二乗検定 | α = 0.05 |
| 秘密スコアの比較 | t検定 / Mann-Whitney U | α = 0.05 |
| コンテキストと成功率の傾向 | 線形回帰 | α = 0.05 |

### 効果量

- オッズ比（成功率の比較）
- Cohen's d（連続変数の比較）
- R²（傾向の説明力）

---

## 期待される結果

| コンテキスト | テスト成功率 | 秘密スコア | 平均応答時間 |
|--------------|--------------|------------|--------------|
| 30% | 90-96% | 0.86-0.93 | 12-17秒 |
| 50% | 84-92% | 0.78-0.86 | 15-20秒 |
| 80% | 68-78% | 0.58-0.70 | 20-28秒 |

---

## 制限事項

- コンテキスト消費量の正確な制御は困難（±5%の誤差を許容）
- Claude Code のバージョンアップにより結果が変わる可能性
- APIのレート制限により実行時間が変動する可能性

---

## 関連ドキュメント

| ファイル | 用途 |
|----------|------|
| [docs/fizzbuzz_spec.md](docs/fizzbuzz_spec.md) | 実装仕様（Claude用） |
| [docs/experiment_config.json](docs/experiment_config.json) | 実験設定 |
| [docs/validation_spec.md](docs/validation_spec.md) | 検証仕様 |
| [prompts/implementation_prompt.txt](prompts/implementation_prompt.txt) | 実装依頼プロンプト |

---

## 参考資料

- [Claude Code公式ドキュメント - Subagents](https://code.claude.com/docs/en/sub-agents)
- [GitHub Issue #10164 - Sub-agent token usage visibility](https://github.com/anthropics/claude-code/issues/10164)
- [コンテキスト管理のベストプラクティス](https://www.anthropic.com/engineering/claude-code-best-practices)

---

## 変更履歴

| 日付 | バージョン | 変更内容 |
|------|------------|----------|
| 2025-12-26 | 1.0 | 初版作成 |
