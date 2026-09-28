import Mathlib

noncomputable section
namespace Viridis.Monitoring.PairedDetectorCoverage

def coverage (p q overlap : ℝ) : ℝ := p + q - overlap

theorem coverage_definition (p q overlap : ℝ) : coverage p q overlap = p + q - overlap := by
  sorry

theorem gain_over_first (p q overlap : ℝ) : coverage p q overlap - p = q - overlap := by
  sorry

theorem gain_over_second (p q overlap : ℝ) : coverage p q overlap - q = p - overlap := by
  sorry

theorem coverage_ge_first (p q overlap : ℝ) (h : overlap ≤ q) : p ≤ coverage p q overlap := by
  sorry

theorem coverage_ge_second (p q overlap : ℝ) (h : overlap ≤ p) : q ≤ coverage p q overlap := by
  sorry

theorem coverage_antitone_in_overlap (p q r1 r2 : ℝ) (h : r1 ≤ r2) : coverage p q r2 ≤ coverage p q r1 := by
  sorry

theorem paired_detector_witness : coverage (1/2 : ℝ) (3/4 : ℝ) (3/8 : ℝ) = 7/8 ∧ coverage (1/2 : ℝ) (3/4 : ℝ) (3/8 : ℝ) - 1/2 = 3/8 := by
  sorry

end Viridis.Monitoring.PairedDetectorCoverage
