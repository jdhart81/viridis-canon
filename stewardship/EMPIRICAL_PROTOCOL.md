# Falsifiable controlled-sensing protocol (no experimental results)

Start with a reversible laboratory sensing platform having a rechargeable
reserve, instrumented energy consumption, and independently generated hidden
targets. Do not disturb an ecosystem. Before collecting data, register the
apparatus, sampling clock, resource definition and instrument calibration,
exclusion rules, sample size/power calculation, analysis script, randomization
seed, confidence procedure, finite horizon T and terminal-stock valuation.
Do not select T after finding a crossover.

On independent calibration runs, estimate recovery g(D) with sensing off;
estimate damage per attempt at randomized rates and stock levels; measure
achievable H and overhead; estimate q(D) from held-out predictive log-score
improvement against a history-conditioned baseline. Split by complete run,
not observations within a run. Enforce unique target IDs, blind future labels,
record missingness and test whether it depends on the target. Do not impose a
linear q and then call its recovery an empirical discovery. Compare flexible
and logistic/linear fits, with predictive calibration uncertainty.

Freeze the controller and fitted functions before held-out runs. Randomize
matched initial-stock replicates between the frozen controller, full-rate,
and raw-throughput controller. Use identical source dynamics, constraints,
target process, information channels, discount, horizon and terminal rule.
Include every transient, failed attempt, dropped label and terminal reserve.
Report predictive bits, attempts, retained memory, physical resets and joules
separately, including setup, maintenance and computation. If cost enters the
objective, preregister its conversion and coefficient; it is a new objective.

Include zero-damage sensing, a constant-quality channel, and an available
substitute-source control. Report total and per-attempt energy, uncertainty in
φ and g, and missingness. Evaluate paired run-level objective differences with
prespecified confidence intervals and propagate calibration uncertainty by
run-level bootstrap or an explicitly specified measurement-error model.
Adjust any multiple primary comparisons; retain all seeds and failed intervals.

Reject or narrow the apparatus claim if independently measured recovery, damage,
quality, feasibility or held-out policy ordering fails the frozen prediction
within preregistered uncertainty limits. A short terminal-free experiment is
not an infinite-horizon test. No extrapolation to ecology, permanent memory,
general intelligence, or alignment is licensed by passing this protocol.


A concrete preregistration can use paired complete runs as the unit of analysis:
choose the smallest decision-relevant bit difference δ before calibration,
estimate the paired-run standard deviation σ from a separate pilot, and freeze
n=ceil((z_(1−α_test/2)+z_(1−β))² σ²/δ²), with α_test adjusted for the two
primary controller comparisons and power 1−β=0.8. Pilot runs never enter the
held-out test. Fix the apparatus's safe T and terminal-value rule before the
pilot; report a terminal-free outcome and any prespecified terminal-valued
outcome separately. Publish null/negative results and all run exclusions.
