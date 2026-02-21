"""Tests for analyze_results.py"""

import json
from pathlib import Path

import pytest

from analyze_results import ResultsAnalyzer


class TestResultsAnalyzer:
    """Tests for ResultsAnalyzer class."""

    def test_init(self, project_root: Path):
        """Test analyzer initialization."""
        analyzer = ResultsAnalyzer(project_root / "results")

        assert analyzer.results_dir == project_root / "results"
        assert analyzer.results_file == project_root / "results" / "results.json"
        assert analyzer.results == []

    def test_load_results_success(
        self, project_root: Path, sample_results_data: list[dict]
    ):
        """Test loading results from file."""
        results_file = project_root / "results" / "results.json"
        with open(results_file, "w") as f:
            json.dump(sample_results_data, f)

        analyzer = ResultsAnalyzer(project_root / "results")
        success = analyzer.load_results()

        assert success is True
        assert len(analyzer.results) == 4

    def test_load_results_file_not_found(self, project_root: Path):
        """Test loading results when file doesn't exist."""
        analyzer = ResultsAnalyzer(project_root / "results")
        success = analyzer.load_results()

        assert success is False
        assert analyzer.results == []

    def test_group_by_level(self, project_root: Path, sample_results_data: list[dict]):
        """Test grouping results by context level."""
        results_file = project_root / "results" / "results.json"
        with open(results_file, "w") as f:
            json.dump(sample_results_data, f)

        analyzer = ResultsAnalyzer(project_root / "results")
        analyzer.load_results()
        grouped = analyzer.group_by_level()

        assert "30%" in grouped
        assert "80%" in grouped
        assert len(grouped["30%"]) == 2
        assert len(grouped["80%"]) == 2

    def test_calculate_summary(self, project_root: Path, sample_results_data: list[dict]):
        """Test summary calculation."""
        results_file = project_root / "results" / "results.json"
        with open(results_file, "w") as f:
            json.dump(sample_results_data, f)

        analyzer = ResultsAnalyzer(project_root / "results")
        analyzer.load_results()
        summary = analyzer.calculate_summary()

        # Check 30% level
        assert "30%" in summary
        assert summary["30%"]["count"] == 2
        assert summary["30%"]["test_success_rate"] == 1.0  # Both passed
        assert summary["30%"]["test_passed"] == 2
        # Secret score mean: (1.0 + 0.67) / 2 = 0.835
        assert summary["30%"]["secret_score_mean"] == pytest.approx(0.835, rel=0.01)

        # Check 80% level
        assert "80%" in summary
        assert summary["80%"]["count"] == 2
        assert summary["80%"]["test_success_rate"] == 0.0  # Both failed
        assert summary["80%"]["test_passed"] == 0

    def test_calculate_summary_function_rates(
        self, project_root: Path, sample_results_data: list[dict]
    ):
        """Test function success rates in summary."""
        results_file = project_root / "results" / "results.json"
        with open(results_file, "w") as f:
            json.dump(sample_results_data, f)

        analyzer = ResultsAnalyzer(project_root / "results")
        analyzer.load_results()
        summary = analyzer.calculate_summary()

        # Check function rates for 30%
        func_rates_30 = summary["30%"]["function_rates"]
        assert func_rates_30["fizzbuzz"] == 1.0  # Both have it
        assert func_rates_30["fizzbuzz_stats"] == 0.5  # One has it

        # Check function rates for 80%
        func_rates_80 = summary["80%"]["function_rates"]
        assert func_rates_80["fizzbuzz"] == 1.0  # Both have it
        assert func_rates_80["fizzbuzz_generator"] == 0.0  # Neither has it

    def test_chi_square_test(self, project_root: Path, sample_results_data: list[dict]):
        """Test chi-square test calculation."""
        results_file = project_root / "results" / "results.json"
        with open(results_file, "w") as f:
            json.dump(sample_results_data, f)

        analyzer = ResultsAnalyzer(project_root / "results")
        analyzer.load_results()
        result = analyzer.chi_square_test("30%", "80%")

        assert result is not None
        assert "chi_square" in result
        assert "df" in result
        assert result["df"] == 1
        assert "significance" in result
        assert "level1" in result
        assert "level2" in result
        assert result["level1"]["rate"] == 1.0  # 30% success rate
        assert result["level2"]["rate"] == 0.0  # 80% success rate

    def test_chi_square_test_level_not_found(
        self, project_root: Path, sample_results_data: list[dict]
    ):
        """Test chi-square test when level doesn't exist."""
        results_file = project_root / "results" / "results.json"
        with open(results_file, "w") as f:
            json.dump(sample_results_data, f)

        analyzer = ResultsAnalyzer(project_root / "results")
        analyzer.load_results()
        result = analyzer.chi_square_test("30%", "99%")

        assert result is None

    def test_chi_square_test_significance(self, project_root: Path):
        """Test chi-square significance classification."""
        # Create data with significant difference
        data = [
            {"trial_id": f"30%_{i}", "context_level": "30%", "test_passed": True,
             "secret_score": 1.0, "elapsed_seconds": 50.0, "func_results": {}}
            for i in range(10)
        ] + [
            {"trial_id": f"80%_{i}", "context_level": "80%", "test_passed": False,
             "secret_score": 0.0, "elapsed_seconds": 80.0, "func_results": {}}
            for i in range(10)
        ]

        results_file = project_root / "results" / "results.json"
        with open(results_file, "w") as f:
            json.dump(data, f)

        analyzer = ResultsAnalyzer(project_root / "results")
        analyzer.load_results()
        result = analyzer.chi_square_test("30%", "80%")

        # With 10 pass vs 10 fail, chi-square should be significant
        assert result["significance"] == "significant"

    def test_generate_report(self, project_root: Path, sample_results_data: list[dict]):
        """Test report generation."""
        results_file = project_root / "results" / "results.json"
        with open(results_file, "w") as f:
            json.dump(sample_results_data, f)

        analyzer = ResultsAnalyzer(project_root / "results")
        analyzer.load_results()
        report = analyzer.generate_report()

        assert "コンテキスト消費影響実験" in report
        assert "条件別サマリー" in report
        assert "30%" in report
        assert "80%" in report
        assert "関数別成功率" in report
        assert "統計的検定" in report

    def test_generate_report_empty_results(self, project_root: Path):
        """Test report generation with empty results."""
        results_file = project_root / "results" / "results.json"
        with open(results_file, "w") as f:
            json.dump([], f)

        analyzer = ResultsAnalyzer(project_root / "results")
        analyzer.load_results()
        report = analyzer.generate_report()

        # Should still generate without errors
        assert "コンテキスト消費影響実験" in report


class TestSummaryEdgeCases:
    """Test edge cases in summary calculation."""

    def test_single_trial(self, project_root: Path):
        """Test summary with single trial."""
        data = [{
            "trial_id": "30%_001",
            "context_level": "30%",
            "test_passed": True,
            "secret_score": 0.5,
            "elapsed_seconds": 30.0,
            "func_results": {"fizzbuzz": True, "fizzbuzz_range": False,
                            "fizzbuzz_custom": False, "fizzbuzz_stats": False,
                            "fizzbuzz_generator": False},
        }]

        results_file = project_root / "results" / "results.json"
        with open(results_file, "w") as f:
            json.dump(data, f)

        analyzer = ResultsAnalyzer(project_root / "results")
        analyzer.load_results()
        summary = analyzer.calculate_summary()

        assert summary["30%"]["count"] == 1
        assert summary["30%"]["secret_score_std"] == 0  # std of single value

    def test_zero_expected_values_chi_square(self, project_root: Path):
        """Test chi-square with all passing or all failing."""
        data = [
            {"trial_id": f"30%_{i}", "context_level": "30%", "test_passed": True,
             "secret_score": 1.0, "elapsed_seconds": 50.0, "func_results": {}}
            for i in range(5)
        ] + [
            {"trial_id": f"80%_{i}", "context_level": "80%", "test_passed": True,
             "secret_score": 1.0, "elapsed_seconds": 80.0, "func_results": {}}
            for i in range(5)
        ]

        results_file = project_root / "results" / "results.json"
        with open(results_file, "w") as f:
            json.dump(data, f)

        analyzer = ResultsAnalyzer(project_root / "results")
        analyzer.load_results()
        result = analyzer.chi_square_test("30%", "80%")

        # Should return None when all pass (no failures to compare)
        assert result is None
