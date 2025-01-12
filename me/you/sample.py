#!/usr/bin/env python3
"""
This module demonstrates a simple example of defining and printing a list in Python.
"""

from typing import List


def main() -> None:
    """
    Main execution function:
    - Creates a list of integers
    - Prints them to standard output
    """
    numbers: List[int] = [1, 2, 3]
    print(numbers)


if __name__ == "__main__":
    main()
