# Information-weighted stewardship: exact conditional optimality certificate

Justin Hart / Viridis. Review candidate, 2026-09-25/26.
**Evidence:** analytical proof below; independent numerical and symbolic checks
are separate. See CLAIMS.md for the exact compiled Lean subset. No physical
validation or scientific-priority claim.

## Model and units

Let α,K,φ,Ω,r>0. Quantify over already-admissible trajectories: D is locally
absolutely continuous on [0,∞), takes values in [0,K], H is measurable,
0≤H≤ΩD a.e., and D′=g(D)−φH a.e., where g(d)=αd(1−d/K).
Bounds or values of H on null sets do not affect the dynamics or objective.
This scope does not assume a theorem constructing every measurable feedback
solution. The constant witness below proves that the class is nonempty.

| Quantity | Units and meaning |
|---|---|
| D,K | units of source stock |
| α,r | inverse time |
| H | fresh attempted observations / time |
| φ | stock consumed / attempted observation |
| Ω | attempts / (stock × time), an operating capacity |
| q | predictive bits / attempt |
| L=qH | predictive bits / time |
| J=∫exp(−rt)L dt | discounted predictive bits |
| retained information | a separate memory quantity, unspecified here |
| physical erasures and energy | unspecified; neither inferred from '?' nor H |

Conditional on known stock d and prior history, X is a fresh fair independent
bit. A reveal flag R is Bernoulli(d/K) independent of X; O=X when R=1 and '?'
otherwise. Thus H₂(X|D=d,history)=1 and
H₂(X|O,D=d,history)=(1−d/K)·1+(d/K)·0. Their difference is d/K.
The uninformed true-label log loss is 1 bit; the posterior loss is 0 on reveal
and 1 on '?', yielding the same expected improvement. Each target is counted
once. For *random* D, the scalar conditional mutual information is E[D]/K;
d/K is the statewise value, not a random-valued conditional-MI scalar.

The deterministic rate model is a fluid idealization. A resource-consuming
point process is a different model. The channel law is stipulated, not measured.

## Feasibility and non-vacuity

Assume 0<r<2α and set s=K(2α−r)/(3α). Then 0<s<K. Since
1−s/K=(α+r)/(3α), h=g(s)/φ=s(α+r)/(3φ)>0.
Holding s is feasible exactly when Ω≥(α+r)/(3φ), and the duty is
u=h/(Ωs)=(α+r)/(3φΩ)∈(0,1]. The constant functions D=s,H=h satisfy
all admissibility conditions and the ODE, including at capacity equality.
For α=1/2,K=φ=Ω=1,r=1/10, s=3/5,h=3/25,u=1/5.

For context only, if one instead parameterizes by a prescribed measurable
u∈[0,1], the drift is Carathéodory and locally Lipschitz in D uniformly on
bounded sets. At D=0 it is zero; at K it is nonpositive. On [0,K],
D′≥−φΩD, so positive trajectories satisfy D(t)≥D(0)exp(−φΩt)
until any hypothetical first exit. The scalar comparison principle at both
barriers gives forward invariance and bounded global continuation. This is
an analytical existence/invariance argument, not part of the formalization
unless separately recorded in CLAIMS.md.

## Finite-horizon accounting from the physical ODE

Set W(d)=d²/(2K), q(d)=d/K, F(d)=q(d)g(d)−rW(d).
On every [0,T], D is AC; W is continuously differentiable with bounded derivative
on [0,K], so W∘D is AC and (W∘D)′=q(D)D′ a.e. The smooth multiplier
exp(−rt) preserves AC. Its product derivative is

    [exp(−rt)W(D(t))]′ = exp(−rt)[F(D(t))−φq(D(t))H(t)] a.e.

Every term is integrable on [0,T]: H is measurable and bounded a.e. by ΩK,
D is continuous and bounded, and exponential discount is bounded there.
The AC fundamental theorem of calculus therefore gives, with no assumed
accounting identity,

    J_T = W(D(0))/φ − exp(−rT)W(D(T))/φ
          + (1/φ)∫₀ᵀ exp(−rt)F(D(t))dt.

## Infinite horizon and global comparison

The objective integrand is measurable, nonnegative a.e., and bounded above
by ΩK exp(−rt), whose integral is ΩK/r. Hence J exists and is finite.
Furthermore 0≤g(d)≤αK/4 on [0,K], 0≤W(d)≤K/2, and
|F(d)|≤αK/4+rK/2. Thus exp(−rt)F(D(t)) is absolutely integrable.
The terminal term lies between 0 and (K/2)exp(−rT), which tends to zero.
Taking limits in the finite identity is justified by these explicit bounds.

Expansion and substitution of 3αs=K(2α−r) give

    F(s)−F(d) = α/(2K²) (d−s)²(2d+s).

For d≥0 this is nonnegative, zero exactly at d=s since s>0. The gap is
bounded on [0,K], so its discounted integral is absolutely integrable too.
For the held trajectory,

    J* = q(s)g(s)/(φr) = W(s)/φ+F(s)/(φr).

For every admissible policy with D(0)=s, subtraction of the actual objective
identities, using ∫₀∞exp(−rt)dt=1/r, proves

    J*−J = α/(2φK²) ∫₀∞exp(−rt)(D(t)−s)²(2D(t)+s)dt ≥ 0.

No stationary, accounting, regret or dominance hypothesis was added to the
admissible policy class. This is a global comparison, not a first-order test.

If equality holds, the continuous nonnegative discounted gap has integral zero.
If it were positive at any t≥0, continuity would make it bounded below by a
positive number on a subinterval of positive length (a right neighborhood at
zero), contradicting zero integral. Therefore D(t)=s everywhere. The ODE
then implies H=h a.e. Conversely, if H=h a.e. and D(0)=s, local ODE uniqueness
implies D=s: g is Lipschitz with constant α on [0,K], so
|D(t)−s|≤α∫₀ᵗ|D(v)−s|dv and Grönwall gives zero. This converse needs
uniqueness; it does not follow merely by substituting H=h into the ODE.
The controls are unique only modulo null sets.

For arbitrary D(0)=d₀, the proved upper bound is
J≤[W(d₀)+F(s)/r]/φ. Immediate attainment is not asserted unless d₀=s.
For finite T the difference between the *truncated* held objective and J_T is

    (1/φ)∫₀ᵀexp(−rt)[F(s)−F(D(t))]dt
    + exp(−rT)[W(D(T))−W(s)]/φ.

The boundary term can be negative. Full-rate sensing wins initially in the
normalized example; infinite-horizon optimality says otherwise only for the
full lifetime objective.

## Constant quality and boundary regimes

For q=1 use W₀(d)=d and F₀(d)=g(d)−rd. If 0<r<α,
s₀=K(α−r)/(2α), h₀=g(s₀)/φ=s₀(α+r)/(2φ), and holding is feasible
exactly when Ω≥(α+r)/(2φ). The same AC proof, integrability, and vanishing
terminal argument yield from D(0)=s₀

    J₀*−J = α/(φK)∫₀∞exp(−rt)(D(t)−s₀)²dt ≥ 0.

For r≥2α there is no positive information-weighted interior setpoint of the
claimed type; r=0 has no finite discounted-objective guarantee. Implementations
reject these inputs for that theorem. For φ=0, D is independent of H; q≥0 makes
H=ΩD dominate throttling pointwise. No positive-φ formula is evaluated at zero.
Insufficient Ω means an infeasible candidate, not an optimum.

For integer m≥0, W_m=d^(m+1)/((m+1)K^m) and
F_m′=(d/K)^m[(m+1)α−r−(m+2)αd/K]. Under 0<r<(m+1)α,
s_m=K((m+1)α−r)/((m+2)α) is the global maximizer on [0,K]; holding
requires Ω≥(α+r)/((m+2)φ). This extension is analytically derived and
numerically checked, not automatically inherited as a Lean theorem.
For measured q>0, g′+(q′/q)g=r only identifies stationary candidates.

## Forcing benchmark and a conservative analytical certificate

In the normalized instance, forced stock solves
D′=−(D+D²)/2 and is D(t)=0.6exp(−t/2)/[1+0.6(1−exp(−t/2))].
Direct differentiation verifies the ODE and initial condition. The denominator
is at least one, so D≤0.6exp(−t/2), D→0, and
J_force≤0.36∫exp(−1.1t)dt=0.36/1.1. Since the objective is strictly positive
near zero, 0<J_force≤0.36/1.1; thus J*/J_force≥2.2. The approximately
2.991 ratio is numerical, not the conservative analytic bound.

## Energy and literature limits

For an independently justified per-attempt cost ε_op>0 and stipulated available
power P_eff(d)=Pd/K, accounting gives Ω=P/(Kε_op). It establishes neither
ε_op=kBT ln 2 nor a universal learned-bit energy price.

Clark and Munro (1975), *The Economics of Fishing and Modern Capital Theory*,
pp. 94–95, use renewable-stock dynamics, stock-dependent unit returns, a possibly
stock-dependent harvest cap and discounted lifetime value. Those are inherited
control ideas, not scientific priority of this example. Mapping depletion to
φH and return per depletion to q/φ places this problem in that established class.
The present concrete contribution is the constructed fresh-bit channel and
explicit polynomial regret certificate. [Primary paper](https://www3.nd.edu/~lemmon/courses/bios60581/lectures/lect3/clark1975economics.pdf).

Still, Sivak, Bell and Crooks (2012), *The thermodynamics of prediction*, relate
nonpredictive retained information to dissipation for their driven physical
model. That does not establish a universal linear maintenance cost for arbitrary
mutual information or price each observation at a Landauer quantum.
[Primary paper](https://arxiv.org/html/1203.3271v3).
Novelty remains unresolved; no universal AI-alignment conclusion follows.
