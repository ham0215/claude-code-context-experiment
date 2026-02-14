"""Analyze experiment results and generate reports."""

import json
from pathlib import Path
from typing import Optional
from collections import defaultdict
import math


class ResultsAnalyzer:
    """Analyzes experiment results."""

    def __init__(self, results_dir: Path):
        self.results_dir = results_dir
        self.results_file = results_dir / "results.json"
        self.results: list[dict] = []

    def load_results(self) -> bool:
        """Load results from file."""
        if not self.results_file.exists():
            print(f"Results file not found: {self.results_file}")
            return False

        with open(self.results_file, 'r') as f:
            self.results = json.load(f)

        print(f"Loaded {len(self.results)} trial results")
        return True

    def group_by_level(self) -> dict[str, list[dict]]:
        """Group results by context level."""
        grouped = defaultdict(list)
        for result in self.results:
            grouped[result["context_level"]].append(result)
        return dict(grouped)

    def calculate_summary(self) -> dict:
        """Calculate summary statistics for each context level."""
        grouped = self.group_by_level()
        summary = {}

        for level, trials in grouped.items():
            n = len(trials)
            if n == 0:
                continue

            # Test success rate
            test_passed = sum(1 for t in trials if t["test_passed"])
            test_rate = test_passed / n

            # Secret score statistics
            secret_scores = [t["secret_score"] for t in trials]
            secret_mean = sum(secret_scores) / n
            secret_std = math.sqrt(
                sum((s - secret_mean) ** 2 for s in secret_scores) / n
            ) if n > 1 else 0

            # Response time statistics
            times = [t.get("elapsed_seconds") or 0 for t in trials]
            time_mean = sum(times) / n

            # Context consumption statistics
            target_percents = [t.get("target_context_percent") or 0 for t in trials]
            target_mean = sum(target_percents) / n if target_percents else 0

            # Function-level success rates
            func_rates = {}
            func_names = ["fizzbuzz", "fizzbuzz_range", "fizzbuzz_custom",
                         "fizzbuzz_stats", "fizzbuzz_generator"]

            for func in func_names:
                func_passed = sum(
                    1 for t in trials
                    if t.get("func_results", {}).get(func, False)
                )
                func_rates[func] = func_passed / n

            # Hidden instruction success rates
            hidden_rates = {
                "sorted_divisors": sum(1 for t in trials if t.get("hidden_sorted_divisors", False)) / n,
                "stats_version": sum(1 for t in trials if t.get("hidden_stats_version", False)) / n,
                "stats_comment": sum(1 for t in trials if t.get("hidden_stats_comment", False)) / n,
                "infinite_seq": sum(1 for t in trials if t.get("hidden_infinite_seq", False)) / n,
                "ensure_ascii": sum(1 for t in trials if t.get("hidden_ensure_ascii", False)) / n,
                "header_row": sum(1 for t in trials if t.get("hidden_header_row", False)) / n,
                "format_table_row": sum(1 for t in trials if t.get("hidden_format_table_row", False)) / n,
                "group_keys": sum(1 for t in trials if t.get("hidden_group_keys", False)) / n,
            }

            # Hidden score statistics
            hidden_scores = [t.get("hidden_score", 0) for t in trials]
            hidden_mean = sum(hidden_scores) / n

            summary[level] = {
                "count": n,
                "target_context_percent": round(target_mean, 1),
                "test_success_rate": round(test_rate, 4),
                "test_passed": test_passed,
                "secret_score_mean": round(secret_mean, 4),
                "secret_score_std": round(secret_std, 4),
                "hidden_score_mean": round(hidden_mean, 4),
                "hidden_rates": hidden_rates,
                "response_time_mean": round(time_mean, 2),
                "function_rates": func_rates
            }

        return summary

    def chi_square_test(self, level1: str, level2: str) -> Optional[dict]:
        """
        Perform chi-square test comparing success rates between two levels.

        Returns chi-square statistic and approximate p-value.
        """
        grouped = self.group_by_level()

        if level1 not in grouped or level2 not in grouped:
            return None

        trials1 = grouped[level1]
        trials2 = grouped[level2]

        # 2x2 contingency table
        n1 = len(trials1)
        n2 = len(trials2)
        pass1 = sum(1 for t in trials1 if t["test_passed"])
        pass2 = sum(1 for t in trials2 if t["test_passed"])
        fail1 = n1 - pass1
        fail2 = n2 - pass2

        total = n1 + n2
        total_pass = pass1 + pass2
        total_fail = fail1 + fail2

        if total == 0 or total_pass == 0 or total_fail == 0:
            return None

        # Expected frequencies
        e_pass1 = n1 * total_pass / total
        e_pass2 = n2 * total_pass / total
        e_fail1 = n1 * total_fail / total
        e_fail2 = n2 * total_fail / total

        # Chi-square statistic
        chi2 = 0
        for obs, exp in [(pass1, e_pass1), (pass2, e_pass2),
                         (fail1, e_fail1), (fail2, e_fail2)]:
            if exp > 0:
                chi2 += (obs - exp) ** 2 / exp

        # Approximate p-value (1 df)
        # Using simple approximation for p < 0.05 threshold
        significance = "significant" if chi2 > 3.841 else "not significant"

        return {
            "chi_square": round(chi2, 4),
            "df": 1,
            "significance": significance,
            "level1": {"total": n1, "passed": pass1, "rate": round(pass1/n1, 4)},
            "level2": {"total": n2, "passed": pass2, "rate": round(pass2/n2, 4)}
        }

    def generate_report(self) -> str:
        """Generate a text report of the analysis."""
        summary = self.calculate_summary()

        lines = [
            "=" * 70,
            "コンテキスト消費影響実験 - 結果レポート",
            "=" * 70,
            "",
            "【条件別サマリー】",
            ""
        ]

        # Table header
        lines.append(f"{'Level':<8} {'N':>4} {'Target':>8} {'Pass Rate':>10} {'Secret':>8} {'Hidden':>8} {'Time':>8}")
        lines.append("-" * 70)

        for level in sorted(summary.keys()):
            s = summary[level]
            hidden_mean = s.get('hidden_score_mean', 0)
            lines.append(
                f"{level:<8} {s['count']:>4} "
                f"{s['target_context_percent']:>7.1f}% "
                f"{s['test_success_rate']:>9.1%} {s['secret_score_mean']:>8.2f} "
                f"{hidden_mean:>8.2f} {s['response_time_mean']:>7.1f}s"
            )

        lines.extend(["", "【関数別成功率】", ""])

        for level in sorted(summary.keys()):
            lines.append(f"{level}:")
            for func, rate in summary[level]["function_rates"].items():
                bar = "█" * int(rate * 20) + "░" * (20 - int(rate * 20))
                lines.append(f"  {func:<20} {bar} {rate:.1%}")
            lines.append("")

        # Hidden instruction rates
        lines.extend(["【隠し指示の遵守率】", ""])
        lines.append("仕様書中間部分に埋め込まれた指示への対応:")
        lines.append("")

        hidden_labels = {
            "sorted_divisors": "_sorted_divisors変数名",
            "stats_version": "STATS_VERSION定数",
            "stats_comment": "Uses STATS_VERSIONコメント",
            "infinite_seq": "infinite sequenceフレーズ",
            "ensure_ascii": "ensure_ascii=False",
            "header_row": "_header_row変数名",
            "format_table_row": "_format_table_row関数",
            "group_keys": "GROUP_KEYS定数",
        }

        for level in sorted(summary.keys()):
            lines.append(f"{level}:")
            hidden_rates = summary[level].get("hidden_rates", {})
            for key, label in hidden_labels.items():
                rate = hidden_rates.get(key, 0)
                bar = "█" * int(rate * 20) + "░" * (20 - int(rate * 20))
                lines.append(f"  {label:<28} {bar} {rate:.1%}")
            lines.append("")

        # Chi-square tests
        lines.extend(["【統計的検定】", ""])

        test_30_80 = self.chi_square_test("30%", "80%")
        if test_30_80:
            lines.append("30% vs 80% 比較:")
            lines.append(f"  χ² = {test_30_80['chi_square']:.4f}")
            lines.append(f"  結果: {test_30_80['significance']} (α = 0.05)")
            lines.append(f"  30% 成功率: {test_30_80['level1']['rate']:.1%}")
            lines.append(f"  80% 成功率: {test_30_80['level2']['rate']:.1%}")

        lines.append("")
        lines.append("=" * 70)

        return "\n".join(lines)


def main():
    """Run analysis."""
    project_root = Path(__file__).parent.parent
    results_dir = project_root / "results"

    analyzer = ResultsAnalyzer(results_dir)

    if not analyzer.load_results():
        print("No results to analyze.")
        print("Run the experiment first with: python scripts/experiment_runner.py")
        return

    report = analyzer.generate_report()
    print(report)

    # Save report
    report_file = results_dir / "analysis_report.txt"
    with open(report_file, 'w') as f:
        f.write(report)
    print(f"\nReport saved to {report_file}")


if __name__ == "__main__":
    main()
