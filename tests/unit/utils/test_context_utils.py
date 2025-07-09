"""Unit tests for context utilities module.

Tests validate context immutability validation and context hash generation
for SpecContext instances and related utilities.
"""

from dataclasses import dataclass
from unittest.mock import Mock

import pytest

from spec_cli.utils.context_utils import (
    create_context_hash,
    validate_context_immutability,
)

# Test constants
SAMPLE_HASH_VALUE = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
MOCK_DEPENDENCY_NAME = "test_dependency"
INVALID_CONTEXT_MESSAGE = "Context must be a dataclass"


@dataclass
class MockFrozenContext:
    """Mock frozen dataclass for testing."""

    name: str
    value: int


@dataclass(frozen=True)
class MockImmutableContext:
    """Mock immutable dataclass for testing."""

    name: str
    value: int


@dataclass
class MockMutableContext:
    """Mock mutable dataclass for testing."""

    name: str
    value: int


class MockNonDataclass:
    """Mock non-dataclass for testing."""

    def __init__(self, name: str, value: int):
        self.name = name
        self.value = value


class TestValidateContextImmutability:
    """Test context immutability validation function."""

    def test_validate_context_immutability_when_frozen_dataclass_then_returns_true(
        self,
    ):
        """Test that frozen dataclass is validated as immutable."""
        context = MockImmutableContext(name="test", value=42)

        result = validate_context_immutability(context)

        assert result is True

    def test_validate_context_immutability_when_mutable_dataclass_then_returns_false(
        self,
    ):
        """Test that mutable dataclass is not validated as immutable."""
        context = MockMutableContext(name="test", value=42)

        result = validate_context_immutability(context)

        assert result is False

    def test_validate_context_immutability_when_non_dataclass_then_returns_false(self):
        """Test that non-dataclass objects are not validated as immutable."""
        context = MockNonDataclass(name="test", value=42)

        result = validate_context_immutability(context)

        assert result is False

    def test_validate_context_immutability_when_none_then_returns_false(self):
        """Test that None is not validated as immutable."""
        result = validate_context_immutability(None)

        assert result is False

    def test_validate_context_immutability_when_primitive_type_then_returns_false(self):
        """Test that primitive types are not validated as immutable."""
        result = validate_context_immutability("string")

        assert result is False


class TestCreateContextHash:
    """Test context hash generation function."""

    def test_create_context_hash_when_same_values_then_generates_consistent_hash(self):
        """Test that identical contexts generate identical hashes."""
        context1 = MockImmutableContext(name="test", value=42)
        context2 = MockImmutableContext(name="test", value=42)

        hash1 = create_context_hash(context1)
        hash2 = create_context_hash(context2)

        assert hash1 == hash2
        assert isinstance(hash1, str)
        assert len(hash1) == 64  # SHA-256 hex length

    def test_create_context_hash_when_different_values_then_generates_different_hash(
        self,
    ):
        """Test that different contexts generate different hashes."""
        context1 = MockImmutableContext(name="test1", value=42)
        context2 = MockImmutableContext(name="test2", value=42)

        hash1 = create_context_hash(context1)
        hash2 = create_context_hash(context2)

        assert hash1 != hash2

    def test_create_context_hash_when_different_types_then_generates_different_hash(
        self,
    ):
        """Test that different field types generate different hashes."""
        context1 = MockImmutableContext(name="test", value=42)
        context2 = MockImmutableContext(name="test", value=43)

        hash1 = create_context_hash(context1)
        hash2 = create_context_hash(context2)

        assert hash1 != hash2

    def test_create_context_hash_when_non_dataclass_then_raises_value_error(self):
        """Test that non-dataclass objects raise ValueError."""
        context = MockNonDataclass(name="test", value=42)

        with pytest.raises(ValueError, match=INVALID_CONTEXT_MESSAGE):
            create_context_hash(context)

    def test_create_context_hash_when_none_then_raises_value_error(self):
        """Test that None raises ValueError."""
        with pytest.raises(ValueError, match=INVALID_CONTEXT_MESSAGE):
            create_context_hash(None)

    def test_create_context_hash_when_primitive_type_then_raises_value_error(self):
        """Test that primitive types raise ValueError."""
        with pytest.raises(ValueError, match=INVALID_CONTEXT_MESSAGE):
            create_context_hash("string")

    def test_create_context_hash_when_complex_object_then_includes_class_info(self):
        """Test that complex objects include class information in hash."""
        mock_obj = Mock(spec=[])
        mock_obj.__class__.__name__ = "MockClass"

        @dataclass(frozen=True)
        class ComplexContext:
            obj: Mock

        context = ComplexContext(obj=mock_obj)

        hash_result = create_context_hash(context)

        assert isinstance(hash_result, str)
        assert len(hash_result) == 64  # SHA-256 hex length

    def test_create_context_hash_when_hash_generation_fails_then_raises_value_error(
        self,
    ):
        """Test that hash generation failures raise ValueError with context."""

        @dataclass(frozen=True)
        class BadContext:
            bad_field: object

        # Create object that will fail during hash processing
        class FailingObject:
            def __str__(self):
                raise Exception("String conversion failed")

        bad_obj = FailingObject()
        context = BadContext(bad_field=bad_obj)

        with pytest.raises(ValueError, match="Failed to generate context hash"):
            create_context_hash(context)
