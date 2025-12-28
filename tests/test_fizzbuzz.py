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
