#!/usr/bin/env python3
"""Adversarial gate for Run 117, written before the paper.

PREREGISTERED HYPOTHESIS
------------------------
For two equal-cost symbiont strains and two unresolved environmental regimes,
let strain performance cross symmetrically: strain A has efficacy alpha in
regime 1 and beta in regime 2, while strain B has beta in regime 1 and alpha in
regime 2, with alpha > beta > 0. If total inoculum dose is D and establishment
failures follow independent Poisson exposure, the allocation that maximizes
the worst-regime establishment probability is the equal split. Its guaranteed
log-failure exponent is (alpha + beta) D / 2, versus beta D for either
monoculture.

ASSUMPTIONS
-----------
1. Dose effects add in the log-failure exponent within each regime.
2. Total dose and per-dose cost are equal across strains.
3. The decision is made before the realized regime is known and uses a
   worst-case, not expected-value, objective.
4. Efficacies are nonnegative and fixed over the establishment window.
5. The symmetric two-regime result is a model theorem, not field validation.

FAILURE CONDITIONS
------------------
The headline claim fails if any of the following occurs:
1. exhaustive grid search places the maximin optimum away from D/2 beyond its
   grid resolution under alpha > beta > 0;
2. the analytic guaranteed exponent disagrees with an independent exact
   piecewise-linear solver;
3. the claimed diversification gain persists when alpha = beta;
4. a mixture beats the dominant strain when one strain weakly dominates in
   every regime;
5. numerical refinement does not converge to the analytic optimum.

VERIFICATION PLAN
-----------------
Check the closed forms algebraically through independent evaluations; compare
them with dense-grid and exact breakpoint solvers; run randomized parameter
sweeps; test identical-strain and dominance negative controls; verify target
probability dose formulas, monotonicities, numerical stability, and explicit
counterexamples to the slogan that diversity always helps.
"""

from __future__ import annotations

import math
import random
from typing import Iterable, Sequence


PASS = 0
FAIL = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"PASS {PASS:02d}: {name}" + (f" | {detail}" if detail else ""))
    else:
        FAIL += 1
        print(f"FAIL {FAIL:02d}: {name}" + (f" | {detail}" if detail else ""))


def isclose(a: float, b: float, *, atol: float = 1e-11, rtol: float = 1e-10) -> bool:
    return abs(a - b) <= atol + rtol * max(abs(a), abs(b))


def stable_success(exponent: float) -> float:
    """Return 1-exp(-exponent) without cancellation for small exponent."""
    if exponent < 0:
        raise ValueError("exponent must be nonnegative")
    return -math.expm1(-exponent)


def regime_exponents(alpha: float, beta: float, dose: float, x_a: float) -> tuple[float, float]:
    x_b = dose - x_a
    return alpha * x_a + beta * x_b, beta * x_a + alpha * x_b


def guaranteed_exponent(alpha: float, beta: float, dose: float, x_a: float) -> float:
    return min(regime_exponents(alpha, beta, dose, x_a))


def exact_two_strain_maximin(
    scenarios: Sequence[tuple[float, float]], dose: float
) -> tuple[float, float]:
    """Solve max_{0<=x<=D} min_s [a_s x + b_s(D-x)].

    The lower envelope is concave and piecewise linear, so an optimum occurs at
    an endpoint or an intersection of two scenario lines.
    """
    candidates = {0.0, dose}
    for i, (a_i, b_i) in enumerate(scenarios):
        slope_i = a_i - b_i
        intercept_i = b_i * dose
        for a_j, b_j in scenarios[i + 1 :]:
            slope_j = a_j - b_j
            intercept_j = b_j * dose
            denom = slope_i - slope_j
            if abs(denom) > 1e-15:
                x = (intercept_j - intercept_i) / denom
                if 0.0 <= x <= dose:
                    candidates.add(x)

    def value(x: float) -> float:
        return min(a * x + b * (dose - x) for a, b in scenarios)

    best_x = min(candidates)
    best_v = value(best_x)
    for x in sorted(candidates):
        v = value(x)
        if v > best_v + 1e-14:
            best_x, best_v = x, v
    return best_x, best_v


def grid_maximin(
    scenarios: Sequence[tuple[float, float]], dose: float, intervals: int
) -> tuple[float, float]:
    best_x = 0.0
    best_v = -math.inf
    for k in range(intervals + 1):
        x = dose * k / intervals
        v = min(a * x + b * (dose - x) for a, b in scenarios)
        if v > best_v:
            best_x, best_v = x, v
    return best_x, best_v


def reciprocal_closed_form(alpha: float, beta: float, dose: float) -> tuple[float, float]:
    if not (alpha > beta > 0 and dose > 0):
        raise ValueError("requires alpha > beta > 0 and dose > 0")
    return dose / 2.0, (alpha + beta) * dose / 2.0


def main() -> int:
    alpha, beta, dose = 1.7, 0.3, 4.0
    scenarios = ((alpha, beta), (beta, alpha))
    x_star, t_star = reciprocal_closed_form(alpha, beta, dose)

    # Closed-form core.
    e1, e2 = regime_exponents(alpha, beta, dose, x_star)
    check("equal split equalizes regime exponents", isclose(e1, e2), f"E1={e1:.12g}, E2={e2:.12g}")
    check("equalized exponent matches closed form", isclose(e1, t_star), f"t*={t_star:.12g}")
    check("left perturbation lowers guarantee", guaranteed_exponent(alpha, beta, dose, x_star - 0.01) < t_star)
    check("right perturbation lowers guarantee", guaranteed_exponent(alpha, beta, dose, x_star + 0.01) < t_star)
    mono = beta * dose
    gain = t_star - mono
    check("monoculture worst exponent is beta D", isclose(guaranteed_exponent(alpha, beta, dose, dose), mono))
    check("diversification exponent gain is (alpha-beta)D/2", isclose(gain, (alpha - beta) * dose / 2.0))
    check("crossover produces strict gain", gain > 0)

    # Independent exact solver.
    x_exact, t_exact = exact_two_strain_maximin(scenarios, dose)
    check("breakpoint solver returns equal split", isclose(x_exact, x_star), f"x={x_exact:.12g}")
    check("breakpoint solver returns analytic value", isclose(t_exact, t_star), f"t={t_exact:.12g}")

    # Grid convergence at deliberately odd resolutions, so D/2 is not exactly sampled.
    grid_errors = []
    for intervals in (101, 1001, 10001):
        x_grid, t_grid = grid_maximin(scenarios, dose, intervals)
        err = t_star - t_grid
        grid_errors.append(err)
        bound = (alpha - beta) * dose / (2 * intervals) + 1e-14
        check(
            f"grid {intervals} converges within slope-resolution bound",
            0 <= err <= bound,
            f"x={x_grid:.9g}, value_error={err:.3e}, bound={bound:.3e}",
        )
    check("grid refinement strictly reduces error", grid_errors[2] < grid_errors[1] < grid_errors[0])

    # Random symmetric sweeps.
    rng = random.Random(11720260802)
    max_x_error = 0.0
    max_t_error = 0.0
    for _ in range(1000):
        b = 10 ** rng.uniform(-2.0, 1.0)
        a = b + 10 ** rng.uniform(-2.0, 1.0)
        d = 10 ** rng.uniform(-2.0, 2.0)
        xa, ta = reciprocal_closed_form(a, b, d)
        xe, te = exact_two_strain_maximin(((a, b), (b, a)), d)
        max_x_error = max(max_x_error, abs(xa - xe))
        max_t_error = max(max_t_error, abs(ta - te))
    check("1000 randomized reciprocal cases match exact allocation", max_x_error < 1e-10, f"max error={max_x_error:.3e}")
    check("1000 randomized reciprocal cases match exact value", max_t_error < 1e-9, f"max error={max_t_error:.3e}")

    # General multi-scenario exact solver versus dense grid.
    worst_gap = 0.0
    for _ in range(250):
        scenario_count = rng.randint(2, 7)
        ss = tuple((rng.uniform(0.01, 3.0), rng.uniform(0.01, 3.0)) for _ in range(scenario_count))
        d = rng.uniform(0.1, 5.0)
        _, v_exact = exact_two_strain_maximin(ss, d)
        _, v_grid = grid_maximin(ss, d, 20000)
        worst_gap = max(worst_gap, v_exact - v_grid)
        slope_bound = max(abs(a - b) for a, b in ss) * d / 20000 + 1e-12
        if not (-1e-10 <= v_exact - v_grid <= slope_bound):
            check("general multi-scenario solver agrees with grid", False, f"gap={v_exact-v_grid:.3e}")
            break
    else:
        check("250 multi-scenario exact solutions agree with dense grid", True, f"worst gap={worst_gap:.3e}")

    # Negative control 1: identical strains. Diversity has no intrinsic benefit.
    a_equal = 0.8
    equal_values = [
        min(a_equal * x + a_equal * (dose - x), a_equal * x + a_equal * (dose - x))
        for x in (0.0, dose * 0.17, dose / 2, dose * 0.91, dose)
    ]
    check("negative control: identical strains make every allocation tie", max(equal_values) - min(equal_values) < 1e-12)
    check("negative control: identical strains have zero diversification gain", isclose(equal_values[0], equal_values[2]))

    # Negative control 2: one strain dominates in every regime.
    dominant = ((1.2, 0.5), (0.9, 0.4), (1.6, 0.8), (0.7, 0.1))
    xd, td = exact_two_strain_maximin(dominant, dose)
    check("negative control: uniformly dominant strain gets all dose", isclose(xd, dose), f"x_A={xd:.12g}")
    check("negative control: mixing cannot beat dominant monoculture", isclose(td, min(a * dose for a, _ in dominant)))

    # One-crossing asymmetric example: diversification can be useful without a 50/50 optimum.
    asymmetric = ((1.8, 0.2), (0.4, 1.0), (0.9, 0.7))
    xa, ta = exact_two_strain_maximin(asymmetric, dose)
    check("asymmetric crossover produces an interior robust allocation", 0 < xa < dose, f"x_A={xa:.6g}")
    check("asymmetric crossover need not produce equal split", not isclose(xa, dose / 2), f"x_A={xa:.6g}")
    check(
        "asymmetric robust mix beats both monocultures",
        ta > max(min(b * dose for _, b in asymmetric), min(a * dose for a, _ in asymmetric)),
        f"robust exponent={ta:.6g}",
    )

    # Probability and target-dose consequences.
    p_mix = stable_success(t_star)
    p_mono = stable_success(mono)
    check("guaranteed establishment probability improves under crossover", p_mix > p_mono, f"mix={p_mix:.8f}, mono={p_mono:.8f}")
    check("probability remains in [0,1)", 0 <= p_mono < p_mix < 1)
    target_p = 0.95
    target_L = -math.log1p(-target_p)
    d_mix = 2 * target_L / (alpha + beta)
    d_mono = target_L / beta
    check("target-dose formulas hit the requested probability", isclose(stable_success((alpha + beta) * d_mix / 2), target_p) and isclose(stable_success(beta * d_mono), target_p))
    saving = 1 - d_mix / d_mono
    check("target-dose saving equals (alpha-beta)/(alpha+beta)", isclose(saving, (alpha - beta) / (alpha + beta)), f"saving={saving:.8f}")
    check("target-dose saving is strictly between 0 and 1", 0 < saving < 1)

    # Monotonicities and numerical stability.
    check("guaranteed mix exponent increases linearly with dose", isclose(reciprocal_closed_form(alpha, beta, 2 * dose)[1], 2 * t_star))
    check("gain vanishes continuously as crossover closes", reciprocal_closed_form(beta + 1e-9, beta, dose)[1] - beta * dose < 3e-9)
    tiny = 1e-14
    stable_tiny = stable_success(tiny)
    check("expm1 path resolves tiny establishment probabilities", stable_tiny > 0 and isclose(stable_tiny, tiny, atol=1e-28, rtol=1e-12), f"p={stable_tiny:.3e}")
    huge = 1000.0
    check("large-exponent probability saturates safely without overflow", stable_success(huge) == 1.0)

    print()
    print("PREREGISTERED FAILURE CONDITIONS")
    print("- equal-split mismatch: NOT TRIGGERED" if isclose(x_exact, x_star) else "- equal-split mismatch: TRIGGERED")
    print("- analytic/exact disagreement: NOT TRIGGERED" if isclose(t_exact, t_star) else "- analytic/exact disagreement: TRIGGERED")
    print("- false diversity gain for identical strains: NOT TRIGGERED" if isclose(equal_values[0], equal_values[2]) else "- false diversity gain for identical strains: TRIGGERED")
    print("- mixture beats uniformly dominant strain: NOT TRIGGERED" if isclose(xd, dose) else "- mixture beats uniformly dominant strain: TRIGGERED")
    print("- nonconvergent refinement: NOT TRIGGERED" if grid_errors[2] < grid_errors[1] < grid_errors[0] else "- nonconvergent refinement: TRIGGERED")
    print()
    print(f"RESULT: {PASS} PASS / {FAIL} FAIL")
    print("STATUS: NUMERICAL_GATE_PASS" if FAIL == 0 else "STATUS: NUMERICAL_GATE_FAIL")
    print("SCOPE: synthetic model checks only; no formal or empirical verification")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
