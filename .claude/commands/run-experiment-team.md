---
description: チームベースでコンテキスト消費実験を実行（共有タスクリスト・進捗監視付き）
allowed-tools: TeamCreate, TeamDelete, TaskCreate, TaskList, TaskGet, TaskUpdate, Task, SendMessage, Bash, Read, Write, Edit
---

# チームベース実験実行

TeamCreate/TaskCreate/SendMessage を使用して、タスクを事前割り当てしたワーカーが並列にトライアルを実行します。

## 既存方式との比較

| 機能 | `/run-experiment-parallel`（既存） | `/run-experiment-team`（本コマンド） |
|------|-----------------------------------|--------------------------------------|
| エージェント管理 | Task で個別起動 | TeamCreate でチーム化 |
| タスク管理 | プロンプトで指示 | タスク事前割り当て（競合なし） |
| 進捗監視 | 各エージェントの完了待ち | TaskList でリアルタイム確認 |
| 障害対応 | エージェント単位で再起動 | 未完了タスクを別ワーカーが自動引き継ぎ |
| クリーンアップ | なし | TeamDelete で一括削除 |

## コンテキスト注入方式

ルートの `CLAUDE.md` をレベルごとのバリアントに切り替えることで、ワーカー起動時に自動的にコンテキストが消費されます。
ワーカー側でのチャンク読み込みは不要です。

| レベル | CLAUDE.md バリアント | 目標消費率 | チーム名 |
|--------|---------------------|-----------|----------|
| 30%    | `claude_md_variants/CLAUDE.md.30pct` | ~30% | `exp-30pct` |
| 50%    | `claude_md_variants/CLAUDE.md.50pct` | ~50% | `exp-50pct` |
| 80%    | `claude_md_variants/CLAUDE.md.80pct` | ~80% | `exp-80pct` |

## 使い方

ユーザーから以下のパラメータを確認してください：

1. **コンテキストレベル**: `30%`, `50%`, `80%` のいずれか
2. **試行範囲**: 開始番号と終了番号（例: 1-5）
3. **ワーカー数**: 同時起動するワーカー数（推奨: 試行数と同数。**1トライアル1ワーカーが必須**）

## 実行手順

### Step 0: CLAUDE.md 切り替え確認

ルートの `CLAUDE.md` が対象レベルのバリアントに切り替え済みであることを確認します。

```bash
head -20 CLAUDE.md
```

出力に `## Context Noise ({level}% Level)` が含まれていることを確認してください。
含まれていない場合、バリアントをコピーしてから続行：

```bash
cp claude_md_variants/CLAUDE.md.{level}pct CLAUDE.md
```

### Step 0.5: /context でコンテキスト消費量を確認

CLAUDE.md の切り替え後、`/context` コマンドを実行して現在のコンテキスト消費量を確認・記録します。

**出力例:**
```
Context: XX.X% used (XXXK / XXXK tokens)
```

**記録する値:**
- `measured_context_percent`: 測定されたコンテキスト消費率（例: 32.5）

**検証ルール — 不一致時は即座に中断:**

| 目標レベル | 許容範囲 |
|-----------|---------|
| 30%       | 15% ≤ measured ≤ 45% |
| 50%       | 30% ≤ measured ≤ 65% |
| 80%       | 65% ≤ measured ≤ 95% |

測定値が許容範囲外の場合、**実験を中断**してユーザーに報告してください：

```
ERROR: Context consumption mismatch.
  Target level: {level}%
  Measured: {measured}%
  Expected range: {min}% - {max}%
Please verify CLAUDE.md variant and retry.
```

### Step 1: チーム作成

レベルに応じたチーム名でチームを作成：

```
TeamCreate(team_name="exp-{level}pct", description="Context experiment at {level}% level")
```

例: `TeamCreate(team_name="exp-30pct", description="Context experiment at 30% level")`

### Step 1.5: 過去データの処理

既存の `results/` や `workspaces/` にファイルが存在する場合、AskUserQuestion でユーザーに処理方法を確認します。
既存データがない場合はこのステップをスキップしてください。

#### 確認方法

```
AskUserQuestion:
  question: "過去の実験データが存在します。どのように処理しますか？"
  header: "Past data"
  options:
    - label: "バックアップ"
      description: "results/_backup_YYYYMMDD_HHMMSS/ に退避してから実行"
    - label: "削除"
      description: "過去データを削除してクリーンな状態で実行"
    - label: "スキップ"
      description: "過去データをそのまま残して実行（結果が混在する可能性あり）"
```

#### 「バックアップ」選択時

バックアップ先は `results/` および `workspaces/` 配下にすることで、`.gitignore` により自動的にgit管理外となります。

```bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# results/ 内の既存ファイルをバックアップ（_backup_ ディレクトリ自体は除外）
mkdir -p "results/_backup_${TIMESTAMP}"
find results -maxdepth 1 -type f -exec mv {} "results/_backup_${TIMESTAMP}/" \;
echo "Backed up results files -> results/_backup_${TIMESTAMP}/"

# workspaces/ 内の既存ディレクトリをバックアップ
if [ -d workspaces ] && [ "$(ls -A workspaces 2>/dev/null)" ]; then
  mkdir -p "workspaces/_backup_${TIMESTAMP}"
  find workspaces -maxdepth 1 -mindepth 1 -not -name '_backup_*' -exec mv {} "workspaces/_backup_${TIMESTAMP}/" \;
  echo "Backed up workspaces -> workspaces/_backup_${TIMESTAMP}/"
fi
```

#### 「削除」選択時

```bash
# results/ 内の既存ファイルを削除（_backup_ ディレクトリは保持）
find results -maxdepth 1 -type f -delete
echo "Deleted result files"

# workspaces/ 内の既存ディレクトリを削除（_backup_ ディレクトリは保持）
if [ -d workspaces ]; then
  find workspaces -maxdepth 1 -mindepth 1 -not -name '_backup_*' -exec rm -rf {} \;
  echo "Deleted workspace directories"
fi
```

#### 「スキップ」選択時

何もしない。`mkdir -p results workspaces` のみ実行。

#### 共通（全選択肢の後に実行）

```bash
mkdir -p results workspaces
```

### Step 2: タスク登録 & 事前割り当て

各トライアルを TaskCreate でタスク登録し、**直後に TaskUpdate で対応するワーカーに割り当て**ます。
これにより、ワーカー間のタスク競合（レースコンディション）を完全に排除します。

#### 2a: タスク作成

```
TaskCreate:
  subject: "Trial {level}_{number:03d}"
  description: |
    Execute experiment trial.
    - context_level: {level}
    - trial_number: {number}
    - measured_context_percent: {measured_context_percent}
    - workspace: workspaces/trial_{level}_{number:03d}/
    - result_file: results/trial_{level}_{number:03d}.json
    - project_root: /Users/naoto.hamada/github/ham/claude-code-context-experiment
  activeForm: "Executing trial {level}_{number:03d}"
```

#### 2b: ワーカーへの事前割り当て

タスク作成後、各タスクを対応するワーカーに割り当てます。
TaskCreate の戻り値からタスクIDを取得し、`TaskUpdate` で `owner` を設定：

```
TaskUpdate(taskId="<task-1-id>", owner="worker-1")
TaskUpdate(taskId="<task-2-id>", owner="worker-2")
TaskUpdate(taskId="<task-3-id>", owner="worker-3")
// ... 試行数分
```

**タスクとワーカーの対応**: Trial N → worker-N（1対1対応）

**例: 30% レベルで試行 1-3、measured_context_percent=32.5 の場合**

```
// Step 2a: タスク作成（並列実行可）
TaskCreate(subject="Trial 30%_001", description="Execute experiment trial.\n- context_level: 30%\n- trial_number: 1\n- measured_context_percent: 32.5\n- workspace: workspaces/trial_30%_001/\n- result_file: results/trial_30%_001.json\n- project_root: /Users/naoto.hamada/github/ham/claude-code-context-experiment", activeForm="Executing trial 30%_001")

TaskCreate(subject="Trial 30%_002", description="Execute experiment trial.\n- context_level: 30%\n- trial_number: 2\n- measured_context_percent: 32.5\n- workspace: workspaces/trial_30%_002/\n- result_file: results/trial_30%_002.json\n- project_root: /Users/naoto.hamada/github/ham/claude-code-context-experiment", activeForm="Executing trial 30%_002")

TaskCreate(subject="Trial 30%_003", description="Execute experiment trial.\n- context_level: 30%\n- trial_number: 3\n- measured_context_percent: 32.5\n- workspace: workspaces/trial_30%_003/\n- result_file: results/trial_30%_003.json\n- project_root: /Users/naoto.hamada/github/ham/claude-code-context-experiment", activeForm="Executing trial 30%_003")

// Step 2b: 事前割り当て（タスクID取得後に実行）
TaskUpdate(taskId="<task-1-id>", owner="worker-1")
TaskUpdate(taskId="<task-2-id>", owner="worker-2")
TaskUpdate(taskId="<task-3-id>", owner="worker-3")
```

### Step 2c: ワークスペース事前作成

ワーカー起動前に、全トライアルのワークスペースディレクトリをチームリーダー側で事前作成します。
これにより、ワーカー側での `mkdir` 権限プロンプトを回避します。

```bash
mkdir -p workspaces/trial_{level}_{001}/src workspaces/trial_{level}_{002}/src workspaces/trial_{level}_{003}/src
# ... 試行数分のディレクトリを1コマンドで作成
```

**例: 30% レベルで試行 1-3 の場合**

```bash
mkdir -p workspaces/trial_30%_001/src workspaces/trial_30%_002/src workspaces/trial_30%_003/src
```

### Step 3: ワーカー起動

**MUST: 1トライアル1ワーカー**。試行数と同数のワーカーを **1つのメッセージで同時に** 起動。
各ワーカーのプロンプトに **割り当て済みタスク名** を明示し、競合を防止：

```
Task(
  subagent_type="experiment-team-worker",
  team_name="exp-{level}pct",
  name="worker-1",
  mode="bypassPermissions",
  prompt="You are worker-1 in team exp-{level}pct. Your assigned task is 'Trial {level}_{001}'. Find it in TaskList by subject, set status to in_progress, and execute the trial. Do NOT claim any other task. Project root: /Users/naoto.hamada/github/ham/claude-code-context-experiment",
  description="Experiment worker 1"
)

Task(
  subagent_type="experiment-team-worker",
  team_name="exp-{level}pct",
  name="worker-2",
  mode="bypassPermissions",
  prompt="You are worker-2 in team exp-{level}pct. Your assigned task is 'Trial {level}_{002}'. Find it in TaskList by subject, set status to in_progress, and execute the trial. Do NOT claim any other task. Project root: /Users/naoto.hamada/github/ham/claude-code-context-experiment",
  description="Experiment worker 2"
)

// ... 試行数分のワーカー
```

**重要**:
- 全ワーカーを1つのメッセージ内で並列起動すること
- 各ワーカーのプロンプトに固有のタスク名（`Trial {level}_{number}`）を含めること
- ワーカーは自分に割り当てられたタスクのみを実行する

### Step 4: 進捗監視

`TaskList` を定期的に実行して進捗を確認：

- `pending`: 未着手
- `in_progress`: 実行中
- `completed`: 完了

全タスクが `completed` になるまで監視。

### Step 5: クリーンアップ

全タスク完了後：

1. 各ワーカーに `SendMessage(type="shutdown_request")` を送信
2. ワーカーの終了を確認
3. `TeamDelete` でチームとタスクリストを削除

```
SendMessage(type="shutdown_request", recipient="worker-1", content="All tasks complete")
SendMessage(type="shutdown_request", recipient="worker-2", content="All tasks complete")
// ...
TeamDelete()
```

### Step 6: 結果集計

```bash
python scripts/analyze_results.py
```

## 注意事項

- **CLAUDE.md 切り替え必須**: 実験前にルートの `CLAUDE.md` が対象レベルのバリアントであることを確認。コンテキストはワーカー起動時に自動注入される
- **コンテキスト検証必須**: `/context` で消費量を確認し、許容範囲外なら中断
- **1トライアル1ワーカー（MUST）**: コンテキスト分離を保証するため、各ワーカーは1試行のみ実行して停止
- **相対パスで実行（MUST）**: Bash コマンドは必ずプロジェクトルートからの **相対パス** で実行すること。`/usr/bin/ls` や `/Users/.../project/file` のような絶対パスは権限プロンプトが発生するため使用禁止。例: `ls workspaces/` ○、`/bin/ls /Users/.../workspaces/` ×
- 結果 JSON は既存フォーマットと完全互換（`scripts/analyze_results.py` で集計可能）
- ワークスペースは `workspaces/trial_{level}_{number:03d}/` に分離
- チーム命名規則: `exp-30pct`, `exp-50pct`, `exp-80pct`
- API レート制限に注意してワーカー数を調整
