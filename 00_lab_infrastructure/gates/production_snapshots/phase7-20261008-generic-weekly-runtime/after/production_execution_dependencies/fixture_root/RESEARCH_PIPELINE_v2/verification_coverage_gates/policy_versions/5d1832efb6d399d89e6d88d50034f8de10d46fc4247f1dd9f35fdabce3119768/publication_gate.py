#!/usr/bin/env python3
"""Stage publication labels from the ledger; report-only unless --enforce is set.

This consumer cannot issue certificates or amend a published DOI. Certificate
proof status and claim publication eligibility are deliberately separate.
"""
from __future__ import annotations

import methods_digest_registration

import argparse
from copy import deepcopy
import hashlib
import html
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable

from publication_binding import validate_publication_binding
from release_packet import LABEL as UNCERTIFIED_LABEL, SEPARATOR

from claim_binding import (CONJECTURE_LABEL, DISCLAIMER, check_run, find_entity,
                           inspect_entity_certificate, read_object, tree_root)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _artifact_bindings(artifact: Path, inspection: dict[str, Any]) -> list[dict[str, str]]:
    inputs = inspection.get("sealed_paper_inputs")
    if not isinstance(inputs, dict):
        raise ValueError("certificate lacks sealed paper input bindings")
    paper_bindings = {name: value for name, value in inputs.items() if name in {"SEALED_paper.pdf", "SEALED_paper.tex"}}
    if not paper_bindings:
        raise ValueError("certificate has no sealed paper to bind this artifact")
    files = [path for path in artifact.iterdir() if path.is_file() and path.suffix.lower() in {".pdf", ".tex"}]
    if not files:
        raise ValueError("artifact directory contains no certifiable paper bytes")
    checked = []
    for file in files:
        expected = [binding for name, binding in paper_bindings.items()
                    if Path(name).suffix.lower() == file.suffix.lower()]
        if not expected:
            raise ValueError(f"artifact {file.name} has no certificate binding")
        digest = sha256(file)
        matching = [value for value in expected if isinstance(value, dict) and value.get("sha256") == digest]
        if len(matching) != 1:
            raise ValueError(f"artifact bytes differ from certified sealed input: {file.name}")
        checked.append({"path": str(file.resolve()), "sha256": digest})
    return checked


class PublicationGateHold(ValueError):
    """A new artifact cannot be released under the explicit enforcing flag."""


def _uncertified_description(description: str) -> str:
    """Stamp one current status while preserving historical claims and the title."""
    historical = description
    while True:
        match = re.match(r"\s*<p>\s*<strong>(.*?)</strong>\s*</p>", historical, re.S)
        if match and html.unescape(match.group(1)).strip() == UNCERTIFIED_LABEL:
            tail = historical[match.end():]
            separator = re.match(r"\s*(?:<hr\s*/?>\s*)?<p>\s*<strong>Historical description \(verification assertions below are not current certification labels\):</strong>\s*</p>\s*", tail, re.S)
            if separator is None:
                raise ValueError("existing UNCERTIFIED label lacks its historical separator")
            historical = tail[separator.end():]
            continue
        stripped = historical.lstrip()
        # Remove only former leading gate banners; never rewrite scientific prose.
        if stripped.startswith(CONJECTURE_LABEL):
            historical = stripped[len(CONJECTURE_LABEL):].lstrip(" \r\n")
            continue
        if stripped.startswith(DISCLAIMER):
            historical = stripped[len(DISCLAIMER):].lstrip(" \r\n")
            continue
        break
    return '<p><strong>' + html.escape(UNCERTIFIED_LABEL, quote=False) + '</strong></p>' + SEPARATOR + historical



SCOPED_HISTORICAL_SEPARATOR = ('<hr><p><strong>Historical metadata — UNCERTIFIED provenance: '
    'the title, description, abstract and keywords below are archival and are not part '
    'of the certified scope.</strong></p><pre>')
SCOPED_HISTORY_FIELDS = {'title','description','abstract','keywords'}


def _scoped_metadata_prefix(scope: dict[str, Any]) -> str:
    """Closed public statement; no free-form scientific prose is affirmative."""
    from scoped_release import DISCLAIMER as SCOPED_DISCLAIMER
    claims=scope.get('statement_scope',scope.get('claim_gate',{}).get('claims'))
    basis=scope.get('foundation_basis')
    if (not isinstance(claims,list) or not claims or basis not in {'INDEPENDENT','THEOREM','CONDITIONAL_PL_PD'}
            or any(not isinstance(v,dict)or not isinstance(v.get('lean_theorem'),str)
                   or not v['lean_theorem'] for v in claims)):
        raise ValueError('exact scope theorem names and declared basis required')
    names=[v['lean_theorem']for v in claims]
    if len(set(names))!=len(names):raise ValueError('duplicate public scope theorem name')
    label='SCOPED CERTIFIED — mathematical claims: '+', '.join(names)
    return ('<p><strong>'+html.escape(label,quote=False)+'</strong></p>'
        +'<p>'+html.escape(SCOPED_DISCLAIMER,quote=False)+'</p>'
        +'<p>Foundation basis: '+html.escape(basis,quote=False)+'.</p>')


def _encode_scoped_history(historical: dict[str, Any]) -> str:
    return html.escape(json.dumps(historical,ensure_ascii=False,sort_keys=True,indent=2),quote=False)


def _validate_closed_scoped_metadata(metadata: dict[str, Any], scope: dict[str, Any]) -> dict[str, Any]:
    """Require final reviewed bytes; this never repairs a publish payload."""
    if not isinstance(metadata.get('title'),str) or not metadata['title'].strip():
        raise ValueError('exact preserved nonempty public title required')
    description=metadata.get('description')
    prefix=_scoped_metadata_prefix(scope)
    if not isinstance(description,str) or not description.startswith(prefix):
        raise ValueError('final metadata description is not the closed reviewed scoped statement')
    tail=description[len(prefix):]
    historical={}
    if tail:
        if not tail.startswith(SCOPED_HISTORICAL_SEPARATOR) or not tail.endswith('</pre>'):
            raise ValueError('unqualified text outside the closed historical metadata archive')
        encoded=tail[len(SCOPED_HISTORICAL_SEPARATOR):-len('</pre>')]
        historical=json.loads(html.unescape(encoded))
        if (not isinstance(historical,dict) or not historical
                or not set(historical).issubset(SCOPED_HISTORY_FIELDS)
                or _encode_scoped_history(historical)!=encoded):
            raise ValueError('historical metadata must be one canonical escaped JSON archive')
        if any(not isinstance(historical[k],str)for k in ('title','description','abstract')if k in historical):
            raise ValueError('historical textual metadata must be strings')
        if 'keywords'in historical and (not isinstance(historical['keywords'],list)
                or any(not isinstance(k,str)for k in historical['keywords'])):
            raise ValueError('historical keywords must be strings')
    for key in ('title','keywords'):
        if (key in metadata)!= (key in historical) or (key in metadata and metadata[key]!=historical[key]):
            raise ValueError('final '+key+' differs from preserved historical metadata')
    if 'abstract'in metadata and metadata['abstract']!=description:
        raise ValueError('final scoped abstract must equal the exact closed description')
    if description!=prefix+(SCOPED_HISTORICAL_SEPARATOR+_encode_scoped_history(historical)+'</pre>'if historical else ''):
        raise ValueError('final scoped description is not canonical')
    return historical


def scoped_metadata_proposal(before: dict[str, Any], scope: dict[str, Any]) -> dict[str, Any]:
    """Report-only before→safe-after constructor; no PASS, receipt or writes.

    Freeze this proposal's exact metadata file and obtain a fresh independent
    review and publication binding before invoking the publication gate. Already
    canonical metadata is returned unchanged, never nested as its own history.
    """
    if not isinstance(before,dict):raise ValueError('original metadata object required')
    proposal=deepcopy(before)
    if isinstance(before.get('description'),str) and before['description'].startswith(_scoped_metadata_prefix(scope)):
        _validate_closed_scoped_metadata(before,scope)
        return proposal
    historical={key:deepcopy(before[key])for key in ('title','description','abstract','keywords')if key in before}
    description=_scoped_metadata_prefix(scope)
    if historical:description+=SCOPED_HISTORICAL_SEPARATOR+_encode_scoped_history(historical)+'</pre>'
    proposal['description']=description
    if 'abstract'in proposal:proposal['abstract']=description
    _validate_closed_scoped_metadata(proposal,scope)
    return proposal


def require_new_artifact_publication(result: dict[str, Any]) -> None:
    """Check release eligibility only; this grants no remote-write authority."""
    if result.get("enforcement") is not True or result.get("mode") != "ENFORCING":
        raise PublicationGateHold("new-artifact release requires explicit enforcing mode")
    if result.get("status") != "PASS" or result.get("exact_publication_binding") is not True:
        raise PublicationGateHold("new-artifact publication HOLD: " + "; ".join(result.get("reasons", [])))


def _premise_required(ledger: dict[str, Any], entity: dict[str, Any], explicit: bool) -> bool:
    if type(explicit) is not bool:
        raise ValueError('premise-declaration requirement must be an explicit boolean')
    if explicit:
        return True
    cutover = ledger.get('premise_declaration_cutover_run')
    if cutover is None:
        return False
    if not isinstance(cutover, str) or re.fullmatch(r'Run-[0-9]+', cutover) is None:
        raise ValueError('canonical premise-declaration nightly cutover required')
    number = int(cutover[4:])
    if cutover != f'Run-{number:03d}' or not 1 <= number < 900:
        raise ValueError('premise-declaration cutover must name a canonical nightly run')
    rid = entity.get('run_id') or entity.get('id')
    if not isinstance(rid, str) or re.fullmatch(r'Run-[0-9]+', rid) is None:
        return False
    return number <= int(rid[4:]) < 900


def _evaluate_publication_scoped_legacy(
    artifact: Path, ledger: dict[str, Any], *, entity_id: str | None = None,
    inspector: Callable[[Path, Path], dict[str, Any]] | None = None,
    enforce: bool = False,
    require_premise_declaration: bool = False,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "artifact": str(artifact.resolve()), "mode": "ENFORCING" if enforce else "REPORT_ONLY",
        "enforcement": enforce, "status": "HOLD",
        "verification_status": "UNCERTIFIED", "label": UNCERTIFIED_LABEL,
        "disclaimer": None, "reasons": [], "paper_bindings": [],
        "published_doi_requires_human_decision": False, "local_lean_execution": False,
    }
    metadata: dict[str, Any] = {}
    metadata_binding = None
    scoped_publication = False
    try:
        if not artifact.is_dir():
            raise ValueError("artifact must be a directory")
        metadata_path = artifact / "zenodo_metadata.json"
        if not metadata_path.exists():
            metadata_path = artifact / "metadata.json"
        if metadata_path.exists():
            metadata_binding = {'filename':metadata_path.name,'sha256':sha256(metadata_path)}
            metadata = read_object(metadata_path)
            if isinstance(metadata.get("metadata"), dict):
                metadata = metadata["metadata"]
        entity = find_entity(ledger, artifact, entity_id)
        result["entity_id"] = entity.get("id")
        result["publication_registration_status"] = entity.get('publication_registration_status')
        doi = metadata.get("doi") or entity.get("doi")
        if isinstance(doi, str) and doi:
            result["doi"] = doi
            result["published_doi_requires_human_decision"] = True
        inspection = inspect_entity_certificate(entity, ledger, inspector)
        root = tree_root(ledger)
        if (artifact/'SCOPED_RELEASE_MANIFEST.json').exists() or (artifact/'SCOPED_RELEASE_MANIFEST.json').is_symlink():
            from scoped_release import require_publication_bound, DISCLAIMER as SCOPED_DISCLAIMER
            scoped = require_publication_bound(artifact, root,
                entity.get('approved_publication_binding_reviews', []), inspector=inspector)
            if scoped['certificate'] != {'path': str((root/entity['certificate']).resolve()),
                                         'sha256': sha256(root/entity['certificate'])}:
                raise ValueError('scoped review differs from SSOT certificate')
            present_metadata=[artifact/name for name in ('zenodo_metadata.json','metadata.json')
                if (artifact/name).exists() or (artifact/name).is_symlink()]
            if len(present_metadata)>1:raise ValueError('ambiguous public metadata files')
            if present_metadata:
                path=present_metadata[0]
                if (path.is_symlink() or not path.is_file() or metadata_binding is None
                        or metadata_binding not in scoped['uploads']
                        or scoped.get('metadata_binding')!=metadata_binding
                        or sha256(path)!=metadata_binding['sha256']
                        or scoped.get('metadata_claim_completeness')is not True):
                    raise ValueError('public metadata missing exact independently reviewed binding')
            else:
                raise ValueError('final independently reviewed public metadata file required')
            historical_fields=_validate_closed_scoped_metadata(metadata,scoped)
            historical_claims=[{'english_claim':'Historical public metadata is UNCERTIFIED provenance, outside the certified scope.',
                'metadata_fields':historical_fields,'evidence_class':'UNCERTIFIED_HISTORICAL_METADATA',
                'verification_status':'NOT_FORMALLY_VERIFIED'}]if historical_fields else []
            result['paper_bindings'] = [{'path': str(artifact/v['filename']), 'sha256': v['sha256']}
                                        for v in scoped['uploads']]
            result['premise_declaration_required'] = True
            result['premise_declaration'] = {'status':'PASS', 'foundation_basis':scoped['foundation_basis'],
                'scope':'Independently reviewed fresh narrowed scope; historical certificate unchanged'}
            result['foundation_basis'] = scoped['foundation_basis']
            result['exact_publication_binding'] = True
            result['claim_gate'] = {'status':'PASS', 'claims':scoped['statement_scope'],
                'unverified_claims':historical_claims, 'independent_review':scoped['review'],
                'scope':'Only listed exact source statements; every historical remainder is UNCERTIFIED'}
            result.update(status='PASS', verification_status='CERTIFIED',
                label='SCOPED CERTIFIED — mathematical claims: '+', '.join(v['lean_theorem'] for v in scoped['statement_scope']),
                disclaimer=SCOPED_DISCLAIMER)
            scoped_publication = True
        else:
            from premise_declaration import validate_artifact
            required = _premise_required(ledger, entity, require_premise_declaration)
            premise = validate_artifact(artifact, inspection, (root / entity['certificate']).resolve(strict=True), root, required=required)
            result['premise_declaration_required'] = required
            result['premise_declaration'] = premise
            if premise.get('status') not in ('PASS', 'EXEMPT') or required and premise.get('status') != 'PASS':
                raise ValueError('premise-declaration gate held: ' + '; '.join(premise.get('reasons', [])))
            if premise.get('foundation_basis') is not None:
                result['foundation_basis'] = premise['foundation_basis']
            result["paper_bindings"] = validate_publication_binding(
                artifact, inspection, (root / entity["certificate"]).resolve(strict=True), root,
                entity.get("approved_publication_binding_reviews", []))
            result["exact_publication_binding"] = True
            claims = check_run(artifact, ledger, entity_id=entity.get("id"), inspector=inspector)
            result["claim_gate"] = claims
            if claims["status"] != "PASS":
                raise ValueError("claim-binding gate held: " + "; ".join(claims["reasons"]))
            result.update(status="PASS", verification_status="CERTIFIED", label="CERTIFIED", disclaimer=DISCLAIMER)
    except Exception as exc:
        result["reasons"].append(f"{type(exc).__name__}: {exc}")
    proposed = dict(metadata)
    # Titles and historical claims are preserved, including on a held artifact.
    proposed["verification_status"] = result["verification_status"]
    proposed["verification_banner"] = result["label"]
    proposed["verification_scope"] = "Only the listed bound formal model claims; empirical claims are not validated by this certificate."
    proposed["unverified_claims"] = result.get("claim_gate", {}).get("unverified_claims", [])
    description = proposed.get("description", proposed.get("abstract", ""))
    if not isinstance(description, str):
        description = ""
    if result["verification_status"] != "CERTIFIED":
        proposed.pop("model_validity_disclaimer", None)
        proposed["description"] = _uncertified_description(description)
        keywords = proposed.get("keywords", [])
        if not isinstance(keywords, list) or any(not isinstance(keyword, str) for keyword in keywords):
            result["reasons"].append("malformed keywords; release remains held")
            keywords = []
        proposed["keywords"] = [keyword for keyword in keywords if keyword.lower() not in ("conjecture", "uncertified")] + ["uncertified"]
    elif scoped_publication:
        proposed["model_validity_disclaimer"] = result['disclaimer']
        # The final API fields remain exactly the independently reviewed input.
        # Bookkeeping is returned separately; no metadata transformation on PASS.
        result['public_metadata']=deepcopy(metadata)
        result['public_metadata_binding']=metadata_binding
        result['public_metadata_unchanged']=True
        proposed['historical_metadata_verification_status']='UNCERTIFIED_PROVENANCE_NOT_CERTIFIED_SCOPE'
    else:
        proposed["model_validity_disclaimer"] = DISCLAIMER
        proposed["description"] = result["label"] + "\n\n" + DISCLAIMER + "\n\n" + description
        if proposed["unverified_claims"]:
            proposed["description"] += "\n\nNot formally verified; empirical validation is not established by the Lean certificate:\n"
            proposed["description"] += "\n".join("- " + item["english_claim"] for item in proposed["unverified_claims"])
    if "abstract" in proposed and not scoped_publication:
        proposed["abstract"] = proposed["description"]
    result["blocking"] = enforce and result["status"] != "PASS"
    result["release_eligible"] = result["status"] == "PASS"
    result["proposed_metadata"] = proposed
    result["canon_eligible"] = result["status"] == "PASS"
    return result


def _evaluate_publication_original_legacy(
    artifact: Path, ledger: dict[str, Any], *, entity_id: str | None = None,
    inspector: Callable[[Path, Path], dict[str, Any]] | None = None,
    enforce: bool = False,
    require_premise_declaration: bool = False,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "artifact": str(artifact.resolve()), "mode": "ENFORCING" if enforce else "REPORT_ONLY",
        "enforcement": enforce, "status": "HOLD",
        "verification_status": "UNCERTIFIED", "label": UNCERTIFIED_LABEL,
        "disclaimer": None, "reasons": [], "paper_bindings": [],
        "published_doi_requires_human_decision": False, "local_lean_execution": False,
    }
    metadata: dict[str, Any] = {}
    try:
        if not artifact.is_dir():
            raise ValueError("artifact must be a directory")
        metadata_path = artifact / "zenodo_metadata.json"
        if not metadata_path.exists():
            metadata_path = artifact / "metadata.json"
        if metadata_path.exists():
            metadata = read_object(metadata_path)
            if isinstance(metadata.get("metadata"), dict):
                metadata = metadata["metadata"]
        entity = find_entity(ledger, artifact, entity_id)
        result["entity_id"] = entity.get("id")
        result["publication_registration_status"] = entity.get('publication_registration_status')
        doi = metadata.get("doi") or entity.get("doi")
        if isinstance(doi, str) and doi:
            result["doi"] = doi
            result["published_doi_requires_human_decision"] = True
        inspection = inspect_entity_certificate(entity, ledger, inspector)
        root = tree_root(ledger)
        from premise_declaration import validate_artifact
        required = _premise_required(ledger, entity, require_premise_declaration)
        premise = validate_artifact(artifact, inspection, (root / entity['certificate']).resolve(strict=True), root, required=required)
        result['premise_declaration_required'] = required
        result['premise_declaration'] = premise
        if premise.get('status') not in ('PASS', 'EXEMPT') or required and premise.get('status') != 'PASS':
            raise ValueError('premise-declaration gate held: ' + '; '.join(premise.get('reasons', [])))
        if premise.get('foundation_basis') is not None:
            result['foundation_basis'] = premise['foundation_basis']
        result["paper_bindings"] = validate_publication_binding(
            artifact, inspection, (root / entity["certificate"]).resolve(strict=True), root,
            entity.get("approved_publication_binding_reviews", []))
        result["exact_publication_binding"] = True
        claims = check_run(artifact, ledger, entity_id=entity.get("id"), inspector=inspector)
        result["claim_gate"] = claims
        if claims["status"] != "PASS":
            raise ValueError("claim-binding gate held: " + "; ".join(claims["reasons"]))
        result.update(status="PASS", verification_status="CERTIFIED", label="CERTIFIED", disclaimer=DISCLAIMER)
    except Exception as exc:
        result["reasons"].append(f"{type(exc).__name__}: {exc}")
    proposed = dict(metadata)
    # Titles and historical claims are preserved, including on a held artifact.
    proposed["verification_status"] = result["verification_status"]
    proposed["verification_banner"] = result["label"]
    proposed["verification_scope"] = "Only the listed bound formal model claims; empirical claims are not validated by this certificate."
    proposed["unverified_claims"] = result.get("claim_gate", {}).get("unverified_claims", [])
    description = proposed.get("description", proposed.get("abstract", ""))
    if not isinstance(description, str):
        description = ""
    if result["verification_status"] != "CERTIFIED":
        proposed.pop("model_validity_disclaimer", None)
        proposed["description"] = _uncertified_description(description)
        keywords = proposed.get("keywords", [])
        if not isinstance(keywords, list) or any(not isinstance(keyword, str) for keyword in keywords):
            result["reasons"].append("malformed keywords; release remains held")
            keywords = []
        proposed["keywords"] = [keyword for keyword in keywords if keyword.lower() not in ("conjecture", "uncertified")] + ["uncertified"]
    else:
        proposed["model_validity_disclaimer"] = DISCLAIMER
        proposed["description"] = result["label"] + "\n\n" + DISCLAIMER + "\n\n" + description
        if proposed["unverified_claims"]:
            proposed["description"] += "\n\nNot formally verified; empirical validation is not established by the Lean certificate:\n"
            proposed["description"] += "\n".join("- " + item["english_claim"] for item in proposed["unverified_claims"])
    if "abstract" in proposed:
        proposed["abstract"] = proposed["description"]
    result["blocking"] = enforce and result["status"] != "PASS"
    result["release_eligible"] = result["status"] == "PASS"
    result["proposed_metadata"] = proposed
    result["canon_eligible"] = result["status"] == "PASS"
    return result


def evaluate_publication(
    artifact: Path, ledger: dict[str, Any], *, entity_id: str | None = None,
    inspector: Callable[[Path, Path], dict[str, Any]] | None = None,
    enforce: bool = False,
    require_premise_declaration: bool = False,
) -> dict[str, Any]:
    return methods_digest_registration.evaluate_publication(artifact, ledger, legacy=_evaluate_publication_original_legacy, scoped_legacy=_evaluate_publication_scoped_legacy, entity_id=entity_id, inspector=inspector, enforce=enforce, require_premise_declaration=require_premise_declaration)


def stage_result(result: dict[str, Any], output_dir: Path, *, enforce: bool = False) -> list[str]:
    """Write a reviewable successor package, without touching source artifacts."""
    source = Path(result["artifact"]).resolve()
    target = output_dir.resolve()
    if target == source or target.is_relative_to(source):
        raise ValueError("output-dir must be outside the source artifact")
    target.mkdir(parents=True, exist_ok=True)
    report = dict(result)
    report["mode"] = "ENFORCING" if enforce else "REPORT_ONLY"
    report["enforcement"] = enforce
    report["blocking"] = enforce and result["status"] != "PASS"
    report["source_artifact_modified"] = False
    paths = []
    report_path = target / "PUBLICATION_GATE_REPORT.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    paths.append(str(report_path))
    if enforce:
        # Existing published records are never changed, even with --enforce.
        # A successor proposal is reviewable; DOI amendment remains a human act.
        metadata_path = target / "metadata.json"
        metadata_path.write_text(json.dumps(result["proposed_metadata"], indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        banner_path = target / "VERIFICATION_BANNER.md"
        banner = result["label"] + ("\n\n" + DISCLAIMER if result["status"] == "PASS" else "")
        banner_path.write_text(banner + "\n", encoding="utf-8")
        paths.extend([str(metadata_path), str(banner_path)])
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["check"])
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--entity-id")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--enforce", action="store_true", help="stage enforceable labels in output-dir")
    parser.add_argument('--require-premise-declaration', action='store_true', help='require INV-9 for this new artifact; historical default remains off')
    args = parser.parse_args(argv)
    if args.enforce and args.output_dir is None:
        parser.error("--enforce requires an explicit --output-dir for the successor package")
    try:
        result = evaluate_publication(args.artifact, read_object(args.ledger), entity_id=args.entity_id, enforce=args.enforce, require_premise_declaration=args.require_premise_declaration)
        if args.output_dir:
            result["written"] = stage_result(result, args.output_dir, enforce=args.enforce)
        result["mode"] = "ENFORCING" if args.enforce else "REPORT_ONLY"
    except Exception as exc:
        result = {"status": "HOLD", "verification_status": "UNCERTIFIED", "label": UNCERTIFIED_LABEL,
                  "enforcement": args.enforce, "blocking": args.enforce,
                  "disclaimer": None, "reasons": [f"{type(exc).__name__}: {exc}"]}
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
