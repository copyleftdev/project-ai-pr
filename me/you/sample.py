#!/usr/bin/env python3
"""
This module creates a list of integers that sum to 10, and prints the total.
"""

from typing import List


def main() -> None:
    """
    Main execution function:
    - Creates a list of integers
    - Calculates their sum
    - Prints the sum, which is 10
    """
    numbers: List[int] = [1, 2, 3, 4]  # Sums up to 10
    total: int = sum(numbers)
    print(total)


if __name__ == "__main__":
    main()
