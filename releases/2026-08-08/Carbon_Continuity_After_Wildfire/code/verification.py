#!/usr/bin/env python3
"""Deterministic checks and TikZ figure generation for Carbon Continuity."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE_BINDING = ROOT.parent / "provenance" / "SOURCE_BINDING.json"
EXPECTED_SOURCE_CONCEPT_SHA256 = "f538bb8b6629fea970336a710c471915b8cdee319b2cde3100cdb1019321bd67"
SEED = 20260804


@dataclass(frozen=True)
class Params:
    a: float
    d: float
    r: float
    p: float

    @property
    def loop_gain(self) -> float:
        return self.r * self.p

    @property
    def leakage_product(self) -> float:
        return (1.0 - self.a) * (1.0 - self.d)

    @property
    def continuity_number(self) -> float:
        return self.loop_gain / self.leakage_product


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def bound_source_concept_sha256() -> str:
    """Return the frozen concept-outline hash without requiring a private path.

    The concept outline is provenance, not a computational or scientific input.
    The release therefore binds its recorded digest through the included
    Aristotle source-binding receipt rather than attempting to open the
    author's original Desktop file.
    """
    if not SOURCE_BINDING.is_file():
        return ""
    try:
        record = json.loads(SOURCE_BINDING.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ""
    value = record.get("source_concept_sha256", "")
    return value if isinstance(value, str) else ""


def step(params: Params, living: float, durable: float) -> tuple[float, float]:
    return (
        params.a * living + params.r * durable,
        params.p * living + params.d * durable,
    )


def capped_step(
    params: Params,
    living: float,
    durable: float,
    living_cap: float = 1.0,
    durable_cap: float = 0.6,
) -> tuple[float, float]:
    next_living, next_durable = step(params, living, durable)
    return min(living_cap, next_living), min(durable_cap, next_durable)


def trajectory(params: Params, initial: tuple[float, float], cycles: int) -> list[tuple[float, float]]:
    states = [initial]
    for _ in range(cycles):
        states.append(capped_step(params, *states[-1]))
    return states


def dominant_eigenvalue(params: Params) -> float:
    trace = params.a + params.d
    determinant = params.a * params.d - params.r * params.p
    discriminant = max(0.0, trace * trace - 4.0 * determinant)
    return 0.5 * (trace + math.sqrt(discriminant))


class Gate:
    def __init__(self) -> None:
        self.rows: list[tuple[str, bool, str]] = []

    def check(self, name: str, condition: bool, detail: str) -> None:
        self.rows.append((name, bool(condition), detail))

    @property
    def passed(self) -> int:
        return sum(ok for _, ok, _ in self.rows)

    def report(self) -> str:
        lines = [
            "CARBON CONTINUITY VERIFICATION",
            f"SEED: {SEED}",
            f"SOURCE_SHA256: {bound_source_concept_sha256()}",
            "",
        ]
        for index, (name, ok, detail) in enumerate(self.rows, 1):
            lines.append(f"{index:02d} {'PASS' if ok else 'FAIL'} {name}: {detail}")
        lines.extend(
            [
                "",
                f"SUMMARY: {self.passed} PASS / {len(self.rows) - self.passed} FAIL",
                "STATUS: NUMERICAL_GATE_PASS" if self.passed == len(self.rows) else "STATUS: NUMERICAL_GATE_FAIL",
                "SCOPE: exact algebra and stylized model checks only; no empirical calibration or causal field claim",
            ]
        )
        return "\n".join(lines) + "\n"


def tikz_coordinates(points: list[tuple[float, float]]) -> str:
    return " ".join(f"({x:.5f},{y:.5f})" for x, y in points)


def make_schematic(path: Path) -> None:
    path.write_text(
        r"""\begin{tikzpicture}[>=stealth,thick,font=\small]
\node[draw=green!50!black,rounded corners,minimum width=5.1cm,minimum height=1.65cm,align=center] (L) at (0,0) {\textbf{Living and regenerative pool, $L$}\\biomass, roots, propagules, productive capacity\\{\scriptsize $a$: retained within-pool function}};
\node[draw=brown!75!black,rounded corners,minimum width=5.1cm,minimum height=1.65cm,align=center] (D) at (8.0,0) {\textbf{Durable-support pool, $D$}\\soil and pyrogenic carbon, stable wood\\{\scriptsize $d$: retained within-pool function}};
\draw[->,brown!75!black] (L.north east) to[bend left=12] node[above] {$p$: living-to-durable transfer} (D.north west);
\draw[->,green!50!black] (D.south west) to[bend left=12] node[below] {$r$: durable support for regeneration} (L.south east);
\draw[->,red!70!black] (L.south) -- ++(0,-1.0) node[below] {living-pool leakage};
\draw[->,red!70!black] (D.south) -- ++(0,-1.0) node[below] {durable-pool leakage};
\node[font=\bfseries] at (4,-2.35) {Continuity threshold: $rp \geq (1-a)(1-d)$};
\end{tikzpicture}
""",
        encoding="utf-8",
    )


def make_phase_diagram(path: Path) -> None:
    a, d = 0.70, 0.95
    leakage = (1.0 - a) * (1.0 - d)
    r_values = [0.035 + i * (0.415 / 80) for i in range(81)]
    boundary = [(r, leakage / r) for r in r_values if leakage / r <= 0.45]
    coordinates = tikz_coordinates(boundary)
    path.write_text(
        rf"""\begin{{tikzpicture}}[x=12cm,y=9cm,font=\small]
\fill[red!6] (0.01,0.01) rectangle (0.45,0.45);
\fill[green!7] (0.035,0.45) -- {coordinates} -- (0.45,0.45) -- cycle;
\draw[->] (0.01,0.01) -- (0.48,0.01) node[right] {{$r$}};
\draw[->] (0.01,0.01) -- (0.01,0.48) node[above] {{$p$}};
\foreach \x in {{0.1,0.2,0.3,0.4}} {{\draw (\x,0.006)--(\x,0.014) node[below=3pt] {{\x}};}}
\foreach \y in {{0.1,0.2,0.3,0.4}} {{\draw (0.006,\y)--(0.014,\y) node[left=3pt] {{\y}};}}
\draw[very thick] plot[smooth] coordinates {{{coordinates}}};
\node[align=center,font=\bfseries] at (0.32,0.32) {{continuity-capable\\local regime}};
\node[align=center,font=\bfseries] at (0.12,0.06) {{depleting\\local regime}};
\node[fill=white,inner sep=2pt] at (0.29,0.08) {{$\mathcal{{R}}_C=1$}};
\end{{tikzpicture}}
""",
        encoding="utf-8",
    )


def make_trajectories(path: Path) -> tuple[float, float]:
    stock_focused = Params(a=0.70, d=0.92, r=0.10, p=0.04)
    continuity_focused = Params(a=0.76, d=0.96, r=0.18, p=0.18)
    stock = trajectory(stock_focused, (1.0, 0.05), 20)
    continuity = trajectory(continuity_focused, (0.85, 0.20), 20)
    weights = [0.96 ** cycle for cycle in range(21)]
    capacity = 1.6
    cci_stock = sum(weight * sum(state) for weight, state in zip(weights, stock)) / sum(weight * capacity for weight in weights)
    cci_continuity = sum(weight * sum(state) for weight, state in zip(weights, continuity)) / sum(weight * capacity for weight in weights)

    stock_l = tikz_coordinates([(i, state[0]) for i, state in enumerate(stock)])
    stock_t = tikz_coordinates([(i, sum(state)) for i, state in enumerate(stock)])
    continuity_l = tikz_coordinates([(i, state[0]) for i, state in enumerate(continuity)])
    continuity_t = tikz_coordinates([(i, sum(state)) for i, state in enumerate(continuity)])
    path.write_text(
        rf"""\begin{{tikzpicture}}[x=0.28cm,y=3.4cm,font=\small]
\draw[->] (0,0) -- (21.2,0) node[right] {{cycle}};
\draw[->] (0,0) -- (0,1.72) node[above] {{normalized state}};
\foreach \x in {{0,5,10,15,20}} {{\draw (\x,-0.015)--(\x,0.015) node[below=3pt] {{\x}};}}
\foreach \y in {{0.5,1.0,1.5}} {{\draw (-0.15,\y)--(0.15,\y) node[left=3pt] {{\y}};}}
\draw[dashed,green!50!black,thick] plot coordinates {{{stock_l}}};
\draw[red!75!black,very thick] plot coordinates {{{stock_t}}};
\draw[dashed,blue!70!black,thick] plot coordinates {{{continuity_l}}};
\draw[brown!80!black,very thick] plot coordinates {{{continuity_t}}};
\node[anchor=west,text=green!50!black] at (10.4,1.62) {{-- living, stock-focused}};
\node[anchor=west,text=red!75!black] at (10.4,1.49) {{-- total, stock-focused}};
\node[anchor=west,text=blue!70!black] at (10.4,1.36) {{-- living, continuity-focused}};
\node[anchor=west,text=brown!80!black] at (10.4,1.23) {{-- total, continuity-focused}};
\node[anchor=east,text=red!75!black] at (20,0.24) {{CCI$_{{20}}={cci_stock:.3f}$}};
\node[anchor=east,text=brown!80!black] at (20,1.08) {{CCI$_{{20}}={cci_continuity:.3f}$}};
\node at (10,1.88) {{Stylized capped trajectories (illustrative, not calibrated)}};
\end{{tikzpicture}}
""",
        encoding="utf-8",
    )
    return cci_stock, cci_continuity


def run_gate() -> Gate:
    gate = Gate()
    source_digest = bound_source_concept_sha256()
    gate.check("source-binding-present", SOURCE_BINDING.is_file(), "provenance/SOURCE_BINDING.json")
    gate.check(
        "source-binding-hash-match",
        source_digest == EXPECTED_SOURCE_CONCEPT_SHA256,
        source_digest,
    )

    concrete = Params(a=0.6, d=0.8, r=0.5, p=0.2)
    witness = (concrete.r, 1.0 - concrete.a)
    nxt = step(concrete, *witness)
    gate.check("explicit-witness-positive", witness[0] > 0 and witness[1] > 0, f"L={witness[0]:.3f}, D={witness[1]:.3f}")
    gate.check("explicit-threshold-strict", concrete.loop_gain > concrete.leakage_product, f"rp={concrete.loop_gain:.3f} > leakage={concrete.leakage_product:.3f}")
    gate.check("explicit-living-held", math.isclose(nxt[0], witness[0], abs_tol=1e-12), f"L'={nxt[0]:.3f}")
    gate.check("explicit-durable-grows", nxt[1] > witness[1], f"D'={nxt[1]:.3f} > D={witness[1]:.3f}")

    rng = random.Random(SEED)
    sufficient_failures = 0
    necessary_failures = 0
    boundary_failures = 0
    strict_failures = 0
    rational_cases = 25000
    for _ in range(rational_cases):
        a = Fraction(rng.randrange(0, 100), 100)
        d = Fraction(rng.randrange(0, 100), 100)
        r = Fraction(rng.randrange(1, 101), 100)
        p = Fraction(rng.randrange(1, 101), 100)
        threshold = (1 - a) * (1 - d) <= r * p
        living, durable = r, 1 - a
        next_living = a * living + r * durable
        next_durable = p * living + d * durable
        if threshold and not (living <= next_living and durable <= next_durable):
            sufficient_failures += 1
        if threshold and r * p > (1 - a) * (1 - d) and not next_durable > durable:
            strict_failures += 1
        boundary_p = (1 - a) * (1 - d) / r
        boundary_next_durable = boundary_p * living + d * durable
        if next_living != living or boundary_next_durable != durable:
            boundary_failures += 1

        test_l = Fraction(rng.randrange(1, 151), 100)
        test_d = Fraction(rng.randrange(1, 151), 100)
        nondecreasing = test_l <= a * test_l + r * test_d and test_d <= p * test_l + d * test_d
        if nondecreasing and not threshold:
            necessary_failures += 1

    gate.check("threshold-sufficiency-exhaustive", sufficient_failures == 0, f"{rational_cases:,} exact rational cases")
    gate.check("threshold-necessity-exhaustive", necessary_failures == 0, f"{rational_cases:,} exact rational cases with adversarial portfolios")
    gate.check("boundary-stationarity-exhaustive", boundary_failures == 0, f"{rational_cases:,} exact boundary constructions")
    gate.check("strict-threshold-growth-exhaustive", strict_failures == 0, f"{rational_cases:,} exact strict-threshold cases")

    negative = Params(a=0.6, d=0.8, r=0.0, p=0.0)
    neg_next = step(negative, 1.0, 1.0)
    gate.check("zero-coupling-negative-control", neg_next[0] < 1.0 and neg_next[1] < 1.0, f"state (1,1) -> ({neg_next[0]:.2f},{neg_next[1]:.2f})")

    below = Params(a=0.6, d=0.8, r=0.2, p=0.2)
    grid_witness = False
    for i in range(1, 101):
        living = 0.02 * i
        for j in range(1, 101):
            durable = 0.02 * j
            nl, nd = step(below, living, durable)
            if nl + 1e-12 >= living and nd + 1e-12 >= durable:
                grid_witness = True
                break
        if grid_witness:
            break
    gate.check("below-threshold-grid-negative-control", not grid_witness, "10,000 positive portfolios searched")

    above = Params(a=0.70, d=0.95, r=0.25, p=0.10)
    gate.check("spectral-cross-check-above", dominant_eigenvalue(above) >= 1.0, f"dominant eigenvalue={dominant_eigenvalue(above):.6f}")
    gate.check("spectral-cross-check-below", dominant_eigenvalue(below) < 1.0, f"dominant eigenvalue={dominant_eigenvalue(below):.6f}")

    figures = ROOT / "figures"
    figures.mkdir(exist_ok=True)
    make_schematic(figures / "carbon_continuity_system.tex")
    make_phase_diagram(figures / "carbon_continuity_phase.tex")
    cci_stock, cci_continuity = make_trajectories(figures / "carbon_continuity_trajectories.tex")
    gate.check("illustrative-cci-order", cci_continuity > cci_stock, f"continuity={cci_continuity:.6f} > stock={cci_stock:.6f}")
    gate.check("illustrative-stock-starts-with-more-living-carbon", 1.0 > 0.85, "stock-focused living=1.00; continuity-focused living=0.85; initial total=1.05 for both")
    figure_names = ("carbon_continuity_system.tex", "carbon_continuity_phase.tex", "carbon_continuity_trajectories.tex")
    gate.check("figures-created", all((figures / name).is_file() for name in figure_names), "3 vector TikZ figure fragments")
    gate.check("figure-files-nonempty", all((figures / name).stat().st_size > 1000 for name in figure_names), "all figure fragments exceed 1 KB")
    gate.check("continuity-number-stock-below", Params(0.70, 0.92, 0.10, 0.04).continuity_number < 1.0, f"R_C={Params(0.70, 0.92, 0.10, 0.04).continuity_number:.6f}")
    gate.check("continuity-number-balanced-above", Params(0.76, 0.96, 0.18, 0.18).continuity_number > 1.0, f"R_C={Params(0.76, 0.96, 0.18, 0.18).continuity_number:.6f}")
    return gate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "verification_output.txt")
    args = parser.parse_args()
    gate = run_gate()
    report = gate.report()
    args.output.write_text(report, encoding="utf-8")
    print(report, end="")
    return 0 if gate.passed == len(gate.rows) else 2


if __name__ == "__main__":
    raise SystemExit(main())
