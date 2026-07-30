/-
  DualCorridor — the machine-verified combinatorial core of "Trees Cannot Cut".

  Companion proof artifact for:
    Hart, J. (2026). "Trees Cannot Cut: Circuit Rank as the Design Variable Reconciling
    Habitat Connectivity and Fuel Discontinuity in Managed Forest Landscapes."
    Viridis LLC, Columbia Falls, Montana.  Correspondence: Justin@viridisconservation.com
    ORCID: 0009-0008-3082-2482

  DOI: 10.5281/zenodo.21686446 (concept DOI, resolves to latest; v1.0.1 = 10.5281/zenodo.21708530)
  Toolchain: leanprover/lean4:v4.28.0 · Mathlib rev 8f9d9cff
  Verified with Aristotle (Harmonic), run 3 of 3, 2026-07-29.
  Co-authored-by: Aristotle (Harmonic) <aristotle-harmonic@harmonic.fun>

  ## Status — read this before citing.

  Every named result in this file has a clean axiom audit:

      #print axioms  ⟹  [propext, Classical.choice, Quot.sound]

  Zero `sorry`. Zero `sorryAx`. Twenty-one named results, including the inhabitation
  witness. The audit log is shipped alongside this file as `axiom_audit.log`; it is
  reproduced by building this file and running `#print axioms` on each name.

  ## What is proved, and what is assumed

  The paper's results are stated topologically: for a corridor `C` embedded in a landscape
  `Ω`, the number of connected components of the fuel matrix `Ω \ C` equals
  `rank H₁(C ∪ ∂Ω)`, via Alexander duality.

  Mathlib has neither Alexander duality nor a planar Euler formula in usable form, so the
  argument is split at its natural seam:

  * The **topological bridge** — "compartment count = circuit rank + 1" — is carried as an
    explicit hypothesis, the `FaceCount` structure below. It is NOT proved here. Its
    justification is Alexander duality, given in the manuscript §2.2–2.3.
  * Everything **downstream** of that bridge is finite graph theory, and every line of it
    is proved here.

  ## Non-vacuity

  A conditional theorem is worthless if its hypothesis is unsatisfiable. `FaceCount` is
  therefore exhibited as inhabited: `FaceCount.ofCircuitRank` is a concrete, axiom-clean
  witness. Nothing below is vacuously true.

  **Scope note, stated plainly.** That witness is the tautological model — it *defines*
  `faces G := (circuitRank G + 1).toNat`. It establishes that the interface is consistent
  and that the downstream theorems have content. It does NOT establish that the
  *geometric* compartment count of `Ω \ C` satisfies the duality relation. That remains
  Alexander duality, assumed. Readers should not read `ofCircuitRank` as a proof of the
  topological step.

  ## The results

  * `numComponents_delete_bridge`          — the keystone: deleting a bridge adds one component
  * `circuitRank_delete_bridge`            — bridges do not change circuit rank
  * `circuitRank_delete_nonBridge`         — non-bridges drop it by exactly one
  * `circuitRank_eq_zero_iff_isAcyclic`    — μ = 0 ⟺ acyclic
  * `circuitRank_nonneg`                   — μ ≥ 0
  * `FaceCount.ofCircuitRank`              — inhabitation witness (non-vacuity gate)
  * `zeroCut`                              — **Proposition 1**: an acyclic corridor leaves one compartment
  * `faces_eq_circuitRank_add_one`         — Proposition 2: compartments = μ + 1
  * `bridge_no_merge`                      — Proposition 4(i): bridges have zero cut capacity
  * `nonBridge_merges_exactly_one`         — Proposition 4(ii)
  * `disjoint_support`                     — Proposition 4(iii): the two supports are disjoint
  * `boundaryAnchor_faces`                 — Proposition 5: b anchors give exactly b compartments
  * `first_anchor_buys_nothing`            — the §2.6 off-by-one: the FIRST anchor buys nothing

  ## Provenance

  Three Aristotle runs. Runs 1 and 2 failed to close the keystone
  (`numComponents_delete_bridge`); run 2's failure traced to a skeleton that derived the
  keystone *from* its own arithmetic consequence. Run 3 inverted that dependency — the
  component count posed as the primitive, the circuit-rank identity as the consequence —
  and closed it. Run 3 left exactly one `sorry`, at `circuitRank_eq_zero_iff_isAcyclic`;
  that was closed by hand from run-3 lemmas (see `circuitRank_eq_zero_of_isAcyclic`).

  A refutation of anything here is more valuable to us than another proof.
  Send counterexamples to Justin@viridisconservation.com.
-/

import Mathlib

open Finset

namespace DualCorridor

variable {V : Type*} [Fintype V] [DecidableEq V]

/-! ## Circuit rank -/

/-- Number of connected components of a finite simple graph. -/
noncomputable def numComponents (G : SimpleGraph V) [DecidableRel G.Adj] : ℕ :=
  Fintype.card G.ConnectedComponent

/-- The circuit rank (cyclomatic number, first Betti number) `μ = |E| - |V| + c`.

    Stated over `ℤ` deliberately: truncated ℕ-subtraction would silently hide exactly the
    off-by-one errors this file exists to rule out. -/
noncomputable def circuitRank (G : SimpleGraph V) [DecidableRel G.Adj] : ℤ :=
  (G.edgeFinset.card : ℤ) - (Fintype.card V : ℤ) + (numComponents G : ℤ)

/-- The supports of the connected components partition the finite vertex set. -/
lemma sum_component_vertex_cards (G : SimpleGraph V) [DecidableRel G.Adj] :
    ∑ c : G.ConnectedComponent, Fintype.card c.supp = Fintype.card V := by
  have h_disj : Pairwise fun c d : G.ConnectedComponent => Disjoint c.supp d.supp := by
    intro c d hcd
    rw [Set.disjoint_iff]
    intro v ⟨hvc, hvd⟩
    exact hcd (hvc.symm.trans hvd)
  have h_union : ⋃ c : G.ConnectedComponent, c.supp = Set.univ := by
    ext v
    simp [SimpleGraph.ConnectedComponent.supp]
  -- Convert to Finset
  have h_finset_sum : ∑ c : G.ConnectedComponent, Fintype.card ↑c.supp =
      ∑ c ∈ Finset.univ, ((c : G.ConnectedComponent).supp.toFinset).card := by
    congr 1 with c : 1
    simp [Fintype.card_coe]
  rw [h_finset_sum]
  -- Use biUnion
  rw [← Finset.card_biUnion]
  · congr 1
    ext v
    simp [Set.mem_iUnion, Set.mem_toFinset]
  · exact fun c _ d _ hcd => Set.disjoint_toFinset.mpr (h_disj hcd)


/-- Deleting an edge that is present drops the edge count by exactly one. -/
lemma edgeFinset_card_delete_of_mem
    (G : SimpleGraph V) [DecidableRel G.Adj] {e : Sym2 V} (he : e ∈ G.edgeFinset)
    [DecidableRel (G.deleteEdges {e}).Adj] :
    (G.deleteEdges {e}).edgeFinset.card = G.edgeFinset.card - 1 := by
  have h2 : (G.deleteEdges {e}).edgeFinset = G.edgeFinset \ {e} := by
    ext x
    simp [SimpleGraph.mem_edgeFinset, SimpleGraph.deleteEdges, Finset.mem_sdiff]
  rw [h2, Finset.card_sdiff]
  simp [he]

/-- **THE KEYSTONE.** Deleting a bridge increases the number of connected components by
    exactly one.

    Proved directly from the bridge characterisation: `e = s(u,v)` is a bridge, so `u` and
    `v` are unreachable in `G' := G.deleteEdges {e}`. The inclusion `G' ≤ G` induces a
    surjection on connected components which is injective except over the `G`-component
    containing `u`, which is exactly the union of the two distinct `G'`-components of `u`
    and `v`. Hence `|CC(G')| = |CC(G)| + 1`.

    Two earlier prover runs failed on this lemma because the skeleton derived it *from*
    `circuitRank_delete_bridge`, which is its arithmetic consequence. The component count
    is the primitive. -/
theorem numComponents_delete_bridge
    (G : SimpleGraph V) [DecidableRel G.Adj] {e : Sym2 V}
    (he : e ∈ G.edgeFinset) (hb : G.IsBridge e)
    [DecidableRel (G.deleteEdges {e}).Adj] :
    numComponents (G.deleteEdges {e}) = numComponents G + 1 := by
  -- Get the endpoints of the bridge edge
  have hmem : e ∈ G.edgeSet := SimpleGraph.mem_edgeFinset.mp he
  -- IsBridge means: edge is in G and endpoints are not reachable after deletion
  have hnotreach : ∀ u v, e = Sym2.mk (u, v) → ¬ (G.deleteEdges {e}).Reachable u v := by
    intro u v hev
    have := hb
    unfold SimpleGraph.IsBridge at this
    simp_all [SimpleGraph.deleteEdges]
  -- Extract endpoints
  obtain ⟨u, v, heq⟩ : ∃ u v, e = Sym2.mk (u, v) := by
    have ⟨p, hp⟩ := Quot.exists_rep e
    use p.1, p.2
    simp [hp]
  have headj : G.Adj u v := by simp_all [SimpleGraph.mem_edgeSet]
  have hnotreach' : ¬ (G.deleteEdges {e}).Reachable u v := hnotreach u v heq
  -- Every edge of deleteEdges is an edge of G
  have hsub : G.deleteEdges {e} ≤ G := SimpleGraph.deleteEdges_le {e}
  -- Reachability in deleteEdges implies reachability in G
  have hreach_mono : ∀ a b, (G.deleteEdges {e}).Reachable a b → G.Reachable a b := by
    intro a b ⟨w⟩
    let f : SimpleGraph.Hom (G.deleteEdges {e}) G := {
      toFun := id
      map_rel' := fun hab => hsub hab
    }
    exact ⟨w.map f⟩
  -- Surjection: each G-component has a preimage
  have hsurj : Function.Surjective (fun c : (G.deleteEdges {e}).ConnectedComponent =>
    Quot.lift (fun a => Quot.mk G.Reachable a) (by
      intro a b hab
      exact Quot.sound (hreach_mono a b hab)) c) := by
    intro cG
    exact Quot.inductionOn cG fun a => ⟨Quot.mk (G.deleteEdges {e}).Reachable a, rfl⟩
  -- u and v are reachable in G (via the edge e)
  have hreach_G : G.Reachable u v := ⟨SimpleGraph.Walk.cons headj .nil⟩
  -- Define the map from deleteEdges components to G components
  let f : (G.deleteEdges {e}).ConnectedComponent → G.ConnectedComponent :=
    Quot.lift (fun a => Quot.mk G.Reachable a) (by
      intro a b hab
      exact Quot.sound (hreach_mono a b hab))
  -- u's component in deleteEdges
  let Cu : (G.deleteEdges {e}).ConnectedComponent := Quot.mk (G.deleteEdges {e}).Reachable u
  -- v's component in deleteEdges  
  let Cv : (G.deleteEdges {e}).ConnectedComponent := Quot.mk (G.deleteEdges {e}).Reachable v
  -- In deleteEdges, u and v are not reachable, so Cu ≠ Cv
  have hCuNeCv : Cu ≠ Cv := by
    intro h
    have hq := h
    have hq2 := SimpleGraph.ConnectedComponent.exact hq
    exact hnotreach' hq2
  -- Both Cu and Cv map to the same G-component (the one containing u and v)
  have hfCu : f Cu = Quot.mk G.Reachable u := rfl
  have hfCv : f Cv = Quot.mk G.Reachable v := rfl
  have hfCu_eq_Cv : f Cu = f Cv := by rw [hfCu, hfCv]; exact Quot.sound hreach_G
  -- The component in G containing u and v
  let CuvG : G.ConnectedComponent := Quot.mk G.Reachable u
  -- Key lemma: if w is reachable from u in G, then w is reachable from u or v in G\e
  have hreach_split : ∀ w : V, G.Reachable w u → (G.deleteEdges {e}).Reachable w u ∨ (G.deleteEdges {e}).Reachable w v := by
    intro w hp
    obtain ⟨p⟩ := hp
    -- Case split: does p use edge e?
    by_cases he : e ∈ p.edges
    · -- p uses e. Find the first occurrence.
      -- Now prove the main statement by induction
      have h : ∀ {a b} (q : G.Walk a b), e ∈ q.edges → (G.deleteEdges {e}).Reachable a u ∨ (G.deleteEdges {e}).Reachable a v := by
        intro a b q heq'
        induction q with
        | nil => simp at heq'
        | @cons x y z hx qb ih =>
          simp [SimpleGraph.Walk.edges_cons] at heq'
          by_cases heqxy : e = s(x, y)
          · -- e = s(x, y)
            have : s(x, y) = s(u, v) := heqxy.symm.trans heq
            rcases Sym2.eq_iff.mp this with ⟨hxm, hym⟩ | ⟨hxp, hym⟩
            · -- x = u, y = v: x = u, so u reaches u trivially
              rw [hxm]
              left
              exact (SimpleGraph.Walk.nil : (G.deleteEdges {e}).Walk u u).reachable
            · -- x = v, y = u: x = v, so v reaches v trivially
              rw [hxp]
              right
              exact (SimpleGraph.Walk.nil : (G.deleteEdges {e}).Walk v v).reachable
          · -- e ≠ s(x, y) and e ∈ qb.edges: y reaches u or v by IH, and x = y without e
            have hx' : (G.deleteEdges {e}).Adj x y := by
              unfold SimpleGraph.deleteEdges
              exact ⟨hx, fun h => heqxy (by simp [SimpleGraph.fromEdgeSet] at h; exact h.1.symm)⟩
            rcases heq' with heq'' | heq''
            · exact absurd heq'' heqxy
            · rcases ih heq'' with h1 | h2
              · left; obtain ⟨w1⟩ := h1; exact (SimpleGraph.Walk.cons hx' w1).reachable
              · right; obtain ⟨w2⟩ := h2; exact (SimpleGraph.Walk.cons hx' w2).reachable
      exact h p he
    · -- p doesn't use e
      left
      -- Convert walk p to walk in G.deleteEdges {e}
      let conv : ∀ {a b}, (p : G.Walk a b) → e ∉ p.edges → (G.deleteEdges {e}).Walk a b
      · intro a b p hp
        induction p with
        | nil => exact SimpleGraph.Walk.nil
        | @cons x y z ha pb ih =>
          have hp_pb : e ∉ pb.edges := by
            intro heq
            apply hp
            simp [SimpleGraph.Walk.edges_cons, heq]
          have ha' : (G.deleteEdges {e}).Adj x y := by
            rw [SimpleGraph.deleteEdges]
            refine ⟨ha, fun h => ?_⟩
            simp [SimpleGraph.fromEdgeSet] at h
            exact hp (by rw [SimpleGraph.Walk.edges_cons]; simp [h])
          exact SimpleGraph.Walk.cons ha' (ih hp_pb)
      exact (conv p he).reachable
  -- f on quotients
  have hf_mk : ∀ a : V, f (Quot.mk (G.deleteEdges {e}).Reachable a) = Quot.mk G.Reachable a := by
    intro a; rfl
  -- Preimage characterization: f x = CuvG ↔ x = Cu ∨ x = Cv
  have hfiber_CuvG : ∀ x : (G.deleteEdges {e}).ConnectedComponent,
      f x = CuvG ↔ x = Cu ∨ x = Cv := by
    intro x
    obtain ⟨a, ha⟩ := Quot.exists_rep x
    have hfx_eq : f x = Quot.mk G.Reachable a := by
      have := hf_mk a
      simp only [ha] at this
      exact this
    constructor
    · intro hfx
      -- f x = CuvG means a is reachable from u in G
      have hauh_G : G.Reachable a u := by
        rw [hfx_eq] at hfx
        have hfx' : (Quot.mk G.Reachable a : G.ConnectedComponent) = Quot.mk G.Reachable u := by
          simp only [CuvG] at hfx; exact hfx
        exact SimpleGraph.ConnectedComponent.exact hfx'
      -- By hreach_split, a reaches u or v in G\e
      rcases hreach_split a hauh_G with hau | hav
      · left
        have := Quot.sound hau
        simp only [ha] at this
        exact this
      · right
        have := Quot.sound hav
        simp only [ha] at this
        exact this
    · intro hx
      rcases hx with rfl | rfl
      · rfl
      · rw [hfCv]; exact Quot.sound hreach_G.symm
  -- f is injective on the complement of {Cv}
  have hinj_excl_Cv : ∀ x y : (G.deleteEdges {e}).ConnectedComponent,
      x ≠ Cv → y ≠ Cv → f x = f y → x = y := by
    intro x y hx_ne_Cv hy_ne_Cv hfy_eq
    by_cases h : f x = CuvG
    · -- f x = CuvG, so x = Cu (since x ≠ Cv)
      have hx_eq_Cu : x = Cu := by
        rcases (hfiber_CuvG x).mp h with rfl | rfl
        · rfl
        · exact absurd rfl hx_ne_Cv
      have hy_eq_Cu : y = Cu := by
        have : f y = CuvG := hfy_eq.symm.trans h
        rcases (hfiber_CuvG y).mp this with rfl | rfl
        · rfl
        · exact absurd rfl hy_ne_Cv
      rw [hx_eq_Cu, hy_eq_Cu]
    · -- f x ≠ CuvG, so neither is f y
      have hy_ne_CuvG : f y ≠ CuvG := hfy_eq.symm ▸ h
      -- Both x and y are not Cu or Cv
      have hx_ne_Cu : x ≠ Cu := by
        intro hx_eq_Cu
        exact h (hx_eq_Cu ▸ rfl)
      have hy_ne_Cu : y ≠ Cu := by
        intro hy_eq_Cu
        exact hy_ne_CuvG (hy_eq_Cu ▸ rfl)
      -- Use hreach_split: f x = f y means they map to same G-component
      -- That component is not CuvG, so any vertex in x or y is NOT reachable from u in G
      -- Wait, that's wrong. Let me reconsider.
      -- f x is some component C' ≠ CuvG. x contains some vertex a.
      -- If a were reachable from u in G, then f x would be CuvG.
      -- Since f x ≠ CuvG, a is not reachable from u in G.
      -- Similarly for y.
      -- But then how do we know x = y from f x = f y?
      -- We need: if a and b are in the same G-component C' ≠ CuvG,
      -- and neither is reachable from u in G, then a and b are in the same G\e-component.
      -- This follows because if a reaches b in G, then b reaches a in G.
      -- If b reaches u, contradiction. So b doesn't reach u.
      -- Since a reaches b and b doesn't reach u, a doesn't reach u.
      -- Now, a reaches b in G. Does a reach b in G\e?
      -- If the path from a to b uses e, then it goes through u and v.
      -- But then a reaches u, contradiction.
      -- So the path doesn't use e, so a reaches b in G\e.
      obtain ⟨a, ha⟩ := Quot.exists_rep x
      obtain ⟨b, hb⟩ := Quot.exists_rep y
      have hab_G : G.Reachable a b := by
        have h1 : f x = Quot.mk G.Reachable a := by
          have := hf_mk a
          simp only [ha] at this
          exact this
        have h2 : f y = Quot.mk G.Reachable b := by
          have := hf_mk b
          simp only [hb] at this
          exact this
        rw [h1, h2] at hfy_eq
        exact SimpleGraph.ConnectedComponent.exact hfy_eq
      -- a is not reachable from u in G
      have ha_not_reach_u : ¬G.Reachable a u := by
        intro hau
        apply h
        rw [← ha]
        exact Quot.sound hau
      -- b is not reachable from u in G
      have hb_not_reach_u : ¬G.Reachable b u := by
        intro hbu
        apply hy_ne_CuvG
        rw [← hb]
        exact Quot.sound hbu
      -- a reaches b in G, and neither reaches u, so the path from a to b doesn't use e
      have hab_Ge : (G.deleteEdges {e}).Reachable a b := by
        obtain ⟨p⟩ := hab_G
        -- Inner lemma: if a walk uses e, then its start reaches u or v in G\e
        have walk_uses_e_implies_reach : ∀ {a' b'} (q : G.Walk a' b'), e ∈ q.edges →
            (G.deleteEdges {e}).Reachable a' u ∨ (G.deleteEdges {e}).Reachable a' v := by
          intro a' b' q heq'
          induction q with
          | nil => simp at heq'
          | @cons x y z hx qb ih =>
            simp [SimpleGraph.Walk.edges_cons] at heq'
            by_cases heqxy : e = s(x, y)
            · -- e = s(x, y)
              have : s(x, y) = s(u, v) := heqxy.symm.trans heq
              rcases Sym2.eq_iff.mp this with ⟨hxm, hym⟩ | ⟨hxp, hym⟩
              · rw [hxm]; left; exact (SimpleGraph.Walk.nil : (G.deleteEdges {e}).Walk u u).reachable
              · rw [hxp]; right; exact (SimpleGraph.Walk.nil : (G.deleteEdges {e}).Walk v v).reachable
            · -- e ≠ s(x, y) and e ∈ qb.edges
              have hx' : (G.deleteEdges {e}).Adj x y := by
                unfold SimpleGraph.deleteEdges
                exact ⟨hx, fun h => heqxy (by simp [SimpleGraph.fromEdgeSet] at h; exact h.1.symm)⟩
              rcases heq' with heq'' | heq''
              · contradiction
              · rcases ih heq'' with h1 | h2
                · left; obtain ⟨w1⟩ := h1; exact (SimpleGraph.Walk.cons hx' w1).reachable
                · right; obtain ⟨w2⟩ := h2; exact (SimpleGraph.Walk.cons hx' w2).reachable
        -- If p uses e, then a reaches u in G (since p passes through u)
        have walk_uses_e_implies_reach_u : ∀ {a' b'} (q : G.Walk a' b'), e ∈ q.edges → G.Reachable a' u := by
          intro a' b' q heq'
          induction q with
          | nil => simp at heq'
          | @cons x y z hx qb ih =>
            simp [SimpleGraph.Walk.edges_cons] at heq'
            by_cases heqxy : e = s(x, y)
            · -- e = s(x, y) = s(u, v)
              have hsym : s(x, y) = s(u, v) := heqxy.symm.trans heq
              rcases Sym2.eq_iff.mp hsym with ⟨hxm, hym⟩ | ⟨hxp, hym⟩
              · -- x = u, y = v: a' reaches x = u
                subst hxm; rfl
              · -- x = v, y = u: a' reaches y = u via x
                have hyu : y = u := hym
                subst hyu
                exact ⟨SimpleGraph.Walk.cons hx SimpleGraph.Walk.nil⟩
            · -- e ≠ s(x, y) and e ∈ qb.edges
              rcases heq' with heq'' | heq''
              · exact absurd heq'' heqxy
              · exact hx.reachable.trans (ih heq'')
        -- If p uses e, then a reaches u in G, contradicting ha_not_reach_u
        have hno_e : e ∉ p.edges := by
          intro he_in_p
          exact ha_not_reach_u (walk_uses_e_implies_reach_u p he_in_p)
        -- Now convert p to a walk in G\e
        let conv : ∀ {a' b'}, (q : G.Walk a' b') → e ∉ q.edges → (G.deleteEdges {e}).Walk a' b' := by
          intro a' b' q hq
          induction q with
          | nil => exact SimpleGraph.Walk.nil
          | @cons x y z ha qb ih =>
            have hq_qb : e ∉ qb.edges := by
              intro heq
              apply hq
              simp [SimpleGraph.Walk.edges_cons, heq]
            have ha' : (G.deleteEdges {e}).Adj x y := by
              rw [SimpleGraph.deleteEdges]
              refine ⟨ha, fun h => ?_⟩
              simp [SimpleGraph.fromEdgeSet] at h
              exact hq (by rw [SimpleGraph.Walk.edges_cons]; simp [h])
            exact SimpleGraph.Walk.cons ha' (ih hq_qb)
        exact (conv p hno_e).reachable
      rw [← ha, ← hb]
      exact Quot.sound hab_Ge
  -- Cardinality argument
  -- The fiber over CuvG has 2 elements (Cu and Cv), all others have 1
  -- So |domain| = 2 + (|codomain| - 1) * 1 = |codomain| + 1
  have h_card : Fintype.card ((G.deleteEdges {e}).ConnectedComponent) =
                Fintype.card (G.ConnectedComponent) + 1 := by
    -- Key: domain ≃ ({x // x ≠ Cv} ⊕ Unit) ≃ (codomain ⊕ Unit)
    -- Define type of elements ≠ Cv
    let S := {x : (G.deleteEdges {e}).ConnectedComponent // x ≠ Cv}
    -- Build Equiv: domain ≃ S ⊕ Unit non-computably
    -- This avoids needing DecidableEq for the cardinality argument
    classical
    let equiv_domain_S_unit : (G.deleteEdges {e}).ConnectedComponent ≃ S ⊕ Unit := 
      { toFun := fun x => if hx : x = Cv then Sum.inr () else Sum.inl ⟨x, hx⟩
        invFun := fun x => x.elim (fun ⟨y, hy⟩ => y) (fun _ => Cv)
        left_inv := fun x => by
          classical
          simp only
          by_cases hx : x = Cv <;> simp [hx]
        right_inv := fun x => by
          cases x using Sum.rec with
          | inl val =>
            simp only
            split
            · rename_i h
              exact absurd h val.2
            · rfl
          | inr _ => simp }
      -- Now show the cardinality: |domain| = |S ⊕ Unit| = |S| + 1 = |codomain| + 1
    have h1 : Fintype.card ((G.deleteEdges {e}).ConnectedComponent) = Fintype.card (S ⊕ Unit) := 
      Fintype.card_congr equiv_domain_S_unit
    rw [h1, Fintype.card_sum, Fintype.card_unit]
    -- Now need: Fintype.card S = Fintype.card (G.ConnectedComponent)
    -- Define g : S → G.ConnectedComponent
    let g : S → G.ConnectedComponent := fun x => f x.val
    -- g is injective
    have hg_inj : Function.Injective g := by
      intro ⟨x, hx⟩ ⟨y, hy⟩ hgy_eq
      exact Subtype.eq (hinj_excl_Cv x y hx hy (by simpa [g] using hgy_eq))
    -- g is surjective
    have hg_surj : Function.Surjective g := by
      intro c'
      obtain ⟨x, hx⟩ := hsurj c'
      by_cases hx'Cv : x = Cv
      · subst hx'Cv
        rw [← hx]
        refine ⟨⟨Cu, hCuNeCv⟩, ?_⟩
        exact hfCu_eq_Cv
      · exact ⟨⟨x, hx'Cv⟩, hx⟩
    have h2 : Fintype.card S = Fintype.card (G.ConnectedComponent) := by
      letI : Fintype (S ⊕ Unit) := Fintype.ofEquiv _ equiv_domain_S_unit
      letI : Fintype S := by infer_instance
      exact Fintype.card_congr (Equiv.ofBijective g ⟨hg_inj, hg_surj⟩)
    rw [h2]
  exact h_card

/-- Deleting a bridge leaves the circuit rank unchanged. Arithmetic consequence of
    `edgeFinset_card_delete_of_mem` and `numComponents_delete_bridge`. -/
theorem circuitRank_delete_bridge
    (G : SimpleGraph V) [DecidableRel G.Adj] {e : Sym2 V}
    (he : e ∈ G.edgeFinset) (hb : G.IsBridge e)
    [DecidableRel (G.deleteEdges {e}).Adj] :
    circuitRank (G.deleteEdges {e}) = circuitRank G := by
  rw [circuitRank, circuitRank, edgeFinset_card_delete_of_mem G he,
    numComponents_delete_bridge G he hb]
  have hpos : 0 < G.edgeFinset.card := Finset.card_pos.mpr ⟨e, he⟩
  omega

/-- **Forward direction.** An acyclic graph has vanishing circuit rank.

    Strong induction on the edge count. In an acyclic graph every edge is a bridge
    (`SimpleGraph.isAcyclic_iff_forall_edge_isBridge`), so `circuitRank_delete_bridge`
    says deletion does not change the rank; acyclicity is inherited by the spanning
    subgraph (`SimpleGraph.IsAcyclic.anti`), so we recurse down to the edgeless graph,
    where `numComponents = Fintype.card V` and the rank is `0 - |V| + |V| = 0`.

    (Hart, post-run-3 completion — Aristotle run 3 left this as the single remaining
    `sorry`; it is closed here from run-3 lemmas that are themselves axiom-clean.) -/
theorem circuitRank_eq_zero_of_isAcyclic (G : SimpleGraph V) [DecidableRel G.Adj]
    (hac : G.IsAcyclic) : circuitRank G = 0 := by
  classical
  have hInd : ∀ m : ℕ, ∀ (H : SimpleGraph V) [DecidableRel H.Adj],
      H.edgeFinset.card = m → H.IsAcyclic → circuitRank H = 0 := by
    intro m
    exact Nat.strong_induction_on m fun m ih H _ hcard hHac => by
      by_cases hEmpty : H.edgeFinset = ∅
      · -- Edgeless: every vertex is its own component.
        have hNoAdj : ∀ u v, ¬H.Adj u v := by
          intro u v hadj
          have hmem : Sym2.mk (u, v) ∈ H.edgeFinset := SimpleGraph.mem_edgeFinset.mpr hadj
          simp [hEmpty] at hmem
        have hReach : ∀ u v, H.Reachable u v ↔ u = v := by
          intro u v
          constructor
          · intro ⟨p⟩
            induction p with
            | nil => rfl
            | @cons u₁ u₂ v₁ hadj tail ih => exact (hNoAdj u₁ u₂ hadj).elim
          · intro h; simp [h]
        have hequiv : H.Reachable = fun u v => u = v := by ext u v; exact hReach u v
        let f : V → H.ConnectedComponent := fun v => Quot.mk H.Reachable v
        let g : H.ConnectedComponent → V := Quot.lift (fun v => v) (by simp [hequiv])
        have hf_g : ∀ x, f (g x) = x := fun x => by rcases x with ⟨a⟩; rfl
        have hg_f : ∀ v, g (f v) = v := fun v => rfl
        let equiv : H.ConnectedComponent ≃ V :=
          { toFun := g, invFun := f, left_inv := hf_g, right_inv := hg_f }
        have hcardCC : numComponents H = Fintype.card V := Fintype.card_congr equiv
        simp [circuitRank, hcardCC, hEmpty]
      · -- Pick any edge; in an acyclic graph it is a bridge.
        obtain ⟨e, he⟩ := Finset.nonempty_iff_ne_empty.mpr hEmpty
        have heS : e ∈ H.edgeSet := SimpleGraph.mem_edgeFinset.mp he
        have hb : H.IsBridge e :=
          (SimpleGraph.isAcyclic_iff_forall_edge_isBridge.mp hHac) heS
        have hcard_delete : (H.deleteEdges {e}).edgeFinset.card = H.edgeFinset.card - 1 :=
          edgeFinset_card_delete_of_mem H he
        have hac' : (H.deleteEdges {e}).IsAcyclic :=
          SimpleGraph.IsAcyclic.anti (SimpleGraph.deleteEdges_le {e}) hHac
        have hcp : 0 < H.edgeFinset.card := Finset.card_pos.mpr ⟨e, he⟩
        have hrec := ih (H.edgeFinset.card - 1) (by omega) (H.deleteEdges {e}) hcard_delete hac'
        rwa [circuitRank_delete_bridge H he hb] at hrec
  exact hInd G.edgeFinset.card G rfl hac

/-- Circuit rank is never negative: `|V| ≤ c + |E|` for every finite graph.

    Load-bearing despite appearances — it is what makes `FaceCount.ofCircuitRank` a valid
    witness (`(circuitRank G + 1).toNat` casts back only when `circuitRank G + 1 ≥ 0`), and
    the non-vacuity of every `FaceCount`-conditional result rests on that. -/
theorem circuitRank_nonneg (G : SimpleGraph V) [DecidableRel G.Adj] :
    0 ≤ circuitRank G := by
  -- We prove by induction on edge count that numComponents G + |E| ≥ |V|
  unfold circuitRank
  -- Key lemma: for any graph, Fintype.card V ≤ numComponents G + G.edgeFinset.card
  suffices h : (Fintype.card V : ℤ) ≤ numComponents G + G.edgeFinset.card by
    linarith
  -- Prove by induction on edges: for any graph, |V| ≤ c + |E|
  -- Base case: empty edge set gives numComponents = Fintype.card V
  -- Inductive step: adding an edge changes (c + |E|) by at most 0 (if merging components) or +1 (if creating cycle)
  -- We use the contrapositive of numComponents_delete_bridge:
  -- If e is a bridge, deleteEdges increases components by 1, so numComponents G = numComponents deleteEdges - 1
  -- If e is not a bridge, numComponents is preserved
  by_cases hEmpty : G.edgeFinset = ∅
  · -- Empty edge set: G has no edges, so each vertex is its own component
    have hNoAdj : ∀ u v, ¬G.Adj u v := by
      intro u v hadj
      have : Sym2.mk (u, v) ∈ G.edgeFinset := SimpleGraph.mem_edgeFinset.mpr hadj
      simp [hEmpty] at this
    have : numComponents G = Fintype.card V := by
      unfold numComponents
      -- Reachable u v ↔ u = v when there are no edges
      have hReach : ∀ u v, G.Reachable u v ↔ u = v := by
        intro u v
        constructor
        · intro ⟨p⟩
          induction p with
          | nil => rfl
          | @cons u₁ u₂ v₁ hadj tail ih =>
            exact (hNoAdj u₁ u₂ hadj).elim
        · intro h
          rw [h]
      -- Build an equivalence between G.ConnectedComponent and V
      have hequiv : G.Reachable = fun u v => u = v := by ext u v; exact hReach u v
      -- ConnectedComponent is Quot G.Reachable
      have hCC : G.ConnectedComponent = Quot G.Reachable := rfl
      -- Define the equivalence using the quotient API
      let f : V → G.ConnectedComponent := fun v => Quot.mk G.Reachable v
      let g : G.ConnectedComponent → V := Quot.lift (fun v => v) (by simp [hequiv])
      have hf_g : ∀ x, f (g x) = x := by
        intro x
        rcases x with ⟨a⟩
        exact rfl
      have hg_f : ∀ v, g (f v) = v := fun v => rfl
      let equiv : G.ConnectedComponent ≃ V := {
        toFun := g
        invFun := f
        left_inv := hf_g
        right_inv := hg_f
      }
      exact Fintype.card_congr equiv
    linarith
  · -- Non-empty: use strong induction on edge count
    -- Goal: Fintype.card V ≤ numComponents G + edgeFinset.card
    -- Equivalently: 0 ≤ circuitRank G
    have hInd : ∀ m : ℕ, ∀ (H : SimpleGraph V) [DecidableRel H.Adj],
        H.edgeFinset.card = m → (Fintype.card V : ℤ) ≤ numComponents H + H.edgeFinset.card := by
      intro m
      exact Nat.strong_induction_on m fun m ih H _ hcard => by
        by_cases hEmpty' : H.edgeFinset = ∅
        · -- Base case: no edges
          -- When edges = ∅, numComponents = |V|
          have hNoAdj : ∀ u v, ¬H.Adj u v := by
            intro u v hadj
            have hmem : Sym2.mk (u, v) ∈ H.edgeFinset := SimpleGraph.mem_edgeFinset.mpr hadj
            simp [hEmpty'] at hmem
          have hReach : ∀ u v, H.Reachable u v ↔ u = v := by
            intro u v
            constructor
            · intro ⟨p⟩
              induction p with
              | nil => rfl
              | @cons u₁ u₂ v₁ hadj tail ih => exact (hNoAdj u₁ u₂ hadj).elim
            · intro h; simp [h]
          have hequiv : H.Reachable = fun u v => u = v := by ext u v; exact hReach u v
          let f : V → H.ConnectedComponent := fun v => Quot.mk H.Reachable v
          let g : H.ConnectedComponent → V := Quot.lift (fun v => v) (by simp [hequiv])
          have hf_g : ∀ x, f (g x) = x := fun x => by rcases x with ⟨a⟩; rfl
          have hg_f : ∀ v, g (f v) = v := fun v => rfl
          let equiv : H.ConnectedComponent ≃ V := { toFun := g, invFun := f, left_inv := hf_g, right_inv := hg_f }
          have hcardCC : numComponents H = Fintype.card V := Fintype.card_congr equiv
          simp [hcardCC, hEmpty']
        · -- Inductive case: at least one edge
          -- Pick an edge
          obtain ⟨e, he⟩ := Finset.nonempty_iff_ne_empty.mpr hEmpty'
          by_cases hb : H.IsBridge e
          · -- e is a bridge: numComponents increases by 1 when deleting e
            have hdec : DecidableRel (H.deleteEdges {e}).Adj := inferInstance
            have hcard_delete : (H.deleteEdges {e}).edgeFinset.card = H.edgeFinset.card - 1 := by
              have h2 : (H.deleteEdges {e}).edgeFinset = H.edgeFinset \ {e} := by
                ext x; simp [SimpleGraph.mem_edgeFinset, SimpleGraph.deleteEdges, Finset.mem_sdiff]
              rw [h2, Finset.card_sdiff]; simp [he]
            have hnc : numComponents (H.deleteEdges {e}) = numComponents H + 1 := numComponents_delete_bridge H he hb
            -- By IH: |V| ≤ numComponents delete + edges delete
            have hcard_pos : 0 < H.edgeFinset.card := Finset.card_pos.mpr ⟨e, he⟩
            have hi := ih (H.edgeFinset.card - 1) (by omega) (H.deleteEdges {e}) hcard_delete
            -- numComponents delete = numComponents H + 1, edges delete = edges H - 1
            rw [hnc, hcard_delete] at hi
            have hcast2 : ((H.edgeFinset.card - 1 : ℕ) : ℤ) = H.edgeFinset.card - 1 := by
              omega
            simp [hcast2] at hi
            linarith
          · -- e is not a bridge: numComponents stays the same when deleting e
            have hdec : DecidableRel (H.deleteEdges {e}).Adj := inferInstance
            have hcard_delete : (H.deleteEdges {e}).edgeFinset.card = H.edgeFinset.card - 1 := by
              have h2 : (H.deleteEdges {e}).edgeFinset = H.edgeFinset \ {e} := by
                ext x; simp [SimpleGraph.mem_edgeFinset, SimpleGraph.deleteEdges, Finset.mem_sdiff]
              rw [h2, Finset.card_sdiff]; simp [he]
            -- Prove numComponents(deleteEdges H {e}) = numComponents H
            -- by showing injection and surjection between components
            let H' := H.deleteEdges {e}
            have hinj : H' ≤ H := SimpleGraph.deleteEdges_le {e}
            have hreach_mono : ∀ u v, H'.Reachable u v → H.Reachable u v := by
              intro u v h
              obtain ⟨w⟩ := h
              induction w with
              | nil => exact ⟨.nil⟩
              | cons hadj w' ih =>
                obtain ⟨ih'⟩ := ih
                exact ⟨ih'.cons (hinj hadj)⟩
            -- e is not a bridge, so its endpoints are reachable in H'
            have he' : e ∈ H.edgeSet := SimpleGraph.mem_edgeFinset.mp he
            unfold SimpleGraph.IsBridge at hb
            have hsym : ∀ a b, (fun v w => ¬H'.Reachable v w) a b = (fun v w => ¬H'.Reachable v w) b a := by
              intro a b
              apply propext
              exact ⟨fun h => h ∘ (·.symm), fun h => h ∘ (·.symm)⟩
            have hb' : ¬Sym2.lift ⟨fun v w => ¬H'.Reachable v w, hsym⟩ e := fun h => hb ⟨he', h⟩
            -- Extract endpoints of e
            obtain ⟨u, v, heq⟩ : ∃ u v, e = Sym2.mk (u, v) := by
              have ⟨p, hp⟩ := Quot.exists_rep e
              use p.1, p.2
              simp [hp]
            -- Endpoints are reachable in H'
            rw [heq] at hb'
            rw [Sym2.lift_mk] at hb'
            have hreach_ev : H'.Reachable u v := not_not.mp hb'
            -- Convert H-walks to H'-walks: any H-reachable pair is H'-reachable
            have hreach_equiv : ∀ a b, H.Reachable a b → H'.Reachable a b := by
              intro a b ⟨p⟩
              induction p with
              | nil => exact ⟨SimpleGraph.Walk.nil⟩
              | @cons a c b hadj p' ih =>
                -- hadj : H.Adj a c, p' : H.Walk c b, ih : H'.Reachable c b
                let edg : Sym2 V := Sym2.mk (a, c)
                by_cases heq' : e = edg
                · -- Edge is e: use reachability of u, v
                  have heq2 : Sym2.mk (a, c) = Sym2.mk (u, v) := heq'.symm.trans heq
                  rcases Sym2.eq_iff.mp heq2 with ⟨rfl, rfl⟩ | ⟨rfl, rfl⟩
                  · -- a = u, c = v: hreach_ev : H'.Reachable u v = H'.Reachable a c
                    exact ⟨hreach_ev.some.append ih.some⟩
                  · -- a = v, c = u: hreach_ev : H'.Reachable u v, need H'.Reachable v u
                    exact ⟨hreach_ev.symm.some.append ih.some⟩
                · -- Edge is not e: it's in H'
                  have hadj_H' : H'.Adj a c := by
                    rw [SimpleGraph.deleteEdges_adj]
                    exact ⟨hadj, fun h => heq' (h ▸ rfl)⟩
                  exact ⟨SimpleGraph.Walk.cons hadj_H' ih.some⟩
            -- Injection from H'.ConnectedComponent to H.ConnectedComponent
            -- Injection from H'.ConnectedComponent to H.ConnectedComponent
            let f : H'.ConnectedComponent → H.ConnectedComponent := fun c =>
              Quot.lift (fun v => Quot.mk _ v) (by
                intro a b hab
                exact Quot.sound (hreach_mono a b hab)) c
            have f_inj : Function.Injective f := by
              intro c1 c2 hfeq
              obtain ⟨v1⟩ := c1
              obtain ⟨v2⟩ := c2
              have hf1 : f (Quot.mk H'.Reachable v1) = Quot.mk H.Reachable v1 := rfl
              have hf2 : f (Quot.mk H'.Reachable v2) = Quot.mk H.Reachable v2 := rfl
              have hH : Quot.mk H.Reachable v1 = Quot.mk H.Reachable v2 := by rw [← hf1, hfeq, hf2]
              have hreachH : H.Reachable v1 v2 := SimpleGraph.ConnectedComponent.exact hH
              have hreachH' : H'.Reachable v1 v2 := hreach_equiv v1 v2 hreachH
              exact Quot.sound hreachH'
            have hle : numComponents H' ≤ numComponents H := Fintype.card_le_of_injective f f_inj
            -- Surjection from H'.ConnectedComponent to H.ConnectedComponent
            let g : H'.ConnectedComponent → H.ConnectedComponent := fun c =>
              Quot.lift (fun v => Quot.mk _ v) (by
                intro a b hab
                exact Quot.sound (hreach_mono a b hab)) c
            have g_surj : Function.Surjective g := by
              intro cH
              exact Quot.inductionOn cH fun v => ⟨Quot.mk _ v, rfl⟩
            have hge : numComponents H ≤ numComponents H' := Fintype.card_le_of_surjective _ g_surj
            have h_nc : numComponents H' = numComponents H := Nat.le_antisymm hle hge
            -- By IH: |V| ≤ numComponents delete + edges delete
            have hcard_pos : 0 < H.edgeFinset.card := Finset.card_pos.mpr ⟨e, he⟩
            have hi := ih (H.edgeFinset.card - 1) (by omega) H' hcard_delete
            rw [h_nc, hcard_delete] at hi
            have hcast2 : ((H.edgeFinset.card - 1 : ℕ) : ℤ) = H.edgeFinset.card - 1 := by omega
            simp [hcast2] at hi
            linarith
    exact hInd (G.edgeFinset.card) G rfl

/-- Deleting a non-bridge edge drops the circuit rank by exactly one and leaves the
    component count alone. This is Proposition 4(ii). -/
theorem circuitRank_delete_nonBridge
    (G : SimpleGraph V) [DecidableRel G.Adj] {e : Sym2 V}
    (he : e ∈ G.edgeFinset) (hb : ¬ G.IsBridge e)
    [DecidableRel (G.deleteEdges {e}).Adj] :
    circuitRank (G.deleteEdges {e}) = circuitRank G - 1 := by
  have h_edge : (G.deleteEdges {e}).edgeFinset.card = G.edgeFinset.card - 1 := by
    have h2 : (G.deleteEdges {e}).edgeFinset = G.edgeFinset \ {e} := by
      ext x; simp [SimpleGraph.mem_edgeFinset, SimpleGraph.deleteEdges, Finset.mem_sdiff]
    rw [h2, Finset.card_sdiff]; simp [he]
  have h_nc : numComponents (G.deleteEdges {e}) = numComponents G := by
    have he' : e ∈ G.edgeSet := SimpleGraph.mem_edgeFinset.mp he
    unfold SimpleGraph.IsBridge at hb
    -- hb : ¬(e ∈ G.edgeSet ∧ Sym2.lift ⟨fun v w => ¬(G.deleteEdges {e}).Reachable v w, pr⟩ e)
    -- Since he' : e ∈ G.edgeSet, we get ¬Sym2.lift ...
    let H := G.deleteEdges {e}
    -- hnotbridge says: ¬(∀ v w with e = (v,w), ¬H.Reachable v w)
    -- which means: there exist v,w with e=(v,w) and H.Reachable v w
    apply Nat.le_antisymm
    · -- H.numComponents ≤ G.numComponents (no split because endpoints connected)
      -- Every H-component is contained in a G-component (injection)
      have hinj : H ≤ G := SimpleGraph.deleteEdges_le {e}
      have hreach_mono : ∀ u v, H.Reachable u v → G.Reachable u v := by
        intro u v h
        obtain ⟨w⟩ := h
        induction w with
        | nil => exact ⟨.nil⟩
        | cons hadj w' ih =>
          obtain ⟨ih'⟩ := ih
          exact ⟨ih'.cons (hinj hadj)⟩
      -- Injection from H.ConnectedComponent to G.ConnectedComponent
      let f : H.ConnectedComponent → G.ConnectedComponent := fun c =>
        Quot.lift (fun v => Quot.mk _ v) (by
          intro a b hab
          exact Quot.sound (hreach_mono a b hab)) c
      -- f is injective because if two H-components map to same G-component,
      -- the vertices are reachable in G, hence in H (using non-bridge property)
      -- Key: since e's endpoints are reachable in H, any G-reachable pair is H-reachable
      -- (replace e in the path with a detour through the endpoints)
      have hreach_equiv : ∀ u v, G.Reachable u v → H.Reachable u v := by
        -- Define a function that converts G-walks to H-walks
        have convert : ∀ (u v : V) (p : G.Walk u v), H.Walk u v := by
          intro u v p
          induction p with
          | nil => exact .nil
          | @cons u₀ u₁ v₀ hadj p' ih =>
            -- hadj : G.Adj u₀ u₁ means u₀, u₁ form an edge in G
            -- Define the edge (u₀, u₁) as a Sym2
            let edg : Sym2 V := Quot.mk _ (u₀, u₁)
            -- Check if this edge equals e
            by_cases heq : e = edg
            · -- Edge is e: u₀ and u₁ are endpoints, so reachable in H (non-bridge)
              -- From hnotbridge, the endpoints of e are reachable in H
              have hreach : H.Reachable u₀ u₁ := by
                -- heq : e = edg = Quot.mk _ (u₀, u₁)
                -- hb : ¬(e ∈ G.edgeSet ∧ Sym2.lift ⟨fun v w => ¬H.Reachable v w, _⟩ e)
                -- Since he' : e ∈ G.edgeSet, we have ¬Sym2.lift ...
                have hsym : ∀ a b, (fun v w => ¬H.Reachable v w) a b = (fun v w => ¬H.Reachable v w) b a := by
                  intro a b
                  apply propext
                  exact ⟨fun h => h ∘ (·.symm), fun h => h ∘ (·.symm)⟩
                have hb' : ¬Sym2.lift ⟨fun v w => ¬H.Reachable v w, hsym⟩ e := fun h => hb ⟨he', h⟩
                -- Use the fact that e = s(u₀, u₁) to extract reachability
                rw [heq] at hb'
                -- hb' : ¬Sym2.lift ⟨fun v w => ¬H.Reachable v w, hsym⟩ (Quot.mk _ (u₀, u₁))
                rw [Sym2.lift_mk] at hb'
                -- hb' should now be ¬(fun v w => ¬H.Reachable v w) u₀ u₁ = ¬¬H.Reachable u₀ u₁
                exact not_not.mp hb'
              exact (hreach.some).append ih
            · -- Edge is not e: it's in H
              have hadj_H : H.Adj u₀ u₁ := by
                rw [SimpleGraph.deleteEdges_adj]
                exact ⟨hadj, fun h => heq (h ▸ rfl)⟩
              exact SimpleGraph.Walk.cons hadj_H ih
        intro s t ⟨p⟩
        exact Nonempty.intro (convert s t p)
      have f_inj : Function.Injective f := by
        intro c1 c2 hfeq
        obtain ⟨v1⟩ := c1
        obtain ⟨v2⟩ := c2
        -- f (Quot.mk H.Reachable v) = Quot.mk G.Reachable v by definition
        have hf1 : f (Quot.mk H.Reachable v1) = Quot.mk G.Reachable v1 := rfl
        have hf2 : f (Quot.mk H.Reachable v2) = Quot.mk G.Reachable v2 := rfl
        have hG : Quot.mk G.Reachable v1 = Quot.mk G.Reachable v2 := by rw [← hf1, hfeq, hf2]
        -- hG means G.Reachable v1 v2
        have hreachG : G.Reachable v1 v2 := by
          have := Quot.eq.mp hG
          -- Relation.EqvGen G.Reachable = G.Reachable since Reachable is an equivalence relation
          -- Use that EqvGen is the transitive closure of the symmetric transitive closure
          -- For an already transitive symmetric reflexive relation, EqvGen = id
          exact SimpleGraph.ConnectedComponent.exact hfeq
        -- By hreach_equiv, H.Reachable v1 v2
        have hreachH : H.Reachable v1 v2 := hreach_equiv v1 v2 hreachG
        -- Convert to quotient equality
        exact Quot.sound hreachH
      exact Fintype.card_le_of_injective f f_inj
    · -- G.numComponents ≤ H.numComponents (subgraph has ≥ components)
      -- There's a surjection from H.ConnectedComponent to G.ConnectedComponent
      have hinj : H ≤ G := SimpleGraph.deleteEdges_le {e}
      -- Reachability in H implies reachability in G
      have hreach_mono : ∀ u v, H.Reachable u v → G.Reachable u v := by
        intro u v h
        obtain ⟨w⟩ := h
        induction w with
        | nil => exact ⟨.nil⟩
        | cons hadj w' ih =>
          obtain ⟨ih'⟩ := ih
          exact ⟨ih'.cons (hinj hadj)⟩
      -- Define the surjection f : H.ConnectedComponent → G.ConnectedComponent
      -- Each H-component maps to the G-component containing it
      let f : H.ConnectedComponent → G.ConnectedComponent := fun c =>
        Quot.lift (fun v => Quot.mk _ v) (by
          intro a b hab
          exact Quot.sound (hreach_mono a b hab)) c
      have f_surj : Function.Surjective f := by
        intro cG
        exact Quot.inductionOn cG fun v => ⟨Quot.mk _ v, rfl⟩
      exact Fintype.card_le_of_surjective _ f_surj
  simp [circuitRank, h_edge, h_nc]
  have hcard : 1 ≤ G.edgeFinset.card := Finset.card_pos.mpr ⟨e, he⟩
  simp [Int.ofNat_sub hcard]; omega

theorem numComponents_delete_nonBridge
    (G : SimpleGraph V) [DecidableRel G.Adj] {e : Sym2 V}
    (he : e ∈ G.edgeFinset) (hb : ¬ G.IsBridge e)
    [DecidableRel (G.deleteEdges {e}).Adj] :
    numComponents (G.deleteEdges {e}) = numComponents G := by
  have hr := circuitRank_delete_nonBridge G he hb
  have he' : (G.deleteEdges {e}).edgeFinset.card = G.edgeFinset.card - 1 := by
    simp [SimpleGraph.edgeFinset, SimpleGraph.deleteEdges, Finset.card_sdiff]
    have he' : e ∈ G.edgeSet := by simpa [SimpleGraph.mem_edgeSet] using he
    have : ({e} : Finset (Sym2 V)) ∩ G.edgeSet.toFinset = {e} := by
      rw [Finset.singleton_inter]
      simp [he']
    rw [this, Finset.card_singleton]
  have hcard : G.edgeFinset.card ≥ 1 := Finset.card_pos.mpr ⟨e, he⟩
  have he'' : ((G.deleteEdges {e}).edgeFinset.card : ℤ) = (G.edgeFinset.card : ℤ) - 1 := by
    simp [he', Nat.cast_sub hcard]
  simp only [circuitRank] at hr
  omega

/-- A finite graph has vanishing circuit rank exactly when it is acyclic.

    Forward direction: `circuitRank_eq_zero_of_isAcyclic` above.
    Reverse direction: if `G` is not acyclic it has a non-bridge edge, and deleting that
    edge drops the rank by one (`circuitRank_delete_nonBridge`) below a quantity that is
    never negative (`circuitRank_nonneg`), so the rank was at least one. -/
theorem circuitRank_eq_zero_iff_isAcyclic (G : SimpleGraph V) [DecidableRel G.Adj] :
    circuitRank G = 0 ↔ G.IsAcyclic := by
  classical
  refine ⟨fun h0 => ?_, circuitRank_eq_zero_of_isAcyclic G⟩
  by_contra hac
  rw [SimpleGraph.isAcyclic_iff_forall_edge_isBridge] at hac
  push_neg at hac
  obtain ⟨e, heS, hnb⟩ := hac
  have he : e ∈ G.edgeFinset := SimpleGraph.mem_edgeFinset.mpr heS
  have hd := circuitRank_delete_nonBridge G he hnb
  have hnn := circuitRank_nonneg (G.deleteEdges {e})
  omega

/-! ## The topological bridge, as a hypothesis

  `FaceCount` packages the one thing we are *not* proving: that the number of compartments
  of the fuel matrix is the circuit rank of the corridor-plus-boundary, plus one.
  Justification is Alexander duality (manuscript §2.2–2.3).

  Everything below is a consequence of this hypothesis together with the graph theory
  above, which is exactly the claim the paper makes. -/

/-- A compartment-counting function satisfying the duality relation. -/
structure FaceCount (V : Type*) [Fintype V] [DecidableEq V] where
  /-- Number of connected components of the complement of the corridor. -/
  faces : (G : SimpleGraph V) → [DecidableRel G.Adj] → ℕ
  /-- Alexander duality, assumed. -/
  duality : ∀ (G : SimpleGraph V) [DecidableRel G.Adj],
      (faces G : ℤ) = circuitRank G + 1

/-- A concrete witness that the combinatorial `FaceCount` interface is inhabited.
    It assigns the natural number represented by `circuitRank G + 1`. -/
noncomputable def FaceCount.ofCircuitRank : FaceCount V where
  faces G := (circuitRank G + 1).toNat
  duality G := by
    intro
    rw [Int.toNat_of_nonneg]
    exact add_nonneg (circuitRank_nonneg G) (by omega)

variable (F : FaceCount V)

/-- **Proposition 1 — the Zero-Cut Lemma (combinatorial form).**
    An acyclic corridor leaves the fuel matrix in exactly one compartment, regardless of
    how many vertices or edges it has. "Trees cannot cut." -/
theorem zeroCut (G : SimpleGraph V) [DecidableRel G.Adj] (h : G.IsAcyclic) :
    F.faces G = 1 := by
  have hr : circuitRank G = 0 := (circuitRank_eq_zero_iff_isAcyclic G).2 h
  have hd := F.duality G
  rw [hr] at hd
  exact_mod_cast hd

/-- **Proposition 2 — compartment count is circuit rank.** -/
theorem faces_eq_circuitRank_add_one (G : SimpleGraph V) [DecidableRel G.Adj] :
    (F.faces G : ℤ) = circuitRank G + 1 :=
  F.duality G

/-- **Proposition 4(i) — bridges have zero cut capacity.**
    Deleting a bridge merges no compartments. -/
theorem bridge_no_merge
    (G : SimpleGraph V) [DecidableRel G.Adj] {e : Sym2 V}
    (he : e ∈ G.edgeFinset) (hb : G.IsBridge e)
    [DecidableRel (G.deleteEdges {e}).Adj] :
    F.faces (G.deleteEdges {e}) = F.faces G := by
  have hd := circuitRank_delete_bridge G he hb
  have h₁ := F.duality (G.deleteEdges {e})
  have h₂ := F.duality G
  omega

/-- **Proposition 4(ii) — a non-bridge merges exactly one pair of compartments.** -/
theorem nonBridge_merges_exactly_one
    (G : SimpleGraph V) [DecidableRel G.Adj] {e : Sym2 V}
    (he : e ∈ G.edgeFinset) (hb : ¬ G.IsBridge e)
    [DecidableRel (G.deleteEdges {e}).Adj] :
    F.faces (G.deleteEdges {e}) + 1 = F.faces G := by
  have hd := circuitRank_delete_nonBridge G he hb
  have h₁ := F.duality (G.deleteEdges {e})
  have h₂ := F.duality G
  omega

/-- **Proposition 4(iii) — disjoint support.**
    No edge is simultaneously connectivity-critical (a bridge) and cut-bearing (its
    deletion merges compartments). The two design objectives never compete for the
    same edge.

    NOTE the scope condition, which matters: "connectivity-critical" here is the *binary*
    notion — deletion disconnects. The paper conjectures (Appendix A.4) that this fails
    for a resistance-based notion of criticality. That weaker statement is NOT claimed here. -/
theorem disjoint_support
    (G : SimpleGraph V) [DecidableRel G.Adj] {e : Sym2 V}
    (he : e ∈ G.edgeFinset)
    [DecidableRel (G.deleteEdges {e}).Adj] :
    ¬ (G.IsBridge e ∧ F.faces (G.deleteEdges {e}) < F.faces G) := by
  rintro ⟨hb, hlt⟩
  have h := bridge_no_merge F G he hb
  omega

/-! ## Boundary anchoring

  The landscape boundary `∂Ω` is modelled by contracting the exterior to a single vertex —
  the standard one-point-compactification / outer-face-vertex device. A corridor tree `T`
  anchored to the boundary at `b` points becomes a graph on `Option V` in which the new
  vertex `none` is joined to `b` vertices of `T`.

  Proposition 5 then says: circuit rank `b - 1`, hence exactly `b` compartments. -/

/-- Attach a boundary vertex `none` to the given set of anchor vertices. -/
def anchor (G : SimpleGraph V) (A : Finset V) : SimpleGraph (Option V) where
  Adj x y :=
    match x, y with
    | some u, some v => G.Adj u v
    | none, some v   => v ∈ A
    | some u, none   => u ∈ A
    | none, none     => False
  symm := by
    intro x y h
    cases x with
    | none => cases y <;> simpa using h
    | some x =>
     
      cases y with
      | none => simpa using h
      | some y => exact G.symm h
  loopless := ⟨fun x => by
    cases x with
    | none => simp
    | some x => exact G.loopless.irrefl x⟩

instance (G : SimpleGraph V) [DecidableRel G.Adj] (A : Finset V) :
    DecidableRel (anchor G A).Adj := by
  intro x y
  cases x <;> cases y <;> simp only [anchor] <;> infer_instance

lemma anchor_connected
    (G : SimpleGraph V) [DecidableRel G.Adj] (hc : G.Connected)
    (A : Finset V) (hA : A.Nonempty) : (anchor G A).Connected := by
  apply SimpleGraph.Connected.mk
  -- Need to prove: (anchor G A).Preconnected = ∀ u v, (anchor G A).Reachable u v
  obtain ⟨anch, hanch⟩ := hA
  intro u v
  -- Case analysis on u and v
  rcases u with _ | u <;> rcases v with _ | v
  · -- u = none, v = none
    exact SimpleGraph.Reachable.refl (none : Option V)
  · -- u = none, v = some v
    -- none is adjacent to anch (since anch ∈ A), and anch can reach v in G
    have h1 : (anchor G A).Adj none (some anch) := by simp [anchor, hanch]
    have h2 : G.Reachable anch v := hc anch v
    -- Convert G.Reachable to (anchor G A).Reachable
    let hom : G →g (anchor G A) := {
      toFun := some
      map_rel' := @fun x y hxy => show (anchor G A).Adj (some x) (some y) from by simp [anchor, hxy]
    }
    have h2' : (anchor G A).Reachable (some anch) (some v) := h2.map hom
    exact SimpleGraph.Reachable.trans h1.reachable h2'
  · -- u = some u, v = none
    have h1 : (anchor G A).Adj (some anch) none := by simp [anchor, hanch]
    have h2 : G.Reachable u anch := hc u anch
    let hom : G →g (anchor G A) := {
      toFun := some
      map_rel' := @fun x y hxy => show (anchor G A).Adj (some x) (some y) from by simp [anchor, hxy]
    }
    have h2' : (anchor G A).Reachable (some u) (some anch) := h2.map hom
    exact h2'.trans h1.reachable
  · -- u = some u, v = some v
    have h1 : G.Reachable u v := hc u v
    let hom : G →g (anchor G A) := {
      toFun := some
      map_rel' := @fun x y hxy => show (anchor G A).Adj (some x) (some y) from by simp [anchor, hxy]
    }
    exact h1.map hom

lemma numComponents_eq_one_of_connected
    (G : SimpleGraph V) [DecidableRel G.Adj] (hc : G.Connected) : numComponents G = 1 := by
  unfold numComponents
  letI : Unique G.ConnectedComponent :=
    { default := G.connectedComponentMk hc.nonempty.some
      uniq := by
        intro c
        induction c using SimpleGraph.ConnectedComponent.ind
        apply SimpleGraph.ConnectedComponent.sound
        exact hc _ _ }
  exact Fintype.card_unique

lemma anchor_edge_card
    (G : SimpleGraph V) [DecidableRel G.Adj] (A : Finset V) :
    (anchor G A).edgeFinset.card = G.edgeFinset.card + A.card := by
  -- Define the two parts of the edge set
  let E1 := G.edgeFinset.image (fun e => e.map (Option.some))
  let E2 := A.image (fun v => Sym2.mk (none, some v))
  -- The edge set is the union of E1 and E2
  have h_union : (anchor G A).edgeFinset = E1 ∪ E2 := by
    ext e
    simp only [Finset.mem_union, Finset.mem_image]
    rw [SimpleGraph.mem_edgeFinset]
    symm
    apply Iff.symm
    induction e using Sym2.ind with
    | @h u v =>
      simp [anchor, SimpleGraph.edgeSet]
      simp [E1, E2]
      induction u with
      | none =>
        induction v with
        | none =>
          simp [E1, E2]
          intro x hx h_eq
          have key : ∀ (p : V × V), Sym2.map some (Sym2.mk p) ≠ Sym2.mk (none, none) := by
            simp [Sym2.map_pair_eq]
          cases x with | h u v => exact key (u, v) (by simp_all)
        | some v =>
          simp [E1, E2]
          intro x hx h_eq
          cases x with | h u v => simp [Sym2.map_pair_eq] at h_eq
      | some u =>
        induction v with
        | none =>
          simp [E1, E2]
          intro x hx h_eq
          cases x with | h u v => simp [Sym2.map_pair_eq] at h_eq
        | some v =>
          simp [E1, E2]
          constructor
          · intro h
            exact ⟨Sym2.mk (u, v), h, rfl⟩
          · intro ⟨a, ⟨ha, h_eq⟩⟩
            cases a with | h u' v' =>
            simp [SimpleGraph.mem_edgeSet] at ha
            simp [Sym2.map_pair_eq] at h_eq
            rcases h_eq with ⟨rfl, rfl⟩ | ⟨rfl, rfl⟩
            · exact ha
            · exact G.symm ha
  rw [h_union]
  have h_disjoint : Disjoint E1 E2 := by
    simp [E1, E2, Finset.disjoint_left]
    intro a ha x hx h_eq
    cases a with | h u v =>
    simp [Sym2.map_pair_eq] at h_eq
  rw [Finset.card_union_of_disjoint h_disjoint]
  congr 1
  · rw [Finset.card_image_of_injective _ (fun a b hab => by
      cases a with | h u v => cases b with | h u' v' =>
      simp [Sym2.map_pair_eq] at hab
      rcases hab with ⟨rfl, rfl⟩ | ⟨rfl, rfl⟩
      · rfl
      · simp)]
  · rw [Finset.card_image_of_injective _ (fun x y hxy => by simp at hxy; exact hxy)]

/-- Anchoring an acyclic corridor at `b` boundary points gives circuit rank `b - 1`. -/
theorem circuitRank_anchor_of_isAcyclic
    (G : SimpleGraph V) [DecidableRel G.Adj] (hG : G.IsAcyclic) (hc : G.Connected)
    (A : Finset V) (hA : A.Nonempty) :
    circuitRank (anchor G A) = (A.card : ℤ) - 1 := by
  have htree : G.IsTree := ⟨hc, hG⟩
  have hedge := htree.card_edgeFinset
  have hanchor := anchor_edge_card G A
  have hconn := numComponents_eq_one_of_connected (anchor G A) (anchor_connected G hc A hA)
  simp only [circuitRank]
  rw [hanchor, hconn]
  simp only [Fintype.card_option]
  omega

/-- **Proposition 5 — boundary anchoring.**
    A tree corridor meeting the landscape boundary at `b ≥ 1` points partitions the
    landscape into exactly `b` compartments — while its own circuit rank remains zero.

    This is the result the paper's operational recommendation rests on, and the one we
    most want attacked. In particular: check `b = 1` (it should give exactly one
    compartment, i.e. no gain over an unanchored tree — the paper's design rule was
    off by one in an earlier draft for precisely this reason). -/
theorem boundaryAnchor_faces
    (Fo : FaceCount (Option V))
    (G : SimpleGraph V) [DecidableRel G.Adj] (hG : G.IsAcyclic) (hc : G.Connected)
    (A : Finset V) (hA : A.Nonempty) :
    Fo.faces (anchor G A) = A.card := by
  have hr := circuitRank_anchor_of_isAcyclic G hG hc A hA
  have hd := Fo.duality (anchor G A)
  omega

/-- The off-by-one, stated so it cannot be forgotten: the *first* anchor buys nothing. -/
theorem first_anchor_buys_nothing
    (Fo : FaceCount (Option V))
    (G : SimpleGraph V) [DecidableRel G.Adj] (hG : G.IsAcyclic) (hc : G.Connected)
    (a : V) :
    Fo.faces (anchor G {a}) = 1 := by
  simpa using boundaryAnchor_faces Fo G hG hc {a} (Finset.singleton_nonempty a)

end DualCorridor
