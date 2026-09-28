import Mathlib

noncomputable section
namespace Viridis.Monitoring.PairedDetectorCoverage

def coverage (p q overlap : ℝ) : ℝ := p + q - overlap

theorem coverage_definition (p q overlap : ℝ) : coverage p q overlap = p + q - overlap := by
  rfl
theorem gain_over_first (p q overlap : ℝ) : coverage p q overlap - p = q - overlap := by
  unfold coverage
  ring
theorem gain_over_second (p q overlap : ℝ) : coverage p q overlap - q = p - overlap := by
  unfold coverage
  ring
theorem coverage_ge_first (p q overlap : ℝ) (h : overlap ≤ q) : p ≤ coverage p q overlap := by
  unfold coverage
  linarith
theorem coverage_ge_second (p q overlap : ℝ) (h : overlap ≤ p) : q ≤ coverage p q overlap := by
  unfold coverage
  linarith
theorem coverage_antitone_in_overlap (p q r1 r2 : ℝ) (h : r1 ≤ r2) : coverage p q r2 ≤ coverage p q r1 := by
  unfold coverage
  linarith
theorem paired_detector_witness : coverage (1/2 : ℝ) (3/4 : ℝ) (3/8 : ℝ) = 7/8 ∧ coverage (1/2 : ℝ) (3/4 : ℝ) (3/8 : ℝ) - 1/2 = 3/8 := by
  norm_num [coverage]

end Viridis.Monitoring.PairedDetectorCoverage
