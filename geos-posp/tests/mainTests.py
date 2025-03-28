# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Alexandre Benedicto
import os
import sys
import unittest

dir_path = os.path.dirname(os.path.realpath(__file__))
parent_dir_path = os.path.join(os.path.dirname(dir_path), "src")
if parent_dir_path not in sys.path:
    sys.path.append(parent_dir_path)


def main() -> None:
    """Run all tests."""
    # Load all test cases in the current folder
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(".", pattern="tests*.py")

    # Run the test suite
    runner = unittest.TextTestRunner()
    runner.run(test_suite)


if __name__ == "__main__":
    main()
