"""Test suite for FizzBuzz extended implementation."""

import pytest
from typing import Generator
import sys
sys.path.insert(0, str(__file__).replace('/tests/test_fizzbuzz.py', '/src'))

from fizzbuzz import (
    fizzbuzz,
    fizzbuzz_range,
    fizzbuzz_custom,
    fizzbuzz_stats,
    fizzbuzz_generator,
    fizzbuzz_json,
    fizzbuzz_csv,
    fizzbuzz_markdown_table,
    fizzbuzz_grouped,
)


class TestFizzbuzz:
    """Tests for the basic fizzbuzz function."""

    def test_fizz_for_3(self):
        assert fizzbuzz(3) == "Fizz"

    def test_fizz_for_6(self):
        assert fizzbuzz(6) == "Fizz"

    def test_fizz_for_9(self):
        assert fizzbuzz(9) == "Fizz"

    def test_buzz_for_5(self):
        assert fizzbuzz(5) == "Buzz"

    def test_buzz_for_10(self):
        assert fizzbuzz(10) == "Buzz"

    def test_buzz_for_20(self):
        assert fizzbuzz(20) == "Buzz"

    def test_fizzbuzz_for_15(self):
        assert fizzbuzz(15) == "FizzBuzz"

    def test_fizzbuzz_for_30(self):
        assert fizzbuzz(30) == "FizzBuzz"

    def test_fizzbuzz_for_45(self):
        assert fizzbuzz(45) == "FizzBuzz"

    def test_number_for_1(self):
        assert fizzbuzz(1) == "1"

    def test_number_for_2(self):
        assert fizzbuzz(2) == "2"

    def test_number_for_7(self):
        assert fizzbuzz(7) == "7"

    def test_number_for_11(self):
        assert fizzbuzz(11) == "11"

    def test_raises_for_zero(self):
        with pytest.raises(ValueError):
            fizzbuzz(0)

    def test_raises_for_negative(self):
        with pytest.raises(ValueError):
            fizzbuzz(-1)

    def test_raises_for_large_negative(self):
        with pytest.raises(ValueError):
            fizzbuzz(-100)


class TestFizzbuzzRange:
    """Tests for the fizzbuzz_range function."""

    def test_range_1_to_5(self):
        result = fizzbuzz_range(1, 5)
        assert result == ["1", "2", "Fizz", "4", "Buzz"]

    def test_range_1_to_15(self):
        result = fizzbuzz_range(1, 15)
        assert len(result) == 15
        assert result[0] == "1"
        assert result[2] == "Fizz"
        assert result[4] == "Buzz"
        assert result[14] == "FizzBuzz"

    def test_range_10_to_16(self):
        result = fizzbuzz_range(10, 16)
        assert result == ["Buzz", "11", "Fizz", "13", "14", "FizzBuzz", "16"]

    def test_empty_range_when_start_greater_than_end(self):
        result = fizzbuzz_range(10, 5)
        assert result == []

    def test_single_element_range(self):
        result = fizzbuzz_range(15, 15)
        assert result == ["FizzBuzz"]

    def test_range_with_same_start_end(self):
        result = fizzbuzz_range(7, 7)
        assert result == ["7"]


class TestFizzbuzzCustom:
    """Tests for the fizzbuzz_custom function."""

    def test_custom_standard_rules(self):
        rules = {3: "Fizz", 5: "Buzz"}
        assert fizzbuzz_custom(15, rules) == "FizzBuzz"

    def test_custom_fizz_only(self):
        rules = {3: "Fizz", 5: "Buzz"}
        assert fizzbuzz_custom(9, rules) == "Fizz"

    def test_custom_buzz_only(self):
        rules = {3: "Fizz", 5: "Buzz"}
        assert fizzbuzz_custom(10, rules) == "Buzz"

    def test_custom_no_match(self):
        rules = {3: "Fizz", 5: "Buzz"}
        assert fizzbuzz_custom(7, rules) == "7"

    def test_custom_single_rule(self):
        rules = {7: "Seven"}
        assert fizzbuzz_custom(7, rules) == "Seven"
        assert fizzbuzz_custom(14, rules) == "Seven"
        assert fizzbuzz_custom(5, rules) == "5"

    def test_custom_three_rules(self):
        rules = {2: "Fizz", 3: "Buzz", 5: "Bazz"}
        assert fizzbuzz_custom(30, rules) == "FizzBuzzBazz"

    def test_custom_rules_sorted_by_divisor(self):
        # Even if rules are given in different order, output should be sorted by divisor
        rules = {5: "Buzz", 3: "Fizz"}
        assert fizzbuzz_custom(15, rules) == "FizzBuzz"

    def test_custom_empty_rules(self):
        rules = {}
        assert fizzbuzz_custom(15, rules) == "15"


class TestFizzbuzzStats:
    """Tests for the fizzbuzz_stats function."""

    def test_stats_1_to_15(self):
        result = fizzbuzz_stats(1, 15)
        assert result["fizz"] == 4  # 3, 6, 9, 12
        assert result["buzz"] == 2  # 5, 10
        assert result["fizzbuzz"] == 1  # 15
        assert result["number"] == 8  # 1, 2, 4, 7, 8, 11, 13, 14

    def test_stats_1_to_30(self):
        result = fizzbuzz_stats(1, 30)
        assert result["fizz"] == 8  # 3, 6, 9, 12, 18, 21, 24, 27
        assert result["buzz"] == 4  # 5, 10, 20, 25
        assert result["fizzbuzz"] == 2  # 15, 30
        assert result["number"] == 16

    def test_stats_single_fizz(self):
        result = fizzbuzz_stats(3, 3)
        assert result == {"fizz": 1, "buzz": 0, "fizzbuzz": 0, "number": 0}

    def test_stats_single_buzz(self):
        result = fizzbuzz_stats(5, 5)
        assert result == {"fizz": 0, "buzz": 1, "fizzbuzz": 0, "number": 0}

    def test_stats_single_fizzbuzz(self):
        result = fizzbuzz_stats(15, 15)
        assert result == {"fizz": 0, "buzz": 0, "fizzbuzz": 1, "number": 0}

    def test_stats_single_number(self):
        result = fizzbuzz_stats(7, 7)
        assert result == {"fizz": 0, "buzz": 0, "fizzbuzz": 0, "number": 1}

    def test_stats_empty_range(self):
        result = fizzbuzz_stats(10, 5)
        assert result == {"fizz": 0, "buzz": 0, "fizzbuzz": 0, "number": 0}


class TestFizzbuzzGenerator:
    """Tests for the fizzbuzz_generator function."""

    def test_generator_returns_generator(self):
        gen = fizzbuzz_generator()
        assert isinstance(gen, Generator)

    def test_generator_first_15_values(self):
        gen = fizzbuzz_generator()
        values = [next(gen) for _ in range(15)]
        expected = [
            "1", "2", "Fizz", "4", "Buzz",
            "Fizz", "7", "8", "Fizz", "Buzz",
            "11", "Fizz", "13", "14", "FizzBuzz"
        ]
        assert values == expected

    def test_generator_start_from_10(self):
        gen = fizzbuzz_generator(start=10)
        values = [next(gen) for _ in range(6)]
        expected = ["Buzz", "11", "Fizz", "13", "14", "FizzBuzz"]
        assert values == expected

    def test_generator_start_from_1(self):
        gen = fizzbuzz_generator(start=1)
        assert next(gen) == "1"

    def test_generator_produces_many_values(self):
        gen = fizzbuzz_generator()
        # Get 100 values to ensure it doesn't stop
        values = [next(gen) for _ in range(100)]
        assert len(values) == 100
        assert values[99] == "Buzz"  # 100 is divisible by 5

    def test_generator_default_start(self):
        gen = fizzbuzz_generator()
        first = next(gen)
        assert first == "1"


class TestFizzbuzzJson:
    """Tests for the fizzbuzz_json function."""

    def test_json_1_to_3(self):
        import json
        result = fizzbuzz_json(1, 3)
        parsed = json.loads(result)
        assert len(parsed) == 3
        assert parsed[0] == {"n": 1, "result": "1"}
        assert parsed[1] == {"n": 2, "result": "2"}
        assert parsed[2] == {"n": 3, "result": "Fizz"}

    def test_json_empty_range(self):
        result = fizzbuzz_json(10, 5)
        assert result == "[]"

    def test_json_single_element(self):
        import json
        result = fizzbuzz_json(15, 15)
        parsed = json.loads(result)
        assert len(parsed) == 1
        assert parsed[0] == {"n": 15, "result": "FizzBuzz"}

    def test_json_is_single_line(self):
        result = fizzbuzz_json(1, 10)
        assert "\n" not in result

    def test_json_fizzbuzz_values(self):
        import json
        result = fizzbuzz_json(13, 16)
        parsed = json.loads(result)
        assert parsed[0]["result"] == "13"
        assert parsed[1]["result"] == "14"
        assert parsed[2]["result"] == "FizzBuzz"
        assert parsed[3]["result"] == "16"


class TestFizzbuzzCsv:
    """Tests for the fizzbuzz_csv function."""

    def test_csv_1_to_3(self):
        result = fizzbuzz_csv(1, 3)
        lines = result.split("\n")
        assert lines[0] == "n,result"
        assert lines[1] == "1,1"
        assert lines[2] == "2,2"
        assert lines[3] == "3,Fizz"

    def test_csv_ends_with_newline(self):
        result = fizzbuzz_csv(1, 3)
        assert result.endswith("\n")

    def test_csv_empty_range_has_header(self):
        result = fizzbuzz_csv(10, 5)
        assert result == "n,result\n"

    def test_csv_custom_delimiter(self):
        result = fizzbuzz_csv(1, 3, delimiter=";")
        lines = result.split("\n")
        assert lines[0] == "n;result"
        assert lines[1] == "1;1"

    def test_csv_fizzbuzz_value(self):
        result = fizzbuzz_csv(14, 16)
        lines = result.split("\n")
        assert "15,FizzBuzz" in lines

    def test_csv_tab_delimiter(self):
        result = fizzbuzz_csv(1, 2, delimiter="\t")
        lines = result.split("\n")
        assert lines[0] == "n\tresult"


class TestFizzbuzzMarkdownTable:
    """Tests for the fizzbuzz_markdown_table function."""

    def test_markdown_1_to_3(self):
        result = fizzbuzz_markdown_table(1, 3)
        lines = result.split("\n")
        assert "| n | result |" in lines[0]
        assert "|---|" in lines[1]
        assert "| 1 | 1 |" in lines[2]
        assert "| 3 | Fizz |" in lines[4]

    def test_markdown_no_trailing_newline(self):
        result = fizzbuzz_markdown_table(1, 3)
        assert not result.endswith("\n")

    def test_markdown_empty_range_has_header(self):
        result = fizzbuzz_markdown_table(10, 5)
        lines = result.split("\n")
        assert len(lines) == 2  # Header and separator only
        assert "| n | result |" in lines[0]

    def test_markdown_fizzbuzz_row(self):
        result = fizzbuzz_markdown_table(14, 16)
        assert "| 15 | FizzBuzz |" in result

    def test_markdown_has_separator_row(self):
        result = fizzbuzz_markdown_table(1, 1)
        lines = result.split("\n")
        assert "|---|" in lines[1] or "|--" in lines[1]


class TestFizzbuzzGrouped:
    """Tests for the fizzbuzz_grouped function."""

    def test_grouped_1_to_15(self):
        result = fizzbuzz_grouped(1, 15)
        assert result["Fizz"] == [3, 6, 9, 12]
        assert result["Buzz"] == [5, 10]
        assert result["FizzBuzz"] == [15]
        assert result["Number"] == [1, 2, 4, 7, 8, 11, 13, 14]

    def test_grouped_all_keys_present(self):
        result = fizzbuzz_grouped(1, 2)
        assert "Fizz" in result
        assert "Buzz" in result
        assert "FizzBuzz" in result
        assert "Number" in result

    def test_grouped_empty_range(self):
        result = fizzbuzz_grouped(10, 5)
        assert result == {"Fizz": [], "Buzz": [], "FizzBuzz": [], "Number": []}

    def test_grouped_values_sorted(self):
        result = fizzbuzz_grouped(1, 30)
        assert result["Fizz"] == sorted(result["Fizz"])
        assert result["Buzz"] == sorted(result["Buzz"])
        assert result["FizzBuzz"] == sorted(result["FizzBuzz"])
        assert result["Number"] == sorted(result["Number"])

    def test_grouped_only_fizz(self):
        result = fizzbuzz_grouped(3, 3)
        assert result["Fizz"] == [3]
        assert result["Buzz"] == []
        assert result["FizzBuzz"] == []
        assert result["Number"] == []

    def test_grouped_larger_range(self):
        result = fizzbuzz_grouped(1, 30)
        assert 15 in result["FizzBuzz"]
        assert 30 in result["FizzBuzz"]
        assert len(result["FizzBuzz"]) == 2
