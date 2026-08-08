#!/usr/bin/env python3
"""Adversarial numerical/symbolic gate for Run 118.

The script uses only the Python standard library.  It tests the preregistered
phasor identity, variance bound, equality/negative controls, Monte Carlo stress
cases, and time-domain convergence independently of the manuscript.
"""

from __future__ import annotations

import cmath
import math
import random

SEED = 118042026
TOL = 2.0e-11
rng = random.Random(SEED)

passes = 0
failures = []


def check(name: str, condition: bool, detail: str) -> None:
    global passes
    if condition:
        passes += 1
        print(f"PASS {passes:02d} | {name} | {detail}")
    else:
        failures.append((name, detail))
        print(f"FAIL {len(failures):02d} | {name} | {detail}")


def normalized_weights(raw: list[float]) -> list[float]:
    total = sum(raw)
    return [x / total for x in raw]


def phasor(weights: list[float], delays: list[float], omega: float) -> complex:
    return sum(
        (w * cmath.exp(-1j * omega * tau) for w, tau in zip(weights, delays)),
        start=0j,
    )


def eta(weights: list[float], delays: list[float], omega: float) -> float:
    return abs(phasor(weights, delays, omega)) ** 2


def pairwise_eta(weights: list[float], delays: list[float], omega: float) -> float:
    loss = 0.0
    for i in range(len(weights)):
        for j in range(i + 1, len(weights)):
            loss += 2.0 * weights[i] * weights[j] * (
                1.0 - math.cos(omega * (delays[i] - delays[j]))
            )
    return 1.0 - loss


def weighted_variance(weights: list[float], delays: list[float]) -> float:
    mean = sum(w * t for w, t in zip(weights, delays))
    return sum(w * (t - mean) ** 2 for w, t in zip(weights, delays))


print("RUN 118 ADVERSARIAL GATE")
print(f"seed={SEED} tolerance={TOL:.1e}")
print("HYPOTHESIS H1: asynchronous nonnegative fusion has eta=|sum w_i exp(-i omega tau_i)|^2.")
print("HYPOTHESIS H2: 1-eta <= omega^2 Var_w(tau), hence eta >= 1-omega^2 Var_w(tau).")
print("ASSUMPTIONS: normalized nonnegative effective weights; locally common harmonic mode; known delays.")
print("FALSIFIERS: identity error > tolerance; eta outside [0,1]; variance bound violation; convergence failure.")
print("NEGATIVE CONTROLS: equal delays, DC, singleton, and balanced half-period cancellation.")
print()

# Exact controls and a deliberately destructive counterexample.
check("equal-delay control", abs(eta([0.2, 0.3, 0.5], [7.0, 7.0, 7.0], 2.3) - 1.0) < TOL, "eta=1")
check("DC control", abs(eta([0.2, 0.3, 0.5], [-9.0, 2.0, 40.0], 0.0) - 1.0) < TOL, "omega=0 gives eta=1")
check("singleton control", abs(eta([1.0], [123.0], 8.0) - 1.0) < TOL, "one active channel gives eta=1")
cancel = eta([0.5, 0.5], [0.0, math.pi], 1.0)
check("half-period cancellation", cancel < 1.0e-30, f"eta={cancel:.3e}")
quarter = eta([0.5, 0.5], [0.0, math.pi / 2.0], 1.0)
check("two-channel exact law", abs(quarter - 0.5) < TOL, f"eta={quarter:.15f}")

# Hand-auditable three-channel example.
w0 = [0.5, 0.3, 0.2]
t0 = [0.0, 0.25, 0.75]
o0 = 1.7
e_direct = eta(w0, t0, o0)
e_pair = pairwise_eta(w0, t0, o0)
v0 = weighted_variance(w0, t0)
check("worked identity", abs(e_direct - e_pair) < TOL, f"direct={e_direct:.15f} pairwise={e_pair:.15f}")
check("worked variance bound", 1.0 - e_direct <= o0 * o0 * v0 + TOL, f"loss={1-e_direct:.9f} bound={o0*o0*v0:.9f}")
check("worked efficiency range", -TOL <= e_direct <= 1.0 + TOL, f"eta={e_direct:.12f}")

# Monte Carlo adversarial stress: wide delays and frequencies, including phase wraps.
max_identity_error = 0.0
min_eta = float("inf")
max_eta = -float("inf")
max_bound_violation = -float("inf")
for _ in range(5000):
    n = rng.randint(2, 12)
    weights = normalized_weights([10.0 ** rng.uniform(-5.0, 2.0) for _ in range(n)])
    delays = [rng.uniform(-25.0, 25.0) for _ in range(n)]
    omega = 10.0 ** rng.uniform(-3.0, 1.5)
    direct = eta(weights, delays, omega)
    pair = pairwise_eta(weights, delays, omega)
    variance = weighted_variance(weights, delays)
    max_identity_error = max(max_identity_error, abs(direct - pair))
    min_eta = min(min_eta, direct)
    max_eta = max(max_eta, direct)
    max_bound_violation = max(max_bound_violation, (1.0 - direct) - omega * omega * variance)

check("Monte Carlo identity", max_identity_error < TOL, f"5000 cases max_error={max_identity_error:.3e}")
check("Monte Carlo eta lower", min_eta >= -TOL, f"min_eta={min_eta:.6e}")
check("Monte Carlo eta upper", max_eta <= 1.0 + TOL, f"max_eta={max_eta:.15f}")
check("Monte Carlo variance bound", max_bound_violation <= TOL, f"max_violation={max_bound_violation:.3e}")

# Translation invariance and permutation invariance are protocol sanity checks.
weights = normalized_weights([0.7, 1.3, 0.2, 3.4])
delays = [-2.0, 0.1, 0.4, 5.0]
omega = 0.83
base = eta(weights, delays, omega)
shifted = eta(weights, [t + 918.5 for t in delays], omega)
check("common-time translation invariance", abs(base - shifted) < TOL, f"difference={abs(base-shifted):.3e}")
perm = [2, 0, 3, 1]
permuted = eta([weights[i] for i in perm], [delays[i] for i in perm], omega)
check("channel permutation invariance", abs(base - permuted) < TOL, f"difference={abs(base-permuted):.3e}")

# Small-delay asymptotic: (1-eta)/(omega^2 Var) -> 1 as delay scale -> 0.
weights = [0.15, 0.25, 0.60]
shape = [-1.0, 0.25, 1.1]
ratios = []
for scale in [1.0e-1, 5.0e-2, 2.5e-2, 1.25e-2]:
    delays = [scale * x for x in shape]
    variance = weighted_variance(weights, delays)
    ratios.append((1.0 - eta(weights, delays, 1.0)) / variance)
errors = [abs(x - 1.0) for x in ratios]
check("small-delay asymptotic approaches one", errors[-1] < errors[0] and errors[-1] < 1.0e-4, f"ratios={[round(x, 8) for x in ratios]}")
orders = [math.log(errors[i] / errors[i + 1], 2.0) for i in range(len(errors) - 1)]
check("small-delay second-order convergence", min(orders) > 1.95, f"observed_orders={[round(x, 4) for x in orders]}")

# Independent time-domain check against direct sampled cosine fusion.
weights = [0.4, 0.35, 0.25]
delays = [0.0, 0.37, 1.21]
omega = 1.13
target_eta = eta(weights, delays, omega)
time_errors = []
for samples in [256, 1024, 4096, 16384]:
    y2 = 0.0
    x2 = 0.0
    for k in range(samples):
        t = 2.0 * math.pi * k / (omega * samples)
        x = math.cos(omega * t)
        y = sum(w * math.cos(omega * (t - tau)) for w, tau in zip(weights, delays))
        x2 += x * x
        y2 += y * y
    empirical = y2 / x2
    time_errors.append(abs(empirical - target_eta))
check("time-domain energy identity", time_errors[-1] < TOL, f"target={target_eta:.15f} error={time_errors[-1]:.3e}")
check("time-domain convergence stable", max(time_errors) < TOL, f"errors={[f'{x:.2e}' for x in time_errors]}")

# Bandlimited mixture: output/input energy is the spectral-weighted eta average.
freqs = [0.2, 0.7, 1.6, 2.4]
amps = [1.0, 0.4, 0.7, 0.25]
weights = [0.2, 0.3, 0.5]
delays = [-0.1, 0.25, 0.8]
spectral_ratio = sum(a * a * eta(weights, delays, o) for a, o in zip(amps, freqs)) / sum(a * a for a in amps)
variance = weighted_variance(weights, delays)
omega_max = max(freqs)
check("bandlimited spectral lower bound", spectral_ratio + TOL >= 1.0 - omega_max * omega_max * variance, f"ratio={spectral_ratio:.9f} lower={1-omega_max*omega_max*variance:.9f}")

# Threshold budget: Var <= (1-q)/Omega^2 is sufficient for eta >= q on every tested mode.
q = 0.90
omega_max = 2.0
budget = (1.0 - q) / (omega_max * omega_max)
weights = [0.25, 0.35, 0.40]
shape = [-1.0, 0.0, 1.0]
shape_var = weighted_variance(weights, shape)
scale = math.sqrt(0.99 * budget / shape_var)
delays = [scale * x for x in shape]
grid_min = min(eta(weights, delays, omega_max * k / 1000.0) for k in range(1001))
check("sufficient alignment budget", weighted_variance(weights, delays) <= budget + TOL and grid_min >= q - TOL, f"variance={weighted_variance(weights,delays):.9f} budget={budget:.9f} min_eta={grid_min:.9f}")

# The bound must be described as sufficient, not necessary: a wrapped full-period delay
# has perfect phase alignment but very large raw delay variance.
weights = [0.5, 0.5]
delays = [0.0, 2.0 * math.pi]
wrapped_eta = eta(weights, delays, 1.0)
wrapped_var = weighted_variance(weights, delays)
check("non-necessity control", abs(wrapped_eta - 1.0) < TOL and wrapped_var > 1.0, f"eta={wrapped_eta:.15f} variance={wrapped_var:.6f}")

print()
print(f"SUMMARY: {passes} PASS / {len(failures)} FAIL")
if failures:
    print("STATUS: NUMERICAL_GATE_FAIL")
    for name, detail in failures:
        print(f"BLOCKER: {name}: {detail}")
    raise SystemExit(1)
print("STATUS: NUMERICAL_GATE_PASS")
print("INTERPRETATION: finite adversarial checks support the stated model identities and bound; they are not formal proof or empirical validation.")
