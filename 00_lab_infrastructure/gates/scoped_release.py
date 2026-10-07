"""Consume an independently reviewed narrowed manuscript, never verify Lean.

Phase 7 permits manuscript narrowing, not changes to a frozen proof contract.
Drafts remain HOLD until Claude's exact-hash scope/PDF review is approved in the
SSOT. This module has no network or publication transport.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
from pathlib import Path

from certificate_inspection import inspect_certificate, resolve_binding
from claim_binding import _names, _one_name
from theorem_coverage import triviality
from static_pregate import scan, code_only
from scoped_statement_text import signature_parts, inline_unicode_escape

STANDARD = 'VRS-SCOPED-RELEASE-1'
REVIEW_STANDARD = 'VRS-SCOPED-RELEASE-REVIEW-1'
REVIEW_SCOPE = 'EXACT_CERTIFIED_SCOPE_NARROWING'
DISCLAIMER = 'logical validity given the model, not empirical validation of its assumptions'
REVIEW_CHECKS = (
    'whole_paper_claim_completeness', 'all_explicit_and_ambient_hypotheses_retained',
    'no_statement_stronger_than_certified', 'model_fidelity_reviewed',
    'nonvacuity_correspondence_reviewed', 'triviality_reviewed',
    'original_unproven_claims_explicitly_uncertified', 'pdf_tex_correspondence_reviewed',
    'foundation_basis_reviewed', 'no_empirical_validation_implied',
    'metadata_claim_completeness',
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _object(path):
    path = Path(path)
    if path.is_symlink():
        raise ValueError('symlink refused: '+str(path))
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError('JSON object required')
    return value


def _time(value):
    t = dt.datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    if t.tzinfo is None:
        raise ValueError('timezone required')
    return t


def _local_file(artifact, value):
    if not isinstance(value, dict) or set(value) != {'filename', 'sha256'}:
        raise ValueError('filename and SHA-256 required')
    name = value['filename']
    if not isinstance(name, str) or not name or Path(name).name != name:
        raise ValueError('one local basename required')
    path = artifact/name
    if path.is_symlink() or not path.is_file() or sha(path) != value['sha256']:
        raise ValueError('exact local file binding failed: '+name)
    return path


def _display_file(artifact, value, tex_text, expected_text):
    """Consume an exact rendered attachment; this does not validate a PDF."""
    if not isinstance(value, dict) or set(value) != {'relative_path', 'sha256'}:
        raise ValueError('exact context/statement display file required')
    rel = Path(value['relative_path'])
    shown = artifact/rel
    if (rel.is_absolute() or '..' in rel.parts or shown.is_symlink()
            or not shown.resolve(strict=True).is_relative_to(artifact)
            or sha(shown) != value['sha256']):
        raise ValueError('context/statement display identity mismatch')
    # Preserve the existing Wave B rendering bytes. Exact UTF-8 proof inputs
    # and the independent PDF correspondence review remain authoritative.
    from science_release_stage import ascii_render
    if shown.read_text() != ascii_render(expected_text):
        raise ValueError('rendered context/statement differs from frozen source')
    if not re.search(r'\\VerbatimInput(?:\[[^\]]*\])?\{'+re.escape(str(rel))+r'\}', tex_text):
        raise ValueError('bound context/statement display not included in final TeX')
    return shown


def _inline_present(text, tex_text):
    normalize = lambda s: ' '.join(s.split())
    return any(normalize(v) in normalize(tex_text)
               for v in (text, inline_unicode_escape(text)))


def ambient_context(source, target_line):
    """Conservative live section-variable text, not an elaborated Lean type."""
    code = code_only(source)
    commands = list(re.finditer(r'(?m)^\s*(?:@\[[^\n]*\]\s*)?(?:(?:private|protected|noncomputable)\s+)*(theorem|lemma|def|abbrev|structure|instance|example|namespace|section|end|variable|variables|open|import|set_option|attribute)\b', code))
    frames = [[]]
    for i, match in enumerate(commands):
        line = code.count('\n', 0, match.start())+1
        if line >= target_line:
            break
        end = commands[i+1].start() if i+1 < len(commands) else len(code)
        if match[1] in {'namespace', 'section'}:
            frames.append([])
        elif match[1] == 'end':
            if len(frames) > 1:
                frames.pop()
        elif match[1] in {'variable', 'variables'}:
            frames[-1].append({'line': line, 'source_text': code[match.start():end].strip()})
    return [row for frame in frames for row in frame]


def assess(artifact, root, *, inspector=None, reviewed_witness_assignments=None):
    """Read-only draft checks; never grants acceptance or publishing authority."""
    result = {'standard': STANDARD, 'status': 'HOLD', 'reasons': [],
              'local_lean_execution': False, 'certifies': False, 'zenodo_writes': False}
    try:
        artifact, root = Path(artifact).resolve(strict=True), Path(root).resolve(strict=True)
        if not artifact.is_relative_to(root):
            raise ValueError('release outside mirror/certification root')
        mp = artifact/'SCOPED_RELEASE_MANIFEST.json'
        snapshots = {}
        def snapshot(path, expected=None):
            path = Path(path)
            if path.is_symlink():
                raise ValueError('snapshot symlink refused')
            digest = sha(path)
            if expected is not None and digest != expected:
                raise ValueError('snapshot hash mismatch: '+str(path))
            if path in snapshots and snapshots[path] != digest:
                raise ValueError('evidence changed during assessment: '+str(path))
            snapshots[path] = digest
            return digest
        snapshot(mp)
        manifest = _object(mp)
        if manifest.get('standard') != STANDARD or manifest.get('scope') != REVIEW_SCOPE:
            raise ValueError('unknown scope contract')
        certificate = resolve_binding(manifest['certificate'], root)
        snapshot(certificate, manifest['certificate']['sha256'])
        cert = _object(certificate)
        # Capture the existing consumer's complete bound input family before
        # inspection, then require the same bytes at the end of this read.
        def snapshot_bindings(value):
            if isinstance(value, dict):
                if 'path' in value:
                    snapshot(resolve_binding(value, root), value.get('sha256'))
                else:
                    for child in value.values():
                        snapshot_bindings(child)
        snapshot_bindings(cert['bindings'])
        candidate_before = resolve_binding(cert['bindings']['candidate_proof'], root)
        formal = resolve_binding(cert['bindings']['formal_statement'], root)
        inspection = (inspector or inspect_certificate)(certificate, root)
        if inspection.get('valid') is not True or inspection.get('run_id') != manifest.get('run_id'):
            raise ValueError('existing certificate consumer did not validate this Run')
        candidate = Path(inspection['candidate_path']).resolve(strict=True)
        if (candidate != candidate_before or inspection.get('sha256') != snapshots[certificate]
                or inspection.get('candidate_sha256') != snapshots[candidate]):
            raise ValueError('inspection snapshot identity mismatch')
        snapshot(certificate, manifest['certificate']['sha256'])
        snapshot(candidate, cert['bindings']['candidate_proof']['sha256'])
        snapshot(formal, cert['bindings']['formal_statement']['sha256'])
        if manifest.get('candidate') != {'path': str(candidate), 'sha256': snapshots[candidate]}:
            raise ValueError('candidate identity mismatch')
        if manifest.get('formal_statement') != {'path': str(formal), 'sha256': snapshots[formal]}:
            raise ValueError('frozen statement identity mismatch')
        candidate_text, formal_text = candidate.read_text(), formal.read_text()
        if scan(candidate).get('static_pass') is not True:
            raise ValueError('existing static gate did not pass')
        source_map = _local_file(artifact, manifest['claim_map'])
        scope = _local_file(artifact, manifest['statement_inventory'])
        snapshot(source_map, manifest['claim_map']['sha256'])
        snapshot(scope, manifest['statement_inventory']['sha256'])
        mapping, inventory = _object(source_map), _object(scope)
        if mapping.get('run_id') != manifest['run_id'] or inventory.get('run_id') != manifest['run_id']:
            raise ValueError('claim map/statement inventory Run identity mismatch')
        basis_file = _local_file(artifact, manifest['foundation_basis'])
        snapshot(basis_file, manifest['foundation_basis']['sha256'])
        basis = _object(basis_file)
        # A fresh declaration supplements a historical certificate; it never
        # edits the certificate's sealed premise metadata or discharges PL/PD.
        if basis.get('foundation_basis') not in {'INDEPENDENT', 'THEOREM', 'CONDITIONAL_PL_PD'}:
            raise ValueError('unknown INV-9 basis')
        if 'foundation_basis' in cert and cert['foundation_basis'] != basis['foundation_basis']:
            raise ValueError('issued certificate basis disagrees')
        uploads = manifest.get('uploads')
        if not isinstance(uploads, list) or not uploads:
            raise ValueError('nonempty exact upload inventory required')
        names = [v.get('filename') for v in uploads if isinstance(v, dict)]
        if len(names) != len(uploads) or len(set(names)) != len(names):
            raise ValueError('duplicate or malformed upload name')
        paths = [_local_file(artifact, v) for v in uploads]
        for path, value in zip(paths, uploads):
            snapshot(path, value['sha256'])
        for key in ('claim_map','statement_inventory','foundation_basis'):
            # Reviewed scope evidence must be delivered, not merely retained
            # locally. Exact filenames avoid substituting equal-byte aliases.
            if manifest[key] not in uploads:
                raise ValueError('exact reviewed '+key+' public upload missing')
        metadata_paths=[artifact/name for name in ('zenodo_metadata.json','metadata.json')
            if (artifact/name).exists() or (artifact/name).is_symlink()]
        if len(metadata_paths)>1:raise ValueError('ambiguous public metadata files')
        metadata_binding=None
        if metadata_paths:
            path=metadata_paths[0]
            matches=[v for v in uploads if v.get('filename')==path.name]
            if len(matches)!=1 or _local_file(artifact,matches[0])!=path:
                raise ValueError('exact public metadata upload missing')
            snapshot(path,matches[0]['sha256']);_object(path)
            metadata_binding=matches[0]
        for bound in (certificate, candidate, formal):
            if not any(snapshots[path] == snapshots[bound]
                       and path.read_bytes() == bound.read_bytes() for path in paths):
                raise ValueError('exact raw certificate/candidate/statement upload missing')
        if sorted(p.suffix for p in paths if p.suffix in {'.tex', '.pdf'}) != ['.pdf', '.tex']:
            raise ValueError('one final PDF and one final TeX required')
        tex = next(p for p in paths if p.suffix == '.tex')
        tex_text = tex.read_text()
        if DISCLAIMER not in tex_text:
            raise ValueError('printed INV-4 disclaimer missing')
        if manifest.get('final_tex_sha256') != sha(tex):
            raise ValueError('final TeX identity mismatch')
        pdf = next(p for p in paths if p.suffix == '.pdf')
        if manifest.get('final_pdf_sha256') != sha(pdf):
            raise ValueError('final PDF identity mismatch')
        theorem_names = _names(inspection['certified_theorems'], 'certified theorem contract')
        witness_names = _names(inspection['nonvacuity'], 'nonvacuity contract')
        coverage = triviality(candidate_text)
        claims = manifest.get('statement_scope')
        if not isinstance(claims, list) or not claims:
            raise ValueError('exact nonempty statement scope required')
        claim_names = {_one_name(v.get('lean_theorem'), theorem_names, 'lean_theorem')
                       for v in claims}
        if reviewed_witness_assignments is not None:
            if (not isinstance(reviewed_witness_assignments, dict)
                    or set(reviewed_witness_assignments)-claim_names):
                raise ValueError('reviewed nonvacuity assignments contain unbound targets')
        mapped = mapping.get('claims')
        declarations = inventory.get('declarations')
        if not isinstance(mapped, list) or not isinstance(declarations, list):
            raise ValueError('explicit map claims and inventory declarations required')
        if (any(not isinstance(v, dict) for v in mapped+declarations)
                or len({v.get('lean_theorem') for v in mapped}) != len(mapped)
                or len({v.get('lean_theorem') for v in declarations}) != len(declarations)):
            raise ValueError('malformed or duplicate claim map')
        seen, english_seen, checked = set(), set(), []
        for claim in claims:
            name = _one_name(claim.get('lean_theorem'), theorem_names, 'lean_theorem')
            if name in seen:
                raise ValueError('theorem bound more than once')
            seen.add(name)
            english = claim.get('english_claim')
            if not isinstance(english, str) or not english.strip() or english in english_seen:
                raise ValueError('one nonempty unique English claim required')
            english_seen.add(english)
            matching_claims = [v for v in mapped if v.get('lean_theorem') == name]
            matching_declarations = [v for v in declarations if v.get('lean_theorem') == name]
            if len(matching_claims) != 1 or len(matching_declarations) != 1:
                raise ValueError('scope claim needs one map and inventory record')
            if matching_claims[0].get('english_claim') != english:
                raise ValueError('claim map English scope differs from manifest')
            for key in ('model_fidelity', 'evidence_class', 'nonvacuity_obligation'):
                if (key not in matching_claims[0] or key not in claim
                        or matching_claims[0][key] != claim[key]):
                    raise ValueError('claim map scope differs from manifest: '+key)
            declaration = coverage.get(name)
            if not declaration or claim.get('exact_source_signature') != declaration['signature']:
                raise ValueError('printed signature differs from frozen candidate')
            if matching_declarations[0].get('exact_source_signature') != declaration['signature']:
                raise ValueError('inventory hypothesis/conclusion differs from frozen source')
            context = ambient_context(candidate_text, declaration['line'])
            if claim.get('ambient_source_context') != context:
                raise ValueError('live ambient hypotheses omitted or changed')
            documented = matching_declarations[0]
            binders, conclusion = signature_parts(declaration['signature'])
            if (documented.get('ambient_source_context') != context
                    or documented.get('explicit_binders_and_hypotheses') != binders
                    or documented.get('conclusion') != conclusion):
                raise ValueError('inventory context/hypothesis/conclusion documentation differs')
            from premise_declaration import _aligner
            aligner = _aligner()
            if aligner.normalized_signature(candidate_text, name) != aligner.normalized_signature(formal_text, name):
                raise ValueError('frozen aligned statement differs')
            witness = claim.get('nonvacuity_obligation')
            if witness is None:
                if not isinstance(reviewed_witness_assignments, dict):
                    raise ValueError('per-claim nonvacuity assignment awaiting independent review')
                witness = reviewed_witness_assignments.get(name)
            witness = _one_name(witness, witness_names, 'nonvacuity obligation')
            if reviewed_witness_assignments is not None and name in reviewed_witness_assignments:
                if _one_name(reviewed_witness_assignments[name], witness_names, 'review nonvacuity obligation') != witness:
                    raise ValueError('review nonvacuity conflicts with explicit assignment')
            documented_witness = documented.get('nonvacuity_obligation')
            if 'nonvacuity_obligation' not in documented:
                raise ValueError('inventory explicit nonvacuity field missing')
            if documented_witness is not None and _one_name(documented_witness, witness_names, 'inventory nonvacuity obligation') != witness:
                raise ValueError('inventory nonvacuity differs from scoped assignment')
            classification = declaration['classification']
            evidence = claim.get('evidence_class')
            if classification == 'CERTIFIED_TRIVIAL' and evidence != 'CERTIFIED_TRIVIAL':
                raise ValueError('trivial theorem cannot carry FORMALLY_VERIFIED')
            if classification == 'TRIVIALITY_UNRESOLVED':
                raise ValueError('existing triviality consumer requires further review')
            if evidence not in {'FORMALLY_VERIFIED', 'CERTIFIED_TRIVIAL'}:
                raise ValueError('unknown release evidence class')
            fidelity = claim.get('model_fidelity')
            if not isinstance(fidelity, dict):
                raise ValueError('model fidelity required')
            defined, empirical = fidelity.get('defined'), fidelity.get('empirically_identified')
            if (not isinstance(defined, list) or not defined or not isinstance(empirical, list)
                    or any(not isinstance(v, str) or not v.strip() for v in defined+empirical)
                    or len(set(defined+empirical)) != len(defined+empirical)):
                raise ValueError('exact disjoint model symbol lists required')
            # These packages deliberately make no empirical symbol identification.
            if empirical:
                raise ValueError('empirical identification exceeds narrowed model-only scope')
            display = claim.get('display_file')
            if display is not None:
                shown = _display_file(artifact, display, tex_text, declaration['signature'])
                snapshot(shown, display['sha256'])
            else:
                # Inline Unicode escapes are injective display bytes, never a
                # replacement for the exact UTF-8 proof inputs.
                if not _inline_present(declaration['signature'], tex_text):
                    raise ValueError('printed paper omits a frozen hypothesis/conclusion')
            context_display = claim.get('context_display_file')
            if context_display is not None:
                shown = _display_file(artifact, context_display, tex_text, formal_text)
                snapshot(shown, context_display['sha256'])
            elif any(not _inline_present(row['source_text'], tex_text) for row in context):
                raise ValueError('printed paper omits a live ambient hypothesis/context')
            checked.append({'lean_theorem': name, 'nonvacuity_obligation': witness,
                            'evidence_class': evidence})
        if {v.get('lean_theorem') for v in mapped} != seen:
            raise ValueError('claim map contains unbound or missing scope statements')
        if {v.get('lean_theorem') for v in declarations} != seen:
            raise ValueError('inventory contains unbound or missing scope statements')
        from premise_declaration import evaluate
        inv9_inputs = {'foundation_basis': basis['foundation_basis']}
        inv9_claims = {**inv9_inputs, 'claims': [{'claim': v.get('english_claim', ''),
                       'lean_theorem': v['lean_theorem']} for v in claims]}
        args = dict(formal_statement=formal_text, candidate=candidate_text,
                    theorem_names=[v['lean_theorem'] for v in claims], required=True)
        full_inv9 = evaluate(inv9_inputs, inv9_claims, paper_text=tex_text, **args)
        projection_sha = None
        actual = full_inv9
        if full_inv9.get('status') != 'PASS':
            # Phase 7 permits explicitly uncertified archival remarks. A
            # projection is only draft evidence until independent whole-paper
            # review approves its exact hash; the full unchanged Lean source
            # still goes through the existing INV-9 consumer in both calls.
            if full_inv9.get('reasons') != ['PREMISE_UNDERDECLARED']:
                raise ValueError('full-paper INV-9 failed outside archival wording')
            projection_path = _local_file(artifact, manifest['inv9_projection'])
            snapshot(projection_path, manifest['inv9_projection']['sha256'])
            projection = _object(projection_path)
            if projection.get('final_tex_sha256') != sha(tex) or projection.get('rule') != 'AUDITED_UNCERTIFIED_ARCHIVE_EXCLUSION':
                raise ValueError('INV-9 projection not bound to this manuscript')
            if not isinstance(projection.get('paper_text'), str) or not projection['paper_text']:
                raise ValueError('nonempty certified-main projection required')
            projection_sha = sha(projection_path)
            actual = evaluate(inv9_inputs, inv9_claims, paper_text=projection['paper_text'], **args)
        if actual.get('status') != 'PASS' or actual.get('foundation_basis') != basis['foundation_basis']:
            raise ValueError('fresh existing INV-9 evaluation did not pass')
        for path, digest in snapshots.items():
            if sha(path) != digest:
                raise ValueError('evidence changed during assessment: '+str(path))
        result.update(status='DRAFT_CHECKS_PASS_NOT_PUBLICATION_BOUND', manifest_sha256=snapshots[mp],
                      certificate={'path': str(certificate), 'sha256': snapshots[certificate]},
                      candidate=manifest['candidate'], formal_statement=manifest['formal_statement'],
                      claim_map_sha256=snapshots[source_map], statement_inventory_sha256=snapshots[scope],
                      foundation_basis_sha256=snapshots[basis_file], uploads=uploads,
                      metadata_binding=metadata_binding,
                      final_tex_sha256=snapshots[tex], final_pdf_sha256=snapshots[pdf],
                      statement_scope=checked, foundation_basis=basis['foundation_basis'],
                      inv9_projection_sha256=projection_sha,
                      archival_exclusion_review_required=projection_sha is not None,
                      fresh_full_inv9=full_inv9, fresh_scoped_inv9=actual)
    except Exception as exc:
        result['reasons'].append(type(exc).__name__+': '+str(exc))
    return result


def validate_review(artifact, root, approved_review_hashes, *, inspector=None, now=None):
    """Require SSOT-approved independent evidence for every exact narrowed byte."""
    root, artifact = Path(root).resolve(), Path(artifact).resolve()
    review_path = artifact/'SCOPED_RELEASE_REVIEW.json'
    digest = sha(review_path)
    review = _object(review_path)
    if (not isinstance(approved_review_hashes, list) or digest not in approved_review_hashes):
        raise ValueError('scope review has no SSOT hash approval')
    if review.get('standard') != REVIEW_STANDARD or review.get('scope') != REVIEW_SCOPE or review.get('status') != 'APPROVED':
        raise ValueError('independent scope review not approved')
    reviewer = review.get('reviewer')
    if (not isinstance(reviewer, dict) or not isinstance(reviewer.get('identity'), str)
            or not reviewer['identity'].startswith('Claude')
            or not isinstance(reviewer.get('model'), str) or not reviewer['model'].startswith('claude-')):
        raise ValueError('independent Claude reviewer provenance required')
    if any(review.get('checks', {}).get(k) is not True for k in REVIEW_CHECKS):
        raise ValueError('independent scope/PDF review incomplete')
    current = assess(artifact, root, inspector=inspector,
                     reviewed_witness_assignments=review.get('nonvacuity_assignments'))
    if current['status'] != 'DRAFT_CHECKS_PASS_NOT_PUBLICATION_BOUND':
        raise ValueError('scope draft HOLD: '+'; '.join(current['reasons']))
    for key in ('manifest_sha256', 'certificate', 'candidate', 'formal_statement',
                'claim_map_sha256', 'statement_inventory_sha256', 'foundation_basis_sha256',
                'uploads', 'final_tex_sha256', 'final_pdf_sha256', 'statement_scope', 'foundation_basis',
                'inv9_projection_sha256', 'archival_exclusion_review_required'):
        if review.get(key) != current[key]:
            raise ValueError('review identity mismatch: '+key)
    if current['archival_exclusion_review_required'] and review.get('checks', {}).get('all_excluded_regions_explicitly_uncertified') is not True:
        raise ValueError('archival exclusion has no independent whole-paper approval')
    issued = _time(_object(current['certificate']['path'])['issued_at_utc'])
    reviewed = _time(review.get('reviewed_at_utc'))
    if not issued <= reviewed <= (now or dt.datetime.now(dt.timezone.utc)):
        raise ValueError('scope review chronology invalid')
    if sha(review_path) != digest:
        raise ValueError('independent review changed during assessment')
    return {**current, 'status': 'AUDITED_SCOPE_READY_FOR_PUBLICATION_TIME_BINDING',
            'review': {'path': str(review_path), 'sha256': digest},
            'publication_authorized': False,
            'metadata_claim_completeness': review['checks']['metadata_claim_completeness']}


def require_publication_bound(artifact, root=None, approved_review_hashes=None, *, inspector=None, now=None):
    """Fresh receipt round trip, never a caller's self-declared boolean PASS."""
    if isinstance(artifact, dict) or root is None or approved_review_hashes is None:
        raise ValueError('actual artifact, SSOT approvals and exact receipt required')
    current = validate_review(artifact, root, approved_review_hashes, inspector=inspector, now=now)
    receipt = _object(Path(artifact)/'PUBLICATION_BINDING.json')
    if receipt.get('standard') != 'VRS-SCOPED-PUBLICATION-BINDING-1' or receipt.get('status') != 'PUBLICATION_BOUND':
        raise ValueError('publish-time exact PUBLICATION_BINDING required; no write permitted')
    for key in ('manifest_sha256', 'certificate', 'candidate', 'formal_statement', 'claim_map_sha256',
                'statement_inventory_sha256', 'foundation_basis_sha256', 'uploads',
                'final_tex_sha256', 'final_pdf_sha256', 'statement_scope', 'foundation_basis', 'review'):
        if receipt.get(key) != current[key]:
            raise ValueError('publish-time receipt identity mismatch: '+key)
    reviewed = _time(_object(current['review']['path'])['reviewed_at_utc'])
    if not reviewed <= _time(receipt.get('issued_at_utc')) <= (now or dt.datetime.now(dt.timezone.utc)):
        raise ValueError('publication binding chronology invalid')
    return {**current, 'status': 'PUBLICATION_BOUND', 'exact_publication_binding': True}
