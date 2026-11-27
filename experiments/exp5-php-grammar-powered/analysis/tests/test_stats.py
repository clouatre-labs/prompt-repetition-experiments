"""Tests for stats.py: sign convention, asymptotic tie handling, zero-variance guard."""

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from stats import U_METHOD, WILSON_Z, bootstrap_ci, mann_whitney_r, wilson_ci  # noqa: E402


def test_mann_whitney_r_sign_follows_treatment_arm():
    control = [1, 2, 2, 3, 2]
    treatment = [3, 4, 4, 5, 4]

    forward = mann_whitney_r(treatment, control)
    swapped = mann_whitney_r(control, treatment)

    assert forward["r"] > 0
    assert swapped["r"] == -forward["r"]
    assert forward["p"] < 0.05
    assert U_METHOD == "asymptotic"


def test_mann_whitney_r_tie_heavy_asymptotic_finite_p():
    rng = np.random.default_rng(7)
    treatment = rng.integers(0, 2, 20) + rng.integers(0, 2, 20)  # many ties over {0,1,2}
    control = rng.integers(0, 2, 20)

    result = mann_whitney_r(treatment, control)

    assert np.isfinite(result["p"])
    assert -1 <= result["r"] <= 1
    json.dumps(result, allow_nan=False)  # finite, serialisable numbers only


def test_mann_whitney_r_zero_variance_arms():
    result = mann_whitney_r([4, 4, 4, 4, 4], [4, 4, 4, 4, 4])

    assert result["p"] is None
    assert result["r"] == 0
    assert "zero-variance" in result["note"]
    json.dumps(result, allow_nan=False)


def test_wilson_ci_uses_hardcoded_z():
    low, high = wilson_ci(1, 10)

    assert WILSON_Z == 1.959963984540054
    assert (low, high) == (0.0179, 0.4042)  # matches the Exp4 analysis.json value


def test_bootstrap_ci_is_seeded_and_deterministic():
    first = bootstrap_ci([3, 4, 4, 5, 4], [1, 2, 2, 3, 2], seed=11)
    second = bootstrap_ci([3, 4, 4, 5, 4], [1, 2, 2, 3, 2], seed=11)

    assert first == second
    assert first["seed"] == 11
    assert first["low"] <= first["high"]
