"""Tests for tiered edge storage (edge_tier.py).

Unit tests for pure functions (no DB required).
"""

from app.services.edge_tier import holder_key, is_promoted


# --- holder_key ---

def test_holder_key_returns_min_first():
    assert holder_key(10, 5) == (5, 10)


def test_holder_key_already_ordered():
    assert holder_key(3, 7) == (3, 7)


def test_holder_key_symmetric():
    assert holder_key(42, 99) == holder_key(99, 42)


def test_holder_key_rejects_self_edge():
    import pytest
    with pytest.raises(AssertionError):
        holder_key(5, 5)


# --- is_promoted ---

def test_is_promoted_both_met():
    """Edge with weight >= 0.10 AND co_fire_count >= 2 is promoted."""
    assert is_promoted(0.10, 2) is True


def test_is_promoted_above_both():
    assert is_promoted(0.50, 10) is True


def test_is_promoted_weight_only():
    """Weight above threshold but co_fire_count below -> not promoted."""
    assert is_promoted(0.15, 1) is False


def test_is_promoted_cofires_only():
    """Co-fire count above threshold but weight below -> not promoted."""
    assert is_promoted(0.05, 5) is False


def test_is_promoted_neither():
    assert is_promoted(0.01, 0) is False


def test_is_promoted_exact_boundary():
    """Exactly at boundary values should be promoted."""
    assert is_promoted(0.10, 2) is True


def test_is_promoted_just_below_weight():
    assert is_promoted(0.099, 2) is False


def test_is_promoted_just_below_cofires():
    assert is_promoted(0.10, 1) is False
