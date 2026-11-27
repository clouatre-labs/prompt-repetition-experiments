"""Statistics helpers for the Exp5 analysis.

Sign convention: ``mann_whitney_r(treatment, control)`` passes the treatment
arm as ``x`` to ``scipy.stats.mannwhitneyu`` and returns the rank-biserial
correlation ``r = 2*U1/(n1*n2) - 1`` where ``U1`` is the U statistic scipy
reports for its first argument (treatment). Positive r therefore means
treatment scores tend to be higher than control scores (Kerby 2014, the
simple difference formula). The method is pinned to ``asymptotic`` because
the tie-heavy fractional rubric scores violate the exact method's assumption.
"""

from __future__ import annotations

import numpy as np
from scipy import stats

WILSON_Z = 1.959963984540054
U_METHOD = "asymptotic"
EFFECT_SIZE_NOTE = (
    "r = 2*U1/(n1*n2) - 1 with U1 taken for x=treatment (y=control), so "
    "positive r means treatment > control; two-sided asymptotic "
    "Mann-Whitney U without continuity correction; CI is a percentile "
    "bootstrap over resampled runs"
)
ZERO_VARIANCE_NOTE = (
    "zero-variance guard: at least one arm is constant, so p is null and r is 0"
)


def wilson_ci(passed: int, total: int) -> tuple[float, float]:
    """Wilson score 95% interval for a proportion, rounded to 4 decimals."""
    if total == 0:
        return 0.0, 0.0
    p = passed / total
    z2 = WILSON_Z * WILSON_Z
    denom = 1 + z2 / total
    centre = (p + z2 / (2 * total)) / denom
    half = WILSON_Z * float(np.sqrt(p * (1 - p) / total + z2 / (4 * total * total))) / denom
    return round(centre - half, 4), round(centre + half, 4)


def mann_whitney_r(treatment, control) -> dict:
    """Two-sided asymptotic Mann-Whitney U plus rank-biserial r.

    Returns ``{"u", "p", "r", "n1", "n2", "note"}``. On a zero-variance arm
    the result is ``p=null, r=0`` with a note; NaN and Infinity are never
    emitted.
    """
    x = np.asarray(treatment, dtype=float)
    y = np.asarray(control, dtype=float)
    out = {"u": None, "p": None, "r": None, "n1": int(x.size), "n2": int(y.size), "note": None}
    if x.size == 0 or y.size == 0:
        out["note"] = "empty arm: test not defined"
        return out
    if np.ptp(x) == 0 and np.ptp(y) == 0:
        out["r"] = 0
        out["note"] = ZERO_VARIANCE_NOTE
        return out
    res = stats.mannwhitneyu(x, y, alternative="two-sided", method=U_METHOD)
    u1 = float(res.statistic)
    r = float(2 * u1 / (x.size * y.size) - 1)
    p = float(res.pvalue)
    if not (np.isfinite(u1) and np.isfinite(r) and np.isfinite(p)):
        out.update(u=round(u1, 4) if np.isfinite(u1) else None, r=0, note=ZERO_VARIANCE_NOTE)
        return out
    out.update(u=round(u1, 4), p=round(p, 4), r=round(r, 4))
    return out


def bootstrap_ci(treatment, control, seed: int, iterations: int = 1000) -> dict:
    """Percentile bootstrap CI for r using numpy.random.default_rng(seed)."""
    x = np.asarray(treatment, dtype=float)
    y = np.asarray(control, dtype=float)
    if x.size == 0 or y.size == 0:
        return {"low": None, "high": None, "iterations": iterations, "seed": seed}
    rng = np.random.default_rng(seed)
    rs = []
    for _ in range(iterations):
        bx = x[rng.integers(0, x.size, x.size)]
        by = y[rng.integers(0, y.size, y.size)]
        u1 = float(stats.mannwhitneyu(bx, by, alternative="two-sided", method=U_METHOD).statistic)
        value = 2 * u1 / (x.size * y.size) - 1
        rs.append(value if np.isfinite(value) else 0.0)
    return {
        "low": round(float(np.percentile(rs, 2.5)), 4),
        "high": round(float(np.percentile(rs, 97.5)), 4),
        "iterations": iterations,
        "seed": seed,
    }
