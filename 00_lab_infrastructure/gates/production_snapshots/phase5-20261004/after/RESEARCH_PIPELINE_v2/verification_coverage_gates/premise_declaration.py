"""INV-9 sealed-premise intake; static classification, never Lean verification.

The Comparator remains the sole verifier. This gate cannot issue proof evidence,
discharge PL/PD, infer empirical truth, or retrofit historical certificates.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import re

STANDARD = 'VRS-PREMISE-DECLARATION-1'
BASES = frozenset({'THEOREM', 'CONDITIONAL_PL_PD', 'INDEPENDENT'})
CONDITIONAL_PHRASE = 'conditional on premises PL and PD'
# Exact normalized binder statements from the immutable certified Run-902 v003.
RUN902_PREMISES = {'PL': 'R_obs * K ≤ P', 'PD': 'rate ≤ R_obs * D'}
RUN902_THEOREM = 'Run902_product_form_conditional'
RUN902_SIGNATURE = 'theorem Run902_product_form_conditional (R_obs rate P D K : NNReal) (hK : 0 < K) (PL : R_obs * K ≤ P) (PD : rate ≤ R_obs * D) : rate ≤ P * D / K'
RUN900_SIGNATURES = {'intelligence_bound': 'theorem intelligence_bound {Ω State : Type} [MeasurableSpace Ω] [MeasurableSpace State] (μ : Measure Ω) [IsProbabilityMeasure μ] (X : Process Ω State) (O : Process Ω State) (τ : NNReal) (P T kB : NNReal) (h_kB_pos : 0 < kB) (h_T_pos : 0 < T) (h_landauer : (P : ENNReal) ≥ intelligenceCreationRate μ X O τ * ENNReal.ofReal ((kB : ℝ) * (T : ℝ) * Real.log 2)) (hB : observationBandwidth μ O ≠ ⊤) (hRho_le_one : predictiveRichness μ X O τ ≤ 1) : intelligenceCreationRate μ X O τ ≤ min (predictiveRichness μ X O τ * observationBandwidth μ O) (ENNReal.ofReal ((P : ℝ) / ((kB : ℝ) * (T : ℝ) * Real.log 2)))', 'data_wall': 'theorem data_wall {Ω State : Type} [MeasurableSpace Ω] [MeasurableSpace State] (μ : Measure Ω) [IsProbabilityMeasure μ] (X : Process Ω State) (O : Process Ω State) (τ : NNReal) (P T kB : NNReal) (ρ_max : ENNReal) (h_kB_pos : 0 < kB) (h_T_pos : 0 < T) (h_landauer : (P : ENNReal) ≥ intelligenceCreationRate μ X O τ * ENNReal.ofReal ((kB : ℝ) * (T : ℝ) * Real.log 2)) (hB : observationBandwidth μ O ≠ ⊤) (hRho_le_one : predictiveRichness μ X O τ ≤ 1) (h_rho_bound : predictiveRichness μ X O τ ≤ ρ_max) (h_data_limited : (P : ENNReal) ≥ criticalPower (predictiveRichness μ X O τ) (observationBandwidth μ O) T kB) : intelligenceCreationRate μ X O τ ≤ ρ_max * observationBandwidth μ O'}
RUN902_STATEMENT_SHA256 = 'd1c4ad2da4565b8087c6999e68fbe539007726afe9c6d388d1859d49a91273f8'
RUN902_CERTIFICATE_SHA256 = 'f8eae567b536fac4dba32456f448de99e7e59b1d2e14ecae2b7234ba92f1e130'
ALIGNER_SHA256 = 'd8d06e582d80bddae73dbb68a23a866ed8cac241f5c9780c3bc779a50fcd4870'
PRODUCT_CODE = re.compile(r'\bRun902_product_form_conditional\b|\b\w*product_form\w*\b|\bP\s*\*\s*D\s*\)*\s*/')
BOUND_CODE = re.compile(r'\b(?:Run90[012]\w*|intelligence_bound\w*|intelligenceCreationRate|'
                        r'observationBandwidth|predictiveRichness|data_wall|thermodynamic_bound_lemma|SatisfiesLandauerLimit)\b')
PRODUCT_PAPER = re.compile(r'product[\s-]*form|\\frac\s*\{\s*P\s*(?:\\cdot\s*|\\times\s*)?D\b|'
                          r'\bP\s*(?:\\cdot|\\times|\*)\s*D\s*(?:/|\\over)', re.I)


def _aligner():
    """Reuse the unchanged frozen-signature/comment parser at its exact path."""
    here = Path(__file__).resolve()
    paths = [here.parents[1]/'engine3_align_challenge.py', here.parents[2]/'comparator-deploy/engine3_align_challenge.py']
    matches = [path for path in paths if path.is_file()]
    if len(matches) != 1 or hashlib.sha256(matches[0].read_bytes()).hexdigest() != ALIGNER_SHA256:
        raise ValueError('unchanged pinned signature parser missing or ambiguous')
    spec = importlib.util.spec_from_file_location('_premise_existing_aligner', matches[0])
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def _normalize(text):
    return ' '.join(text.split())


def _binders(signature):
    result = {}
    for name in RUN902_PREMISES:
        matches = list(re.finditer(r'\(\s*'+name+r'\s*:', signature))
        if len(matches) != 1:
            continue
        start = matches[0].end(); depth = 1; end = start
        while end < len(signature) and depth:
            depth += (signature[end] == '(') - (signature[end] == ')')
            end += 1
        if depth:
            raise ValueError('unterminated premise binder')
        result[name] = _normalize(signature[start:end-1])
    return result


def _code(aligner, text):
    # String literals cannot satisfy an invocation or basis-reference check.
    return re.sub(r'"(?:\\.|[^"\\])*"', ' ', aligner.strip_comments(text))


def _global_assumptions(source):
    # Preserve continuation lines; section-level variables on the next line are
    # still global assumptions, not explicit theorem hypotheses.
    commands = r'theorem|lemma|def|abbrev|axiom|example|instance|structure|class|namespace|section|end|variable|variables|constant|constants|hypothesis|hypotheses|assumption|assumptions|set_option|open|import'
    return re.findall(r'(?ms)^\s*(?:variable|variables|constant|constants|hypothesis|hypotheses|assumption|assumptions)\b(.*?)(?=^\s*(?:'+commands+r')\b|\Z)', source)


def _main_text(text):
    regions = re.findall(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', text, re.S)
    regions += re.findall(r'\\begin\{(?:theorem|proposition|lemma)\}(.*?)\\end\{(?:theorem|proposition|lemma)\}', text, re.S)
    regions += re.findall(r'\\section\*?\{(?:Main [Rr]esults?|Main [Tt]heorem|Results)\}(.*?)(?=\\section|\\end\{document\})', text, re.S)
    return '\n'.join(regions)


def evaluate(manifest, inventory, *, formal_statement, candidate, paper_text, theorem_names, required=False):
    """Read-only check of sealed declarations; PASS is not a proof verdict.

    Historical absent fields are EXEMPT only when the caller has not enabled
    INV-9 for the explicitly recorded new-nightly cutover. Declared fields are
    always checked. Normalization removes Lean comments and collapses whitespace;
    it never renames variables or substitutes a supposedly equivalent premise.
    """
    result = {'standard': STANDARD, 'status': 'HOLD', 'foundation_basis': None,
              'reasons': [], 'findings': [], 'local_lean_execution': False, 'certifies': False}
    try:
        if not isinstance(manifest, dict) or not isinstance(inventory, dict):
            raise ValueError('sealed manifest and claim inventory must be JSON objects')
        values = [manifest.get('foundation_basis'), inventory.get('foundation_basis')]
        if values == [None, None] and not required:
            result.update(status='EXEMPT', historical_exemption=True)
            return result
        if any(not isinstance(value, str) or value not in BASES for value in values):
            result['reasons'].append('PREMISE_DECLARATION_MISSING_OR_UNKNOWN'); return result
        if values[0] != values[1]:
            result['reasons'].append('PREMISE_DECLARATION_MISMATCH'); return result
        basis = result['foundation_basis'] = values[0]
        if not isinstance(theorem_names, list) or not theorem_names or len(set(theorem_names)) != len(theorem_names):
            raise ValueError('exact nonempty certified theorem-name contract required')
        aligner = _aligner()
        source = _code(aligner, candidate); frozen = _code(aligner, formal_statement)
        if re.search(r'\b(?:axiom|sorry|admit|sorryAx|unsafe)\b|open\s+private', source) or re.search(r'\baxiom\b', frozen):
            result['reasons'].append('PREMISE_FORBIDDEN_AXIOM_OR_ESCAPE'); return result
        paper = re.sub(r'(?<!\\)%[^\n]*', '', paper_text)
        main = _normalize(_main_text(paper))
        product_used = bool(PRODUCT_CODE.search(source) or PRODUCT_CODE.search(frozen) or PRODUCT_PAPER.search(paper))
        if basis != 'CONDITIONAL_PL_PD' and product_used:
            result['reasons'].append('PREMISE_UNDERDECLARED'); return result
        if basis == 'INDEPENDENT':
            if BOUND_CODE.search(source) or BOUND_CODE.search(frozen) or re.search(r'intelligence\s+bound', paper, re.I):
                result['reasons'].append('PREMISE_UNDERDECLARED'); return result
            if 'INDEPENDENT' not in main:
                result['reasons'].append('PREMISE_BASIS_NOT_IN_MAIN_RESULT'); return result
        elif basis == 'THEOREM':
            # Names alone cannot establish the min-form/data-wall scope. A
            # restatement must match a certified frozen signature exactly.
            matched = []
            for reference, expected in RUN900_SIGNATURES.items():
                try:
                    actual = aligner.normalized_signature(candidate, reference)
                    frozen_actual = aligner.normalized_signature(formal_statement, reference)
                except ValueError:
                    continue
                if actual == expected and frozen_actual == expected:
                    matched.append(reference)
            if not matched:
                result['reasons'].append('PREMISE_THEOREM_REFERENCE_UNRESOLVED'); return result
            result['findings'].append({'exact_Run900_Run901_statements': matched})
            if 'THEOREM' not in main:
                result['reasons'].append('PREMISE_BASIS_NOT_IN_MAIN_RESULT'); return result
        else:
            # Section variables/global predicates cannot substitute for explicit
            # source binders. A proof may instead invoke the exact conditional
            # theorem with locally established arguments, as the invariant allows.
            if any(re.search(r'\bPL\b|\bPD\b|R_obs\s*\*\s*K|rate\s*≤\s*R_obs', block) for block in _global_assumptions(source)):
                result['reasons'].append('PREMISE_GLOBAL_ASSUMPTION'); return result
            for name in theorem_names:
                signature = aligner.normalized_signature(candidate, name)
                if signature != aligner.normalized_signature(formal_statement, name):
                    result['reasons'].append('PREMISE_STATEMENT_DRIFT'); return result
                start = aligner._declaration_start(source, name); assignment = aligner._assignment(source, start, name)
                proof = source[assignment.end():aligner._proof_end(source, assignment.end(), name)]
                explicit = _binders(signature) == RUN902_PREMISES
                invoked = re.search(r'(?<![\w.])(?:_root_\.)?'+RUN902_THEOREM+r'\b', proof) is not None
                if not explicit and not invoked:
                    result['findings'].append({'theorem': name, 'code': 'PREMISE_DROPPED'})
                    result['reasons'].append('PREMISE_DROPPED'); return result
                # Reuse only the exact frozen conditional declaration. An
                # unresolved imported name cannot be trusted from spelling.
                if invoked:
                    try:
                        exact = aligner.normalized_signature(candidate, RUN902_THEOREM) == RUN902_SIGNATURE
                        exact = exact and aligner.normalized_signature(formal_statement, RUN902_THEOREM) == RUN902_SIGNATURE
                    except ValueError:
                        exact = False
                    if not exact:
                        result['reasons'].append('PREMISE_CONDITIONAL_REFERENCE_UNRESOLVED'); return result
                result['findings'].append({'theorem': name, 'explicit_PL_PD': explicit, 'invokes_Run902': invoked})
            phrases = [CONDITIONAL_PHRASE]
            equivalents = inventory.get('premise_declaration', {}).get('approved_equivalents', [])
            if not isinstance(equivalents, list) or any(not isinstance(p, str) or not p.strip() or
                    not re.search(r'\bconditional\b', p, re.I) or not re.search(r'\bPL\b', p) or not re.search(r'\bPD\b', p) for p in equivalents):
                raise ValueError('inventory-approved equivalent must explicitly name conditional PL and PD')
            phrases += equivalents
            if not any(_normalize(p) in main for p in phrases):
                result['reasons'].append('PREMISE_BASIS_NOT_IN_MAIN_RESULT'); return result
            # Same claim paragraph is a conservative, reproducible definition of
            # near. A distant abstract disclaimer cannot qualify a body assertion.
            for paragraph in re.split(r'\n\s*\n', paper):
                if PRODUCT_PAPER.search(paragraph) and not any(_normalize(p) in _normalize(paragraph) for p in phrases):
                    result['reasons'].append('PREMISE_UNCONDITIONAL_PAPER_CLAIM'); return result
            for claim in inventory.get('claims', []):
                if not isinstance(claim, dict):
                    raise ValueError('sealed claim inventory entries must be objects')
                claim_text = str(claim.get('claim', claim.get('english_claim', '')))
                if PRODUCT_PAPER.search(claim_text) and not any(_normalize(p) in _normalize(claim_text) for p in phrases):
                    result['reasons'].append('PREMISE_UNCONDITIONAL_INVENTORY_CLAIM'); return result
            result['reference_contract'] = {'run_id': 'Run-902', 'theorem': RUN902_THEOREM,
                'premises': RUN902_PREMISES, 'statement_sha256': RUN902_STATEMENT_SHA256,
                'certificate_sha256': RUN902_CERTIFICATE_SHA256, 'normalization': 'unchanged aligner comment removal; whitespace collapse only'}
        result.update(status='PASS', historical_exemption=False)
    except Exception as exc:
        result['reasons'].append('PREMISE_INTAKE_ERROR: '+type(exc).__name__+': '+str(exc))
    return result


def _hold(exc):
    return {'standard': STANDARD, 'status': 'HOLD', 'foundation_basis': None,
            'reasons': ['PREMISE_INTAKE_ERROR: '+type(exc).__name__+': '+str(exc)],
            'findings': [], 'local_lean_execution': False, 'certifies': False}


def validate_envelope(request_path, formal_path, candidate_path, *, required=False):
    try:
        request_path = Path(request_path); request = json.loads(request_path.read_text())
        folder = request_path.parent
        targets = [name for name in request['expected_theorem_names'] if name not in request.get('nonvacuity_obligations', [])]
        return evaluate(json.loads((folder/'SEALED_RUN_MANIFEST.json').read_text()),
            json.loads((folder/'SEALED_CLAIM_INVENTORY.json').read_text()),
            formal_statement=Path(formal_path).read_text(), candidate=Path(candidate_path).read_text(),
            paper_text=(folder/'SEALED_paper.tex').read_text(), theorem_names=targets, required=required)
    except Exception as exc:
        return _hold(exc)


def validate_artifact(artifact, inspection, certificate, root, *, required=False):
    """Consume current hash-bound sealed inputs; check final paper and cert metadata.

    Historical issued sealed contracts may lack the manifest/inventory. They are
    exempt only with no declared basis and no explicit new-run requirement.
    """
    from certificate_inspection import resolve_binding
    try:
        if inspection.get('valid') is not True:
            raise ValueError('current valid proof-certificate inspection required')
        root = Path(root).resolve(); artifact = Path(artifact).resolve(); certificate = Path(certificate).resolve()
        if not artifact.is_relative_to(root) or not certificate.is_relative_to(root):
            raise ValueError('premise inputs outside mirror/certification root')
        cert = json.loads(certificate.read_text())
        bindings = cert.get('bindings', {})
        sealed = bindings.get('sealed_paper_inputs', inspection.get('sealed_paper_inputs', {}))
        documents = []
        for name in ('SEALED_RUN_MANIFEST.json', 'SEALED_CLAIM_INVENTORY.json'):
            if name not in sealed:
                if required or 'foundation_basis' in cert:
                    raise ValueError('required sealed premise input missing: '+name)
                documents.append({})
            else:
                documents.append(json.loads(resolve_binding(sealed[name], root).read_text()))
        if all(isinstance(doc, dict) and 'foundation_basis' not in doc for doc in documents) and not required and 'foundation_basis' not in cert:
            return evaluate(*documents, formal_statement='', candidate='', paper_text='', theorem_names=[], required=False)
        final = list(artifact.glob('*.tex'))
        if len(final) != 1 or final[0].is_symlink():
            raise ValueError('one regular final TeX required')
        result = evaluate(*documents,
            formal_statement=resolve_binding(bindings['formal_statement'], root).read_text(),
            candidate=resolve_binding(bindings['candidate_proof'], root).read_text(),
            paper_text=final[0].read_text(),
            theorem_names=[name for name in inspection['certified_theorems'] if name not in inspection.get('nonvacuity', [])], required=required)
        if result['status'] == 'PASS' and cert.get('foundation_basis') != result['foundation_basis']:
            result.update(status='HOLD'); result['reasons'].append('PREMISE_CERTIFICATE_BASIS_MISMATCH')
        elif result['status'] == 'EXEMPT' and 'foundation_basis' in cert:
            result.update(status='HOLD'); result['reasons'].append('PREMISE_CERTIFICATE_BASIS_MISMATCH')
        return result
    except Exception as exc:
        return _hold(exc)
