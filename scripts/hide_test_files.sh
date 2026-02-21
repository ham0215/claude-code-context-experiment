#!/bin/bash
# hide_test_files.sh
# 実験開始前にテスト/検証ファイルをワーキングツリーから削除し、
# ワーカーがカンニングできないようにする。
# 復元: git checkout HEAD -- tests/ scripts/verify_trials.py scripts/validate_local.py scripts/analyze_results.py

set -euo pipefail

FILES=(
  tests/test_fizzbuzz.py
  tests/test_validate_local.py
  tests/test_analyze_results.py
  tests/conftest.py
  scripts/verify_trials.py
  scripts/validate_local.py
  scripts/analyze_results.py
)

echo "=== Hiding test/verification files from working tree ==="

for f in "${FILES[@]}"; do
  if [ -f "$f" ]; then
    rm "$f"
    echo "  Removed: $f"
  else
    echo "  Already absent: $f"
  fi
done

echo "=== Done. Files removed from working tree. ==="
echo "To restore: git checkout HEAD -- tests/ scripts/verify_trials.py scripts/validate_local.py scripts/analyze_results.py"
