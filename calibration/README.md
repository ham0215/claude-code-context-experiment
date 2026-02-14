# Context Calibration Table

チャンク数と実際のコンテキストウィンドウ占有率のマッピングテーブル。
メインCLIウィンドウで `/context` コマンドにより実測。

## Results

| Level | Chunks | Nominal % | Measured % | Used Tokens | Total Tokens | Delta | Date |
|-------|--------|-----------|------------|-------------|--------------|-------|------|
| baseline | 0 | 0% | 14% | 27k | 200k | +14% | 2026-02-14 |
| 30% | 19 | 30% | 31% | 61k | 200k | +1% | 2026-02-14 |
| 50% | 41 | 50% | 50% | 100k | 200k | 0% | 2026-02-14 |
| 80% | 75 | 80% | 80% | 161k | 200k | 0% | 2026-02-14 |

Delta = Measured % - Nominal %（名目値との差分）

## Notes

- Measured in main CLI window (claude-opus-4-6, 200k context)
- Agent workers have similar but not identical overhead (different system tools, no skills)
- Autocompact buffer size varies; measurements are approximate
- Each level measured in a fresh session after `/clear`
- 90% level was removed from the experiment because autocompact triggers before 86 chunks can be retained in a single session
