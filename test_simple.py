#!/usr/bin/env python3
"""Simple test to verify basic functionality."""

def test_function(x: int) -> str:
    """Test function with type hints."""
    return str(x * 2)

class TestClass:
    """Test class."""
    
    def method(self, value: float) -> bool:
        """Test method."""
        return value > 0.0

# Test constant
TEST_CONSTANT = 42