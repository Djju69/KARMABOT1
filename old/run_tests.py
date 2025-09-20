#!/usr/bin/env python3
"""
Test runner for KarmaBot tests.
This script sets up the test environment before running pytest.
"""
import os
import sys
import pytest

# Set up test environment variables before importing any application code
os.environ["BOT_TOKEN"] = "test_token"
os.environ["ADMIN_IDS"] = "12345,67890"
os.environ["DB_URL"] = "sqlite:///:memory:"
os.environ["TESTING"] = "true"

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

# Import the test modules after setting up the environment
import tests.conftest  # noqa: F401

if __name__ == "__main__":
    # Run pytest with the current script's directory as the test directory
    sys.exit(pytest.main([os.path.dirname(__file__)]))
