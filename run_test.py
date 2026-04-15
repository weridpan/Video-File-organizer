#!/usr/bin/env python3
"""Test script for File Organizer with bug fixes"""

import sys
import os
from io import StringIO
from pathlib import Path

# Get the workspace directory
workspace = Path(__file__).parent

# Import the main script
sys.path.insert(0, str(workspace))

# Mock the input function with our test inputs
test_inputs = [
    "test_files",  # source directory
    "test_target",  # target directory
    "copy",  # operation (move or copy)
    "dry_run",  # mode (live or dry_run)
    "yes",  # cleanup empty folders
]

input_iter = iter(test_inputs)

original_input = __builtins__.input

def mock_input(prompt=""):
    """Mock input function with predefined test inputs"""
    value = next(input_iter)
    print(f"{prompt}{value}")
    return value

# Replace input function
__builtins__.input = mock_input

try:
    # Import and run the main module
    exec(open(str(workspace / "File Organizer - Video Focused.py")).read())
except StopIteration:
    print("\n[TEST] All inputs consumed successfully")
except Exception as e:
    print(f"\n[TEST ERROR] {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
finally:
    # Restore original input
    __builtins__.input = original_input
