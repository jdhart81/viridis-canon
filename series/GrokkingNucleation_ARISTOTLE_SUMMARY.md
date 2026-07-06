# Summary of changes for run d28f92a2-b4dd-4d95-be6a-d12d53b99d75
All five `sorry`s in `GrokkingNucleation.lean` are discharged; the file builds cleanly with 0 sorries.

Proved (statements preserved verbatim):
- `gnt_barrier_eq_cnt` — the CNT nucleation barrier equals both `σ·(u*)² − Δ·(u*)³` and `σ·(u*)²/3`, i.e. `(4/27)σ³/Δ²`. Proved by unfolding the definitions and `field_simp; ring`.
- `gnt_critical_point` — `u* = 2σ/(3Δ)` is a stationary point of `g(u)=σu²−Δu³` (`2σu* − 3Δu*² = 0`). `field_simp; ring`.
- `tau_grok_nonmonotone_unique_min` — for the Goldilocks temperature `T* = Td/(1+√(B/A))`: interiority `0 < T* < Td`, the stationarity first-order condition `−A/T*² + B/(Td−T*)² = 0` (via `Real.sq_sqrt` giving `√(B/A)² = B/A`), and strict convexity `E''(T)=2A/T³+2B/(Td−T)³ > 0` on `(0,Td)`.
- `nucleation_ib_floor` — `tauFloor = max(tK, c·Igen)` dominates both floors and is monotone non-decreasing in `Igen`.
- `gnt_nonvacuous` — explicit witness `σ=Δ=A=B=Td=c=1, tK=Igen=0` giving `barrier = 4/27 > 0` and `T* = 1/2 ∈ (0,1)`, confirming the results are non-vacuous.

Verification: axiom audit for every named theorem is exactly `{propext, Classical.choice, Quot.sound}`. No auxiliary definitions were strengthened or weakened; every conclusion is the original non-trivial one. The only remaining compiler messages are unused-hypothesis linter warnings on positivity hypotheses that are part of the required verbatim statements (`hσ` in `gnt_barrier_eq_cnt`, `htK`/`hI` in `nucleation_ib_floor`); these were kept intentionally to preserve the statements exactly as given.