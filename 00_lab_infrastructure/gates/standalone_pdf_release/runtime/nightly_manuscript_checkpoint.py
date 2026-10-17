"""Normal minimal-note preparation plus separately bound historical PDF access.

No generation, certification, publication or activation is implemented. Every
source/stage/review call delegates to the unchanged ordinary scientific route.
The current digest consumes the new access format through its default reader.
"""
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
import json
import methods_digest_v2 as digest
import nightly_manuscript_access as access

STANDARD = 'VRS-NIGHTLY-MANUSCRIPT-ACCESS-CHECKPOINT-1'


def source_for_cycle(root, *args, **kwargs):
    with access.frozen_sources(root) as load:
        return load('nightly_release_checkpoint').source_for_cycle(root, *args, **kwargs)


def stage_checkpoint(root, *args, **kwargs):
    with access.frozen_sources(root) as load:
        return load('nightly_release_checkpoint').stage_checkpoint(root, *args, **kwargs)


def review_checkpoint(root, note_path, authority, *, review_invocation):
    manifest=json.loads(digest.read_regular(Path(note_path)/'SCOPED_RELEASE_MANIFEST.json'))
    if manifest.get('standard')==access.LABELLED_STANDARD:
        return access.review_labelled(root,note_path,authority,review_invocation=review_invocation)
    with access.frozen_sources(root) as load:
        return load('nightly_release_checkpoint').review_checkpoint(
            root, note_path, authority, review_invocation=review_invocation)


def prepare_access(root, note_path, out, authority, *, render=None):
    """Only an already genuinely reviewed immutable base may be extended."""
    return access.prepare_labelled(root, note_path, out, authority, render=render)


def new_note_specs(root, notes, authority, *, week, account_discovery,
                   predecessor_registration=None):
    root = Path(root).resolve(strict=True)
    with access.frozen_sources(root) as load:
        weekly = load('digest_weekly_state')
        proof = json.loads(digest.bound_file(root, account_discovery)[1])
        discovery = weekly.require_account_discovery(proof, root=root)
        access.need(proof['release_week'] == week, 'exact discovered week')
        if discovery['status'] == 'EXISTING_WEEKLY_RECORD':
            access.need(predecessor_registration is not None
                        and proof['start_kind'] == 'NEW_VERSION', 'actual default predecessor required')
            admitted = load('methods_digest_registration').require_registration(root, predecessor_registration)
            access.need(admitted['receipt']['record_id'] == discovery['record_id']
                        and admitted['receipt']['release_week'] == week, 'exact latest weekly predecessor')
            prior = weekly.registered_lineage_runs(admitted, root=root)
        else:
            access.need(discovery['status'] == 'NO_EXISTING_WEEKLY_RECORD'
                        and proof['start_kind'] == 'CREATE_WEEK'
                        and predecessor_registration is None and week != '2026-W41',
                        'complete first-week absence only')
            prior = set()
        access.need(isinstance(notes, list) and notes, 'nonempty notes')
        specs = []
        seen = set()
        for note in notes:
            path = Path(note).resolve(strict=True)
            access.need(path.is_relative_to(root), 'canonical current access note')
            current = digest.current_note_consumer(path, root, authority)
            run = load('nightly_minimal_policy').canonical_run(current['run_id'])
            access.need(current['status'] == 'PUBLICATION_BOUND'
                        and current.get('exact_publication_binding') is True
                        and run not in seen and run not in prior,
                        'new default-admitted disjoint note')
            seen.add(run)
            specs.append({'run_id':run,'path':str(path)})
        return specs, discovery


def stage_weekly_package(root, out, week, notes, authority, source_metadata,
                         publication_date, *, account_discovery,
                         predecessor_registration=None, render=None):
    specs, discovery = new_note_specs(root, notes, authority, week=week,
        account_discovery=account_discovery, predecessor_registration=predecessor_registration)
    title = digest.week_title(week) if discovery['status'] == 'EXISTING_WEEKLY_RECORD' else None
    manifest = digest.prepare(root, out, week, specs, authority, source_metadata,
        publication_date, render=render, existing_title=title)
    access.need(digest.require_current(out, root) == manifest,
                'fresh unchanged current digest package')
    return {'standard':STANDARD,
        'status':'ACTUAL_DEFAULT_NOTE_COHORT_AND_METHODS_PACKAGE_STAGED_NOT_PUBLISHED',
        'package_path':str(out),'digest_manifest':digest.binding(Path(out) / 'DIGEST_MANIFEST.json'),
        'release_week':week,'notes':[s['run_id'] for s in specs],
        'start_kind':'NEW_VERSION' if discovery['status'] == 'EXISTING_WEEKLY_RECORD' else 'CREATE_WEEK',
        'account_discovery':deepcopy(account_discovery),
        'predecessor_registration':deepcopy(predecessor_registration),
        'full_pdf_review_and_publication_authority_still_required':True,
        'certifies':False,'zenodo_writes':0,'ssot_writes':0}


if __name__ == '__main__':
    raise SystemExit('HOLD: explicit measured preparation calls only; no publication authority')
