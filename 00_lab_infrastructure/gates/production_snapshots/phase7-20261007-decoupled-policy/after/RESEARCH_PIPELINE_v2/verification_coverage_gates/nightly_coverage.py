"""Coverage bookkeeping from genuine checkpoint receipts; never generates or verifies proofs."""
from __future__ import annotations

import copy
from collections import Counter
import datetime as dt
import hashlib
import json
import re
import tomllib
from pathlib import Path
from zoneinfo import ZoneInfo

TZ = ZoneInfo('America/New_York')


def binding(path: Path) -> dict:
    return {'path': str(path.resolve()), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def _aware(value: str) -> dt.datetime:
    result = dt.datetime.fromisoformat(value)
    if result.tzinfo is None:
        raise ValueError('timestamp must include timezone')
    return result


# The activation receipt is bookkeeping evidence, never proof acceptance evidence.
ACTIVATION_STANDARD = 'VRS-PHASE5-ENFORCEMENT-ACTIVATION-1'
ACTIVATION_SOURCES = {'installation', 'protected_readback', 'registration_ledger',
                      'source_observation', 'scheduler_readback'}
ACTIVATION_PROOFS = {'after_manifest', 'merge_review', 'registration_plan',
                     'protected_baseline', 'scheduler_before'}
APPROVED_REGISTRATION_PLAN_SHA256 = '72044a08aba24d2c82d0b9fd68cb2198bc0075f6a456a0662a5e0554bed23b62'
COVERAGE_FIELDS = ('file_counts', 'run_counts', 'receipt_era', 'mirror_drift', 'errors')
REGISTRATION_IDENTITY_FIELDS = ('id', 'path', 'run_id', 'certificate', 'certificate_sha256',
                                'approved_publication_binding_reviews')


class PreActivationIneligible(ValueError):
    """Valid historical checkpoints are informational and cannot poison future windows."""


def ordinary_run(value):
    if (not isinstance(value, str) or re.fullmatch(r'Run-[0-9]{3}', value) is None
            or not 1 <= int(value[4:]) < 900):
        raise ValueError('canonical ordinary Run-001..899 required')
    return int(value[4:])


def _sha(value):
    if not isinstance(value, str) or re.fullmatch(r'[0-9a-f]{64}', value) is None:
        raise ValueError('lowercase SHA-256 required')
    return value


def activation_binding(value):
    if not isinstance(value, dict) or set(value) != {'path', 'sha256'}:
        raise ValueError('exact activation/source path and SHA-256 binding required')
    relative = value['path']
    if (not isinstance(relative, str) or not relative or Path(relative).is_absolute()
            or any(part in ('.', '..') for part in Path(relative).parts)):
        raise ValueError('nonempty canonical tree-relative activation/source path required')
    if str(Path(relative)) != relative:
        raise ValueError('canonical unnormalized activation/source path forbidden')
    _sha(value['sha256'])
    return dict(value)


def _source_path(root, value, *, historical_absolute=False):
    if historical_absolute and isinstance(value, dict) and isinstance(value.get('path'), str) and Path(value['path']).is_absolute():
        # Existing protected baseline bytes contain absolute historical bindings.
        # They must resolve beneath the identical canonical root, never elsewhere.
        absolute = Path(value['path'])
        if not absolute.is_relative_to(root):
            raise ValueError('historical source binding outside canonical tree')
        value = {**value, 'path': str(absolute.relative_to(root))}
    value = activation_binding(value)
    path = root / value['path']
    current = path
    while current != root:
        if current.is_symlink():
            raise ValueError('activation/source path contains a symlink')
        current = current.parent
    resolved = path.resolve(strict=True)
    if not resolved.is_relative_to(root) or not resolved.is_file():
        raise ValueError('activation/source receipt is not a regular canonical file')
    if hashlib.sha256(resolved.read_bytes()).hexdigest() != value['sha256']:
        raise ValueError('activation/source SHA-256 mismatch')
    return resolved


def _load_source(root, value):
    obj = json.loads(_source_path(root, value).read_bytes())
    if not isinstance(obj, dict):
        raise ValueError('activation/source receipt object required')
    return obj


# Closed historical bookkeeping only. The original five authority sources/proofs
# and all verification/registration checks stay strict.
HISTORICAL_PROVENANCE_PROOF = 'historical_provenance'
APPROVED_ORIGINAL_TRACKED_SNAPSHOT_FILES = (('AFTER_MANIFEST.json', '8abfd4f5264c7c6f9c61b0a79c810a7a725d74ce7100b4d209fabaa9d6b1b677'), ('AFTER_MANIFEST_PRE_CUTOVER_20261005.json', 'a881ae2973421db2401fd7b768893365f5bff2d476ad6e4b8a93722a0188d427'), ('AFTER_MANIFEST_PRE_INV9_20261004.json', 'c89d83b5447aaac73edff31234907b19140078484a102c09e6eeb48e92c5c449'), ('BEFORE_DEPENDENCY_MANIFEST.json', '5d7ab7006b44ef2ea381923bceb58f2c960e5aff742f026eae03fae1dcf8797d'), ('BEFORE_MANIFEST.json', '60d7133b8a10da2a051f1bc83a8351dcd0c57c1eefd9456c77d532d01776edf1'), ('CURRENT_REAL_WINDOW_STATUS.json', '5819bafdd39eccfbc164952dd166f0d11c3fd2141cffe6fdaf27cea149285df0'), ('CURRENT_REAL_WINDOW_STATUS_V002.json', '9fb9429e6430ad30130a7f0890ae76927284ef31c923baa020a713ecbb4f4d64'), ('INSTALLATION_PLAN.md', '999b178fd0a28149ef64ccfad8635cf3819b84ac5482e7a9959c055595ef09c6'), ('INV9_BEFORE_MANIFEST.json', '5f198f8cc984773143ee3baf8a8b1dbf63ad45e1e129874b66714441a5ef9ff8'), ('LIVE_INSTALL_PREFLIGHT_UI_20261004.json', '21d4d1437af05a13afc80a4de001137b2bde6d59d18a8e4aa894fb40ea8f1b1e'), ('LIVE_INSTALL_PREFLIGHT_V002.json', '8477f5a5519b95a9da0b6835999133929a469501fa112d85d22fe6111aab3918'), ('NIGHTLY_INTAKE_AUDIT.json', '89971355a7b62cf99e73886845aeb778f274ac49462698981f803748aa4def2b'), ('PREPARATION_STATUS.json', '9999d94451b89ff0719cdafbed430ed41d08f06b535f40d12e6ee0cbeeec5ff2'), ('PUBLICATION_ENTITY_REGISTRATIONS_PROPOSAL.json', 'f3df1a25b62d096ac43c93b5b32ebccaf6ac1b6c83b58ec83428630012d2f5d3'), ('PUBLICATION_REREGISTRATION_V002.json', '72044a08aba24d2c82d0b9fd68cb2198bc0075f6a456a0662a5e0554bed23b62'), ('READINESS_20261004.json', '83eea2964b633026e2a3f9e506d40ab9e08975e3f0ceb2c2bca26085f7c98e5e'), ('READINESS_20261004.md', '96557814991612dfe4b1d421ace324be526186b34e95bd8d584f7dea7104932c'), ('READINESS_PRE_UI_20261004.json', 'd68fa6eab35aa0863db2506fe3f7357741c3447a243f5670af35087c0bc64227'), ('READINESS_UI_20261004.md', 'e643538caa670d54a47f7e56916e46abf8b1b98aa0ebcc288c619239ac51439e'), ('SSOT_REBUILD_DIAGNOSIS_V002.md', '36bace40526b89e9c62ae243778f37028bd8f71a51fb1c13ec839a20a115ee70'), ('TEST_RESULTS.txt', 'ce413810731a1826c6c61900c9b2db9ca399637ba2b0a6abc038f52e4ac107bc'), ('UI_EXECUTION_DEPENDENCIES_MANIFEST_20261004.json', '14d417ee0f9dda3727bcd528261e56bfd14ac23a7ba8d4208d15cc1c9727c3ea'), ('after/RESEARCH_PIPELINE_v2/issue_lean_zero_sorry_certificate.py', '96c5c70d7d9de31c537ac4dc4a405d5f2c38a7ba03389c93dac1efb28cfc5ebe'), ('after/RESEARCH_PIPELINE_v2/nightly_checkpoint.py', 'f550c0f808bb15e603b875aed55962b0297731e5a2e4edf4aac99f33eab959df'), ('after/RESEARCH_PIPELINE_v2/verification_coverage_gates/certificate_inspection.py', 'a7e3d2fcd167865b129529fce7e3599acf045a190cbc2107e87f39b0a3623ec8'), ('after/RESEARCH_PIPELINE_v2/verification_coverage_gates/claim_binding.py', 'd0bac6e9739c41c5cc40cc57b932f1d15ac7a86f457a0ee3fecdc0ef7a2b7240'), ('after/RESEARCH_PIPELINE_v2/verification_coverage_gates/corpus_ledger.py', 'd9d68fbb90605c975a006c070a448c3b843efb05a52b164c816d232dd6e583d9'), ('after/RESEARCH_PIPELINE_v2/verification_coverage_gates/doi_audit.py', '23173076f35f62ca0696544c3a5c7ee2bcf7bc39a8a649390ec8e616c2c06f29'), ('after/RESEARCH_PIPELINE_v2/verification_coverage_gates/doi_triage.py', '86d9d1e65286ff13038dc75ab3150a616d5acc7515b1ee4fcf04644f1db171ca'), ('after/RESEARCH_PIPELINE_v2/verification_coverage_gates/manuscript_structure.py', '3177a850997c760ca65e23416116fa4920cf35f238753f63fa63d3a7e4b300a9'), ('after/RESEARCH_PIPELINE_v2/verification_coverage_gates/mirror_parity.py', '77033a9303519bc47493f4efc2b0872fff805baa9aa35aa61e34467f66336e80'), ('after/RESEARCH_PIPELINE_v2/verification_coverage_gates/nightly_coverage.py', '02f87445c836b02ba5cbda03631e98448dd88b2357098af2cfa87ab6dd6d925c'), ('after/RESEARCH_PIPELINE_v2/verification_coverage_gates/nightly_publication_intake.py', '9f3aa3c7f438f22b1c07242e9c548f6a9917ecbc2999ffe817256a602f472ba8'), ('after/RESEARCH_PIPELINE_v2/verification_coverage_gates/premise_declaration.py', 'c4cdba028df6c34fb117c02ff57d303a26b899b59892fcbbadc9457175232445'), ('after/RESEARCH_PIPELINE_v2/verification_coverage_gates/production_hooks.py', '9b0a3d48e2cabff04c58a9020c07db2a9afe7e7f8c7cbde5e034d56d0b77db81'), ('after/RESEARCH_PIPELINE_v2/verification_coverage_gates/publication_binding.py', '1fb3d5bc1d0df57445b8d7fed8a034e7bab7f1aeb0314db21e3cedd5e237df2e'), ('after/RESEARCH_PIPELINE_v2/verification_coverage_gates/publication_gate.py', 'a44fe11deccc4d1246d4d2b0fc53621807e1f06061eafff1fb684615fcff7fef'), ('after/RESEARCH_PIPELINE_v2/verification_coverage_gates/release_packet.py', '972cc9816e3f2d1c3f93120666358421c9163535afd143a6f401725fc3545357'), ('after/RESEARCH_PIPELINE_v2/verification_coverage_gates/run_flow.py', '00a6d309360aabda0e27f37a0cd757e103c1c502497b3f2553e28d2070b98b04'), ('after/RESEARCH_PIPELINE_v2/verification_coverage_gates/static_pregate.py', '659e2d66a45af24a846a5fafe26564ccf713492d0d06be0fb8172e961e862153'), ('after/RESEARCH_PIPELINE_v2/verification_coverage_gates/theorem_coverage.py', '62bb9e87b10b8ef317616e4b906878d03f06752ab4e7d2dff90bdf9dfb27e99d'), ('after/_ZENODO_DEPOSITS/publish_dated_bundles.py', '4f099eaffb9a35fbd24e5c57ef34801391fabcd5c3272b58a379d7ac52b35e94'), ('after/_ZENODO_DEPOSITS/release_coherence.py', '348bc1f54ed027c6768efe512717bbc66976b7c658198383803d7e2bb8535060'), ('after/_ZENODO_DEPOSITS/weekend_canon_lockstep.py', '36b23f17c4ef4a9758f587caeb52f16c72d149fb49776e4e2fc920f5d2e32bec'), ('after/production_execution_dependencies/byte_metadata_requirements.txt', '3ec8922905dc4e3a10c3b46bd7fba023c37ffc309d51c6bed2a13ec3e98177fd'), ('after/production_execution_dependencies/file_byte_metadata.py', '4a21de5efd74531b135682f92ce4d49b1d8ad71d044795548ea9877756fa50ef'), ('after/production_execution_dependencies/server_managed_fields.py', 'ce8ad2002a11938966201a44d2714ee866bb922649cd572e36f09e8cc0f062a1'), ('after/production_execution_dependencies/test_server_managed_fields.py', '7011fb7b668b8ec0c103423ebdecfa2b4cbf1bc8f19b3cb4119ed936d32be973'), ('before/RESEARCH_PIPELINE_v2/issue_lean_zero_sorry_certificate.py', '789cb903c972a9c10731360769ccff56055b3257de9491a75b92c0d549b5c438'), ('before/RESEARCH_PIPELINE_v2/nightly_checkpoint.py', 'e22068a8f9e587fe4e3ab5382c80197237dbc4c2a8f4b7ad0b066d908683042c'), ('before/RESEARCH_PIPELINE_v2/verification_coverage_gates/certificate_inspection.py', 'a7e3d2fcd167865b129529fce7e3599acf045a190cbc2107e87f39b0a3623ec8'), ('before/RESEARCH_PIPELINE_v2/verification_coverage_gates/claim_binding.py', '3f041f2d60631e055d1c174c8e5939e12ad0a76ba419b8a33649f97473f741bb'), ('before/RESEARCH_PIPELINE_v2/verification_coverage_gates/corpus_ledger.py', '297d83ce31a3d8057c9e965eba683a9b7f3abe59fd316fb365cb0fbcb06e21a0'), ('before/RESEARCH_PIPELINE_v2/verification_coverage_gates/doi_audit.py', '23173076f35f62ca0696544c3a5c7ee2bcf7bc39a8a649390ec8e616c2c06f29'), ('before/RESEARCH_PIPELINE_v2/verification_coverage_gates/doi_triage.py', '86d9d1e65286ff13038dc75ab3150a616d5acc7515b1ee4fcf04644f1db171ca'), ('before/RESEARCH_PIPELINE_v2/verification_coverage_gates/mirror_parity.py', '77033a9303519bc47493f4efc2b0872fff805baa9aa35aa61e34467f66336e80'), ('before/RESEARCH_PIPELINE_v2/verification_coverage_gates/production_hooks.py', '3c595fd12515e4ca46b13f652d5642758f87352c37048042d32bf806516d93b0'), ('before/RESEARCH_PIPELINE_v2/verification_coverage_gates/publication_gate.py', 'a1fb8a88129be2aa286a2652e3de426a721de04cc6838e4e416637e05604e610'), ('before/RESEARCH_PIPELINE_v2/verification_coverage_gates/run_flow.py', '082e6ca62ec3a476c9691b1d1e5d68e0657326ec4eb3f48637e844bffec492a3'), ('before/RESEARCH_PIPELINE_v2/verification_coverage_gates/static_pregate.py', '659e2d66a45af24a846a5fafe26564ccf713492d0d06be0fb8172e961e862153'), ('before/RESEARCH_PIPELINE_v2/verification_coverage_gates/theorem_coverage.py', '62bb9e87b10b8ef317616e4b906878d03f06752ab4e7d2dff90bdf9dfb27e99d'), ('before/_ZENODO_DEPOSITS/publish_dated_bundles.py', '8d0cec379f8fbce959873f0f7524bb36d6ee0440c85fafde40ca57176e804668'), ('before/_ZENODO_DEPOSITS/release_coherence.py', '348bc1f54ed027c6768efe512717bbc66976b7c658198383803d7e2bb8535060'), ('before/_ZENODO_DEPOSITS/weekend_canon_lockstep.py', 'c0cb623e9c58f0db191abe82a8047bf7e6dabfcab869f9923e44c850f1a6741e'))
ORIGINAL_ACTIVATION_GUARD_SHA256 = '02f87445c836b02ba5cbda03631e98448dd88b2357098af2cfa87ab6dd6d925c'
APPROVED_ORIGINAL_AFTER_MANIFEST_SHA256 = '8abfd4f5264c7c6f9c61b0a79c810a7a725d74ce7100b4d209fabaa9d6b1b677'
HISTORICAL_PROVENANCE_POLICY_SHA256 = '3fb8c4dcd465c1272d1499bc3ffb389a07e5d4138a9440b9277f1331cecdec49'


def _provenance_json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate historical-provenance JSON key')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique)


def _policy_sha(value):
    raw = (json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False) + '\n').encode()
    return hashlib.sha256(raw).hexdigest()


def _pointer_value(document, pointer):
    if not isinstance(pointer, str) or not pointer.startswith('/'):
        raise ValueError('canonical source JSON pointer required')
    current = document
    for encoded in pointer[1:].split('/'):
        if re.search(r'~(?![01])', encoded):
            raise ValueError('malformed source JSON pointer escape')
        key = encoded.replace('~1', '/').replace('~0', '~')
        if encoded != key.replace('~', '~0').replace('/', '~1'):
            raise ValueError('noncanonical source JSON pointer')
        if isinstance(current, list):
            if re.fullmatch(r'0|[1-9][0-9]*', key) is None:
                raise ValueError('canonical source array index required')
            current = current[int(key)]
        elif isinstance(current, dict):
            current = current[key]
        else:
            raise ValueError('source JSON pointer crosses a scalar')
    return current


class _HistoricalProvenance:
    """Resolve only source-bound historical literals; never read an external path.

    A policy row is an exact original literal/hash -> exact canonical byte copy.
    A mapping also binds the containing canonical document, its immutable bytes,
    and its JSON pointer. It cannot affect any direct current authority binding.
    All children remain recursively checked and every approved map must be used.
    """
    def __init__(self, root, receipt):
        capsule_binding = activation_binding(receipt['proofs'][HISTORICAL_PROVENANCE_PROOF])
        capsule_path = _source_path(root, capsule_binding)
        capsule = _provenance_json(capsule_path.read_bytes())
        expected = {'standard', 'status', 'tree_root', 'policy', 'documents', 'mappings'}
        if (not isinstance(capsule, dict) or set(capsule) not in (expected, expected | {'gate_successor'})
                or capsule['standard'] != 'VRS-ACTIVATION-HISTORICAL-PROVENANCE-1'
                or capsule['status'] != 'EXACT_SOURCE_BOUND_CANONICAL_RELOCATION'
                or capsule['tree_root'] != str(root)):
            raise ValueError('closed source-bound historical-provenance capsule required')
        self.gate_successor = capsule.get('gate_successor')
        if self.gate_successor is not None:
            activation_binding(self.gate_successor)
        policy = capsule['policy']
        if not isinstance(policy, list) or not policy or _policy_sha(policy) != HISTORICAL_PROVENANCE_POLICY_SHA256:
            raise ValueError('exact reviewed historical-provenance policy required')
        policies = {}
        frozen_documents = {}
        direct_current = list(receipt['sources'].values()) + [v for k, v in receipt['proofs'].items() if k != HISTORICAL_PROVENANCE_PROOF]
        for row in policy:
            fields = {'kind', 'literal_path', 'expected_sha256', 'canonical_path'}
            if not isinstance(row, dict):
                raise ValueError('closed historical-provenance policy row required')
            frozen = row.get('kind') == 'FROZEN_HISTORICAL_LOCATION'
            if set(row) != (fields | {'source_document', 'json_pointer'} if frozen else fields):
                raise ValueError('closed historical-provenance policy row required')
            if row['kind'] not in {'SEALED_INPUT_LOCATION', 'HISTORICAL_PRECONDITION', 'FROZEN_HISTORICAL_LOCATION'} or not isinstance(row['literal_path'], str) or not row['literal_path']:
                raise ValueError('unknown historical-provenance policy class')
            identity = (row['kind'], row['literal_path'], _sha(row['expected_sha256']))
            if frozen:
                source = activation_binding(row['source_document'])
                if source in direct_current:
                    raise ValueError('historical relocation cannot map a direct current authority document')
                # The closed policy may contain a future immutable copy owner.
                # Its bytes are required when that exact edge enters this capsule,
                # never fabricated or read through its historical external literal.
                identity += (source['path'], source['sha256'], row['json_pointer'])
            if identity in policies:
                raise ValueError('duplicate historical-provenance policy row')
            canonical = activation_binding({'path': row['canonical_path'], 'sha256': row['expected_sha256']})
            _source_path(root, canonical)  # Canonical regular bytes must match.
            policies[identity] = canonical
        predecessors = [value for key, value in policies.items() if key[0] == 'HISTORICAL_PRECONDITION']
        if len(predecessors) != 1:
            raise ValueError('one exact immutable historical predecessor required')
        documents = capsule['documents']
        if not isinstance(documents, dict) or set(documents) != {'registration_plan', 'registration_ledger', 'historical_precondition_ledger'}:
            raise ValueError('closed historical source document set required')
        if (documents['registration_plan'] != receipt['proofs']['registration_plan']
                or documents['registration_ledger'] != receipt['sources']['registration_ledger']
                or documents['historical_precondition_ledger'] != predecessors[0]
                or documents['registration_plan'].get('sha256') != APPROVED_REGISTRATION_PLAN_SHA256):
            raise ValueError('historical documents differ from exact current authority or archived predecessor')
        parsed = {}
        for role, source in documents.items():
            source = activation_binding(source)
            document = _provenance_json(_source_path(root, source).read_bytes())
            if not isinstance(document, dict) or document.get('tree_root') != str(root):
                raise ValueError('historical source document root differs')
            if role == 'registration_ledger' and document.get('premise_declaration_cutover_run') != receipt['premise_declaration_cutover_run']:
                raise ValueError('current registration source cutover differs')
            parsed[role] = document
        mappings = capsule['mappings']
        if not isinstance(mappings, list) or not mappings:
            raise ValueError('nonempty explicit historical source mappings required')
        self.rows, self.used = {}, set()
        for row in mappings:
            if not isinstance(row, dict) or set(row) != {'kind', 'document_role', 'source_document', 'json_pointer', 'literal_path', 'expected_sha256', 'canonical_binding'}:
                raise ValueError('closed historical source mapping required')
            role = row['document_role']
            kind, pointer = row['kind'], row['json_pointer']
            if kind == 'FROZEN_HISTORICAL_LOCATION':
                source = activation_binding(row['source_document'])
                identity = (kind, row['literal_path'], _sha(row['expected_sha256']), source['path'], source['sha256'], pointer)
                if role != 'frozen_historical_source' or identity not in policies:
                    raise ValueError('unknown fixed frozen historical source owner')
                key = (source['path'], source['sha256'])
                if key not in frozen_documents:
                    document = _provenance_json(_source_path(root, source).read_bytes())
                    if not isinstance(document, dict):
                        raise ValueError('frozen historical source object required')
                    frozen_documents[key] = document
                document = frozen_documents[key]
            else:
                if role not in documents or row['source_document'] != documents[role]:
                    raise ValueError('historical mapping source binding differs')
                document = parsed[role]
            if kind == 'HISTORICAL_PRECONDITION':
                if (role != 'registration_plan' or pointer != '/precondition_current_ledger'
                        or row['literal_path'] != str(root / 'RESEARCH_PIPELINE_v2/corpus_ledger.json')):
                    raise ValueError('historical predecessor mapping is outside its own original precondition')
            elif kind == 'SEALED_INPUT_LOCATION':
                if (role not in {'registration_ledger', 'historical_precondition_ledger'}
                        or not isinstance(pointer, str)
                        or re.fullmatch(r'/(?:certificates/(?:0|[1-9][0-9]*)/sealed_paper_inputs|run_entities/(?:0|[1-9][0-9]*)/certificate_artifacts)/SEALED_(?:CLAIM_INVENTORY\.json|RUN_MANIFEST\.json|paper\.(?:pdf|tex))', pointer) is None):
                    raise ValueError('sealed input mapping is outside historical diagnostic fields')
            elif kind != 'FROZEN_HISTORICAL_LOCATION':
                raise ValueError('unknown historical source mapping class')
            identity = (kind, row['literal_path'], _sha(row['expected_sha256']))
            if kind == 'FROZEN_HISTORICAL_LOCATION':
                identity += (source['path'], source['sha256'], pointer)
            if identity not in policies or row['canonical_binding'] != policies[identity]:
                raise ValueError('unknown or changed original/canonical historical mapping')
            original = {'path': row['literal_path'], 'sha256': row['expected_sha256']}
            if _pointer_value(document, pointer) != original:
                raise ValueError('historical mapping does not equal the exact source pointer value')
            source = row['source_document']
            key = (source['path'], source['sha256'], pointer)
            if key in self.rows:
                raise ValueError('duplicate historical mapping source pointer')
            self.rows[key] = (original, dict(row['canonical_binding']))

    def mapped(self, source_document, pointer, original):
        if source_document is None:
            return None  # Direct five current sources/proofs never map.
        key = (source_document['path'], source_document['sha256'], pointer)
        if key not in self.rows:
            return None  # The unchanged strict resolver will HOLD if invalid.
        expected, canonical = self.rows[key]
        if original != expected:
            raise ValueError('historical source value differs at mapped pointer')
        self.used.add(key)
        return canonical

    def require_complete(self):
        if self.used != set(self.rows):
            raise ValueError('unused historical mapping or unreachable source pointer')


def _nested_sources(root, obj, seen=None, base=None, *, provenance=None, source_document=None, pointer=''):
    """Re-read every nested binding; only exact approved historical edges map."""
    seen = set() if seen is None else seen
    base = root if base is None else base
    if isinstance(obj, dict):
        if set(obj) == {'path', 'sha256'}:
            reference = provenance.mapped(source_document, pointer, obj) if provenance is not None else None
            if reference is None:
                reference = obj
                if isinstance(obj.get('path'), str) and not Path(obj['path']).is_absolute():
                    at_root, at_parent = root / obj['path'], base / obj['path']
                    if at_root.exists() and at_parent.exists() and at_root.resolve() != at_parent.resolve():
                        raise ValueError('ambiguous recursive receipt binding')
                    if not at_root.exists() and at_parent.exists():
                        reference = {**obj, 'path': str(at_parent.relative_to(root))}
            path = _source_path(root, reference, historical_absolute=True)
            if path in seen:
                return
            seen.add(path)
            try:
                child = _provenance_json(path.read_bytes()) if provenance is not None else json.loads(path.read_bytes())
            except (UnicodeDecodeError, json.JSONDecodeError):
                return
            binding = {'path': str(path.relative_to(root)), 'sha256': reference['sha256']}
            _nested_sources(root, child, seen, path.parent, provenance=provenance, source_document=binding)
        else:
            for key, child in obj.items():
                encoded = str(key).replace('~', '~0').replace('/', '~1')
                _nested_sources(root, child, seen, base, provenance=provenance, source_document=source_document, pointer=pointer + '/' + encoded)
    elif isinstance(obj, list):
        for index, child in enumerate(obj):
            _nested_sources(root, child, seen, base, provenance=provenance, source_document=source_document, pointer=pointer + '/' + str(index))


def first_eligible_window(activated):
    local = activated.astimezone(TZ)
    day = local.date()
    boundary = dt.datetime.combine(day, dt.time(1), TZ)
    if boundary.astimezone(dt.timezone.utc) < activated:
        day += dt.timedelta(days=1)
    return day.isoformat()


def _registrations(root, ledger, original_plan):
    if ledger.get('tree_root') != str(root):
        raise ValueError('registration ledger canonical root differs')
    planned = original_plan.get('publication_entities')
    rows = ledger.get('publication_entities')
    if (not isinstance(planned, list) or len(planned) != 27 or
            not isinstance(rows, list) or any(not isinstance(e, dict) for e in planned + rows)):
        raise ValueError('original approved 27 registrations and current table required')
    expected = {e.get('id'): e for e in planned}
    actual = {e.get('id'): e for e in rows}
    if len(expected) != 27 or len(actual) != len(rows) or any(not isinstance(k, str) or not k for k in expected):
        raise ValueError('unique original registration identities required')
    if not expected.keys() <= actual.keys():
        raise ValueError('original publication registration was lost')
    for eid, original in expected.items():
        for field in REGISTRATION_IDENTITY_FIELDS:
            if not original.get(field) or actual[eid].get(field) != original[field]:
                raise ValueError('original publication registration identity/review changed: ' + eid + '/' + field)
    # Reuse the exact existing preserving consumer and public banner validator.
    # No status/name/count inference can replace these fresh checks.
    from corpus_ledger import preserve_publication_registrations, validate_uncertified_readback
    fresh = preserve_publication_registrations(copy.deepcopy(ledger), ledger)
    reviewed = fresh.get('publication_entities', [])
    if len(reviewed) != len(rows) or {e.get('id') for e in reviewed} != set(actual):
        raise ValueError('fresh preserving registration consumer changed identities')
    for entity in reviewed:
        if entity.get('enforcement_acceptable') is not True:
            raise ValueError('fresh publication registration is not enforcement-acceptable: ' + str(entity.get('id')))
        status = entity.get('publication_registration_status')
        if status == 'HOLD_NO_CLAIM_MAP':
            validate_uncertified_readback(root, entity)
        elif status != 'PASS':
            raise ValueError('registration is neither bound claim PASS nor explicit no-map public banner HOLD')
    return fresh


def _timestamp(obj, key, ceiling):
    value = _aware(obj[key])
    if value > ceiling:
        raise ValueError('future activation dependency timestamp: ' + key)
    return value


def _scheduler(root, receipt):
    if receipt.get('standard') != 'VRS-PHASE5-SCHEDULER-READBACK-1':
        raise ValueError('actual scheduler readback required')
    path = _source_path(root, receipt['raw_configuration'])
    raw = path.read_bytes()
    try:
        actual = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        actual = tomllib.loads(raw.decode())
    if actual != receipt.get('automation') or not isinstance(actual, dict):
        raise ValueError('scheduler fields do not match captured actual configuration bytes')
    return actual


def _gate_successor(root, receipt, provenance, install, manifest, original_merge, original_checks, activated, targets):
    """Require an actual gate-only successor release without replacing PR50 evidence."""
    source = provenance.gate_successor if provenance is not None else None
    if source is None:
        if original_merge['release_commit'] != install.get('release_commit'):
            raise ValueError('original PR50 release differs from installed release without a gate successor')
        return _timestamp(original_merge, 'observed_at_utc', activated)
    successor = _load_source(root, source)
    fields = {'standard', 'status', 'tree_root', 'repository', 'original_merge_review',
              'original_after_manifest', 'after_manifest', 'release_commit', 'observed_at_utc',
              'pull_request_readback', 'checks_readback', 'action_run_readbacks', 'git_readback'}
    if (set(successor) != fields or successor['standard'] != 'VRS-PHASE5-GATE-SUCCESSOR-MERGE-1'
            or successor['status'] != 'MERGED_REQUIRED_CHECKS_PASS' or successor['tree_root'] != str(root)
            or successor['repository'] != 'jdhart81/viridis-canon'
            or successor['original_merge_review'] != receipt['proofs']['merge_review']
            or successor['after_manifest'] != receipt['proofs']['after_manifest']
            or successor['original_after_manifest'].get('sha256') != APPROVED_ORIGINAL_AFTER_MANIFEST_SHA256
            or successor['release_commit'] != install.get('release_commit')
            or re.fullmatch(r'[0-9a-f]{40}', str(successor['release_commit'])) is None
            or successor['release_commit'] == original_merge['release_commit']):
        raise ValueError('closed actual gate-only successor merge and installed release required')
    old_manifest = _load_source(root, successor['original_after_manifest'])
    old_rows = {row.get('relative_path'): row for row in old_manifest.get('snapshots', []) if isinstance(row, dict)}
    new_rows = {row.get('relative_path'): row for row in manifest['snapshots']}
    runtime_guard = 'RESEARCH_PIPELINE_v2/verification_coverage_gates/nightly_coverage.py'
    if (len(old_rows) != len(old_manifest.get('snapshots', [])) or set(old_rows) != targets
            or old_rows[runtime_guard].get('after_sha256') != ORIGINAL_ACTIVATION_GUARD_SHA256
            or any(new_rows[p].get('after_sha256') != old_rows[p].get('after_sha256') for p in targets - {runtime_guard})):
        raise ValueError('original complete manifest or unchanged 21 runtime targets differ')
    pr = _load_source(root, successor['pull_request_readback'])
    head = pr.get('headRefOid')
    if (not isinstance(pr.get('number'), int) or isinstance(pr['number'], bool) or pr['number'] <= 50
            or pr.get('state') != 'MERGED' or pr.get('baseRefName') != 'main'
            or pr.get('mergeCommit', {}).get('oid') != successor['release_commit']
            or re.fullmatch(r'[0-9a-f]{40}', str(head)) is None
            or pr.get('url') != 'https://github.com/jdhart81/viridis-canon/pull/' + str(pr['number'])):
        raise ValueError('actual own gate-successor PR/head/main/merge readback required')
    checks = _provenance_json(_source_path(root, successor['checks_readback']).read_bytes())
    required = Counter((row.get('name'), row.get('workflow')) for row in original_checks)
    actual_checks = Counter((row.get('name'), row.get('workflow')) for row in checks if isinstance(row, dict)) if isinstance(checks, list) else Counter()
    if (not isinstance(checks, list) or not checks or any(name is None for name, workflow in required)
            or any(actual_checks[identity] < count for identity, count in required.items())
            or len({(row.get('name'), row.get('workflow'), row.get('link')) for row in checks if isinstance(row, dict)}) != len(checks)
            or any(not isinstance(row, dict) or row.get('bucket') != 'pass'
                   or row.get('state') != 'SUCCESS' for row in checks)):
        raise ValueError('complete original-required plus successor check set must all pass')
    runs = successor['action_run_readbacks']
    if not isinstance(runs, list) or not runs:
        raise ValueError('bound exact-head Actions run readbacks required')
    readbacks = {}
    for ref in runs:
        run = _load_source(root, ref)
        identity = run.get('id')
        if (not isinstance(identity, int) or isinstance(identity, bool) or identity <= 0 or identity in readbacks
                or run.get('head_sha') != head or run.get('status') != 'completed' or run.get('conclusion') != 'success'):
            raise ValueError('successor Actions run is duplicate, pending, failed, or for a different head')
        readbacks[identity] = run
    linked = set()
    linked_by_identity = {}
    for row in checks:
        match = re.fullmatch(r'https://github\.com/jdhart81/viridis-canon/actions/runs/([1-9][0-9]*)/job/([1-9][0-9]*)', str(row.get('link')))
        if match is None or int(match[1]) not in readbacks:
            raise ValueError('successor check lacks an own exact-head terminal run source')
        linked.add(int(match[1]))
        linked_by_identity.setdefault((row.get('name'), row.get('workflow')), set()).add(int(match[1]))
    if any(len(linked_by_identity.get(identity, set())) < count for identity, count in required.items()):
        raise ValueError('duplicate required checks lack distinct exact-head terminal run sources')
    if linked != set(readbacks):
        raise ValueError('unused or missing successor Actions run readback')
    git = _load_source(root, successor['git_readback'])
    if (set(git) != {'standard', 'repository', 'original_release_commit', 'release_commit', 'head_commit', 'ancestry', 'changed_files'}
            or git['standard'] != 'VRS-PHASE5-GATE-SUCCESSOR-GIT-READBACK-1'
            or git['repository'] != successor['repository']
            or git['original_release_commit'] != original_merge['release_commit']
            or git['release_commit'] != successor['release_commit'] or git['head_commit'] != head
            or git['ancestry'] != {'argv': ['git', 'merge-base', '--is-ancestor', original_merge['release_commit'], successor['release_commit']],
                                   'exit_code': 0, 'stdout': '', 'stderr': ''}):
        raise ValueError('actual original PR50 ancestry/source release is not established')
    rows = git['changed_files']
    if not isinstance(rows, list) or not rows:
        raise ValueError('complete hash-bound successor Git diff required')
    paths = [row.get('path') for row in rows if isinstance(row, dict)]
    if len(paths) != len(rows) or len(set(paths)) != len(paths):
        raise ValueError('unique complete successor Git changed-file inventory required')
    guard = '00_lab_infrastructure/gates/nightly_coverage.py'
    optional = {'00_lab_infrastructure/gates/ACTIVATION_PROVENANCE_RESOLUTION.md',
                '00_lab_infrastructure/gates/test_phase5_production_snapshots.py'}
    required = {guard, '00_lab_infrastructure/gates/test_activation_historical_provenance.py'}
    prefix = '00_lab_infrastructure/gates/production_snapshots/phase5-20261005-provenance-closure/'
    copied = dict(APPROVED_ORIGINAL_TRACKED_SNAPSHOT_FILES)
    runtime_guard_suffix = 'RESEARCH_PIPELINE_v2/verification_coverage_gates/nightly_coverage.py'
    added_snapshots = {'AFTER_MANIFEST_PRE_PROVENANCE_20261005.json', 'CURRENT_BEFORE_OBSERVATION.json',
                       'provenance_before/' + runtime_guard_suffix, 'provenance_after/' + runtime_guard_suffix}
    snapshots = {prefix + p for p in set(copied) | added_snapshots}
    pr_files = pr.get('files')
    if (not isinstance(pr_files, list) or any(not isinstance(row, dict) for row in pr_files)
            or len({row.get('path') for row in pr_files}) != len(pr_files)
            or {row.get('path') for row in pr_files} != set(paths)):
        raise ValueError('successor Git diff inventory differs from the actual complete PR file readback')
    if not required | snapshots <= set(paths) or not set(paths) <= required | optional | snapshots:
        raise ValueError('successor changes a file outside the closed gate/test/snapshot scope')
    guard_row = None
    for row in rows:
        if set(row) != {'path', 'status', 'before_sha256', 'after_sha256', 'after_source'}:
            raise ValueError('closed successor Git file/hash/source row required')
        if row['status'] not in {'A', 'M'} or (row['status'] == 'A') != (row['before_sha256'] is None):
            raise ValueError('successor may neither delete nor rename protected/source files')
        if row['before_sha256'] is not None:
            _sha(row['before_sha256'])
        if _sha(row['after_sha256']) != row['after_source'].get('sha256'):
            raise ValueError('successor Git blob hash differs from captured source bytes')
        _source_path(root, row['after_source'])
        if row['path'].startswith(prefix):
            suffix = row['path'][len(prefix):]
            expected = copied.get(suffix) if suffix != 'AFTER_MANIFEST.json' else successor['after_manifest']['sha256']
            if suffix == 'AFTER_MANIFEST_PRE_PROVENANCE_20261005.json':
                expected = APPROVED_ORIGINAL_AFTER_MANIFEST_SHA256
            elif suffix == 'provenance_before/' + runtime_guard_suffix:
                expected = old_rows[runtime_guard]['after_sha256']
            elif suffix == 'provenance_after/' + runtime_guard_suffix:
                expected = new_rows[runtime_guard]['after_sha256']
            if row['status'] != 'A' or (expected is not None and row['after_sha256'] != expected):
                raise ValueError('successor immutable copied snapshot or before/after bytes differ')
        if row['path'] == guard:
            guard_row = row
    if (guard_row['status'] != 'M'
            or guard_row['before_sha256'] != old_rows[runtime_guard]['after_sha256']
            or guard_row['after_sha256'] != new_rows[runtime_guard]['after_sha256']):
        raise ValueError('successor guard source does not bind exact original and installed module hashes')
    original_at = _timestamp(original_merge, 'observed_at_utc', activated)
    successor_at = _timestamp(successor, 'observed_at_utc', activated)
    if original_at > successor_at:
        raise ValueError('successor merge predates the actual original PR50 merge review')
    return successor_at


def validate_activation_receipt(root, receipt, *, now):
    """Validate immutable actual operation evidence; this never activates anything."""
    root = Path(root).resolve(strict=True)
    expected_keys = {'standard', 'status', 'tree_root', 'generation_root', 'scheduler_id', 'timezone',
                     'activated_at_utc', 'premise_declaration_cutover_run', 'first_eligible_window', 'sources', 'proofs'}
    if isinstance(receipt, dict) and set(receipt) == expected_keys | {'authorized_runtime_update'}:
        from phase7_runtime_update import unwrap_activation
        receipt = unwrap_activation(root, receipt, now=now)
    if not isinstance(receipt, dict) or set(receipt) != expected_keys:
        raise ValueError('closed enforcement activation receipt fields required')
    if receipt['standard'] != ACTIVATION_STANDARD or receipt['status'] != 'ENFORCEMENT_ACTIVATED':
        raise ValueError('completed enforcement activation receipt required')
    if receipt['tree_root'] != str(root) or receipt['timezone'] != 'America/New_York':
        raise ValueError('activation root/timezone differs')
    from mirror_parity import GENERATION_ROOT
    if receipt['generation_root'] != str(GENERATION_ROOT) or receipt['scheduler_id'] != 'viridis-nightly-science-generator':
        raise ValueError('activation generation root or existing scheduler identity differs')
    activated = _aware(receipt['activated_at_utc'])
    if now.tzinfo is None or activated > now:
        raise ValueError('future or timezone-naive enforcement activation')
    cutoff = ordinary_run(receipt['premise_declaration_cutover_run'])
    floor = first_eligible_window(activated)
    if receipt['first_eligible_window'] != floor:
        raise ValueError('first eligible window is not the derived future NY calendar boundary')
    if (not isinstance(receipt['sources'], dict) or set(receipt['sources']) != ACTIVATION_SOURCES
            or not isinstance(receipt['proofs'], dict)
            or set(receipt['proofs']) not in (ACTIVATION_PROOFS, ACTIVATION_PROOFS | {HISTORICAL_PROVENANCE_PROOF})):
        raise ValueError('complete exact activation source/proof set required')
    sources = {k: _load_source(root, v) for k, v in receipt['sources'].items()}
    proofs = {k: _load_source(root, v) for k, v in receipt['proofs'].items()}
    provenance = (_HistoricalProvenance(root, receipt)
                  if HISTORICAL_PROVENANCE_PROOF in receipt['proofs'] else None)
    _nested_sources(root, receipt, provenance=provenance)
    if provenance is not None:
        provenance.require_complete()
    install, manifest, merge = sources['installation'], proofs['after_manifest'], proofs['merge_review']
    gate_modules = {'certificate_inspection', 'claim_binding', 'corpus_ledger', 'doi_audit', 'doi_triage',
                    'mirror_parity', 'production_hooks', 'publication_gate', 'run_flow', 'static_pregate',
                    'theorem_coverage', 'publication_binding', 'manuscript_structure', 'release_packet',
                    'nightly_coverage', 'nightly_publication_intake', 'premise_declaration'}
    TARGETS = {'RESEARCH_PIPELINE_v2/verification_coverage_gates/' + name + '.py' for name in gate_modules} | {
        '_ZENODO_DEPOSITS/publish_dated_bundles.py', '_ZENODO_DEPOSITS/weekend_canon_lockstep.py',
        '_ZENODO_DEPOSITS/release_coherence.py', 'RESEARCH_PIPELINE_v2/nightly_checkpoint.py',
        'RESEARCH_PIPELINE_v2/issue_lean_zero_sorry_certificate.py'}
    if (install.get('standard') != 'VRS-PHASE5-HOOK-INSTALL-1'
            or install.get('status') != 'INSTALLED_HASH_READBACK_PASS' or install.get('root') != str(root)
            or install.get('manifest_sha256') != receipt['proofs']['after_manifest']['sha256']):
        raise ValueError('exact installed hash-readback FINISH/manifest required')
    installed, rows = install.get('installed'), manifest.get('snapshots')
    if not isinstance(installed, list) or not isinstance(rows, list):
        raise ValueError('installed target and manifest tables required')
    target_rows = {e.get('path'): e for e in installed if isinstance(e, dict)}
    manifest_rows = {e.get('relative_path'): e for e in rows if isinstance(e, dict)}
    if len(target_rows) != len(installed) or set(target_rows) != TARGETS or len(manifest_rows) != len(rows) or set(manifest_rows) != TARGETS:
        raise ValueError('exact complete 22 installed/manifest target set required')
    for relative, entry in target_rows.items():
        if _sha(entry.get('after_sha256')) != _sha(manifest_rows[relative].get('after_sha256')):
            raise ValueError('installed target hash differs from reviewed final manifest')
        from phase7_runtime_update import current_runtime_binding
        _source_path(root, current_runtime_binding(root, relative, entry['after_sha256'], receipt, now=now))
    if (merge.get('standard') != 'VRS-PHASE5-MERGE-REVIEW-1' or merge.get('status') != 'MERGED_REQUIRED_CHECKS_PASS'
            or not isinstance(merge.get('release_commit'), str) or re.fullmatch(r'[0-9a-f]{40}', merge['release_commit']) is None):
        raise ValueError('independently captured merge and required CI proof required')
    pr = _load_source(root, merge['pull_request_readback'])
    checks_path = _source_path(root, merge['checks_readback'])
    checks = json.loads(checks_path.read_bytes())
    if (pr.get('number') != 50 or pr.get('state') != 'MERGED'
            or pr.get('mergeCommit', {}).get('oid') != merge['release_commit']
            or not isinstance(checks, list) or not checks or
            any(not isinstance(e, dict) or e.get('bucket') != 'pass' for e in checks)):
        raise ValueError('actual PR50 merge/check readbacks do not establish a complete required pass')
    merged_at = _gate_successor(root, receipt, provenance, install, manifest, merge, checks, activated, TARGETS)
    baseline, protected = proofs['protected_baseline'], sources['protected_readback']
    if (baseline.get('standard') != 'VRS-PROTECTED-IMPLEMENTATION-BASELINE-1'
            or baseline.get('canonical_pipeline_root') != str(root / 'RESEARCH_PIPELINE_v2')
            or protected.get('status') != 'LIVE_PROTECTED_HASH_READBACK_PASS'
            or protected.get('baseline_sha256') != receipt['proofs']['protected_baseline']['sha256']):
        raise ValueError('actual protected post-install readback and exact reconciled baseline required')
    reconciliation = baseline.get('deployed_f2g_baseline_reconciliation', {})
    if (protected.get('approved_overlay_release') != reconciliation.get('release_commit')
            or protected.get('approved_overlay_manifest_sha256') != reconciliation.get('overlay_manifest_sha256')):
        raise ValueError('protected readback does not bind the authoritative F2G reconciliation')
    remote = {**baseline.get('deployed_pre_f2h_sha256', {}), **baseline.get('protected_remote_implementation_sha256', {})}
    remote.update({e['path']: e['deployed_authority_sha256'] for e in reconciliation.get('changes', [])})
    local = {**baseline.get('protected_implementation_sha256', {}), **baseline.get('unchanged_support_sha256', {})}
    expected = {('DEPLOYED_DROPLET', k): _sha(v) for k, v in remote.items()}
    expected.update({('CANONICAL_LOCAL', str(root / 'RESEARCH_PIPELINE_v2' / k)): _sha(v) for k, v in local.items()})
    observed = protected.get('checks')
    if not isinstance(observed, list) or any(not isinstance(e, dict) for e in observed):
        raise ValueError('actual protected target readback table required')
    joined = {(e.get('surface'), e.get('path')): e for e in observed}
    if len(joined) != len(observed) or set(joined) != set(expected):
        raise ValueError('protected readback omits or adds an authoritative local/remote target')
    for identity, expected_hash in expected.items():
        entry = joined[identity]
        if entry.get('expected_sha256') != expected_hash or entry.get('actual_sha256') != expected_hash or entry.get('match') is not True:
            raise ValueError('protected actual/expected hash differs')
    if receipt['proofs']['registration_plan']['sha256'] != APPROVED_REGISTRATION_PLAN_SHA256:
        raise ValueError('original exact approved 27-registration plan SHA-256 required')
    plan, snapshot = proofs['registration_plan'], sources['registration_ledger']
    if plan.get('tree_root') != str(root) or snapshot.get('premise_declaration_cutover_run') != receipt['premise_declaration_cutover_run']:
        raise ValueError('registration baseline root or cutover differs')
    _registrations(root, snapshot, plan)
    observation = sources['source_observation']
    if (observation.get('standard') != 'VRS-PHASE5-CUTOVER-OBSERVATION-1'
            or observation.get('tree_root') != str(root) or observation.get('generation_root') != receipt['generation_root']
            or observation.get('next_run') != receipt['premise_declaration_cutover_run']
            or observation.get('next_run_sealed') is not False):
        raise ValueError('actual next ordinary run source/mirror observation required')
    latest = ordinary_run(observation.get('latest_run'))
    if cutoff != latest + 1:
        raise ValueError('cutover does not follow the observed latest ordinary run')
    for key, expected_root in (('generation_state', receipt['generation_root']), ('mirror_state', str(root))):
        state = _load_source(root, observation[key])
        run_ids = state.get('run_ids')
        if (state.get('root') != expected_root or not isinstance(run_ids, list) or not run_ids
                or len(run_ids) != len(set(run_ids)) or max(ordinary_run(r) for r in run_ids) != latest
                or receipt['premise_declaration_cutover_run'] in run_ids):
            raise ValueError('captured source/mirror state selects a stale or wrong cutover')
    current = _scheduler(root, sources['scheduler_readback'])
    previous = _scheduler(root, proofs['scheduler_before'])
    if current.get('id') != receipt['scheduler_id'] or previous.get('id') != receipt['scheduler_id'] or current.get('status') != 'ACTIVE':
        raise ValueError('same existing ACTIVE scheduler required')
    allowed_scheduler_changes = {'prompt', 'updated_at', 'next_run_at'}
    if {k: v for k, v in current.items() if k not in allowed_scheduler_changes} != {k: v for k, v in previous.items() if k not in allowed_scheduler_changes}:
        raise ValueError('scheduler cadence/model/settings changed outside the approved prompt')
    rrule = current.get('rrule')
    if not isinstance(rrule, str):
        raise ValueError('actual unchanged four-checkpoint calendar schedule required')
    calendar = dict(part.split('=', 1) for part in rrule.removeprefix('RRULE:').split(';') if '=' in part)
    if (calendar.get('FREQ') != 'DAILY' or calendar.get('BYHOUR') != '1,7,13,19'
            or calendar.get('BYMINUTE', '0') != '0' or calendar.get('BYSECOND', '0') != '0'):
        raise ValueError('scheduler no longer has the approved four daily checkpoints')
    cwd = current.get('cwds', [current.get('cwd')])
    if cwd != [receipt['generation_root']]:
        raise ValueError('scheduler source cwd differs')
    prompt = current.get('prompt')
    if not isinstance(prompt, str):
        raise ValueError('actual enforcing scheduler prompt required')
    commands = [line for line in prompt.splitlines() if 'nightly_checkpoint.py' in line and ('--begin' in line or '--finish' in line)]
    if (not any('--begin' in line for line in commands) or not any('--finish' in line for line in commands)
            or any('--enforce-new-artifacts' not in line for line in commands)
            or '--require-premise-declaration' not in prompt
            or not all(token in prompt for token in ('foundation_basis', 'SEALED_RUN_MANIFEST', 'SEALED_CLAIM_INVENTORY'))):
        raise ValueError('actual finish/replay enforcement and explicit new-run premise issuance/sealing missing')
    started = _timestamp(install, 'started_at_utc', activated)
    installed_at = _timestamp(install, 'completed_at_utc', activated)
    protected_at = _timestamp(protected, 'at_utc', activated)
    ledger_at = _timestamp(snapshot, 'activation_snapshot_observed_at_utc', activated)
    source_at = _timestamp(observation, 'observed_at_utc', activated)
    scheduler_at = _timestamp(sources['scheduler_readback'], 'observed_at_utc', activated)
    if not merged_at <= started <= installed_at <= protected_at <= ledger_at <= source_at <= scheduler_at <= activated:
        raise ValueError('reversed activation operation/readback chronology')
    return {'activated_at_utc': activated.isoformat(), 'first_eligible_window': floor,
            'premise_declaration_cutover_run': receipt['premise_declaration_cutover_run'],
            'registration_plan': plan, 'receipt': receipt}


def load_enforcement_activation(root, ledger=None, *, now=None):
    """Only the canonical SSOT can nominate activation; no timestamp/CLI override."""
    now = now or dt.datetime.now(dt.timezone.utc)
    root = Path(root).resolve(strict=True)
    canonical = root / 'RESEARCH_PIPELINE_v2/corpus_ledger.json'
    if canonical.is_symlink() or not canonical.is_file():
        raise ValueError('regular authoritative coverage ledger required')
    authoritative = json.loads(canonical.read_bytes())
    if not isinstance(authoritative, dict) or authoritative.get('tree_root') != str(root):
        raise ValueError('authoritative activation ledger root differs')
    if ledger is not None and ledger != authoritative:
        raise ValueError('caller activation ledger differs from authoritative SSOT bytes')
    evidence = activation_binding(authoritative.get('enforcement_activation'))
    if not Path(evidence['path']).is_relative_to('reports/verification-coverage'):
        raise ValueError('activation receipt outside canonical reports root')
    receipt = _load_source(root, evidence)
    activation = validate_activation_receipt(root, receipt, now=now)
    if authoritative.get('premise_declaration_cutover_run') != activation['premise_declaration_cutover_run']:
        raise ValueError('authoritative cutover differs from immutable activation')
    _registrations(root, authoritative, activation['registration_plan'])
    activation['binding'] = evidence
    return activation


def validate_report_activation(root, report, activation):
    """Re-read the hash-bound per-cycle SSOT snapshot; report fields are not authority."""
    if report.get('enforcement_activation') != activation['binding']:
        raise ValueError('report activation binding missing or differs')
    snapshot = _load_source(root, report.get('coverage_ledger'))
    if snapshot.get('enforcement_activation') != activation['binding'] or snapshot.get('premise_declaration_cutover_run') != activation['premise_declaration_cutover_run']:
        raise ValueError('cycle ledger activation binding/cutover differs')
    _registrations(root, snapshot, activation['registration_plan'])
    if report.get('coverage') != {key: snapshot[key] for key in COVERAGE_FIELDS}:
        raise ValueError('report coverage differs from pinned cycle ledger snapshot')
    return snapshot


def checkpoint_window(root: Path, report: dict, now: dt.datetime, *, activation=None) -> tuple[str, dict]:
    """Re-read immutable START/FINISH bytes rather than trusting a report's date."""
    root = root.resolve()
    receipt = report['checkpoint']
    checkpoint = Path(receipt['path']).resolve(strict=True)
    if not checkpoint.is_relative_to(root / 'RESEARCH_PIPELINE_v2/nightly_checkpoints') or checkpoint.name != 'FINISH.json':
        raise ValueError('checkpoint outside canonical checkpoint root')
    if binding(checkpoint)['sha256'] != receipt['sha256']:
        raise ValueError('checkpoint hash mismatch')
    start_path = checkpoint.with_name('START.json')
    start, finish = json.loads(start_path.read_text()), json.loads(checkpoint.read_text())
    if any(obj.get('standard') != 'VRS-NIGHTLY-CHECKPOINT-1' for obj in (start, finish)):
        raise ValueError('checkpoint standard mismatch')
    if start.get('invocation_id') != checkpoint.parent.name or finish.get('invocation_id') != start['invocation_id']:
        raise ValueError('checkpoint invocation mismatch')
    if finish.get('start_receipt_sha256') != binding(start_path)['sha256']:
        raise ValueError('FINISH does not bind START bytes')
    started, completed = _aware(start['started_at_utc']), _aware(finish['completed_at_utc'])
    observed = _aware(report['observed_at_utc'])
    if not started <= completed <= observed <= now:
        raise ValueError('future or reversed checkpoint/report timestamps')
    if finish.get('started_at_utc') != start['started_at_utc']:
        raise ValueError('checkpoint start timestamp changed')
    generation = finish['generation']
    window = generation['window']
    day = dt.date.fromisoformat(window['window_id'])
    lower = dt.datetime.combine(day, dt.time(1), TZ).astimezone(dt.timezone.utc)
    upper = dt.datetime.combine(day + dt.timedelta(days=1), dt.time(1), TZ).astimezone(dt.timezone.utc)
    if window.get('standard') != 'VRS-NIGHTLY-WINDOW-1' or window.get('timezone') != 'America/New_York':
        raise ValueError('generation window standard mismatch')
    if _aware(window['starts_at_utc']) != lower or _aware(window['ends_at_utc']) != upper:
        raise ValueError('generation window is not the real nightly window')
    generated = _aware(generation['generated_at_utc'])
    if not lower <= generated <= completed < upper:
        raise ValueError('generation did not satisfy the checkpoint window')
    if activation is not None:
        activated = _aware(activation['activated_at_utc'])
        if lower < activated or started < activated or generated < activated:
            raise PreActivationIneligible('PRE_ACTIVATION_INELIGIBLE: window/START/generation precedes completed activation')
        if window.get('satisfied') is not True:
            raise ValueError('generation did not satisfy the checkpoint window')
        snapshot = validate_report_activation(root, report, activation)
        latest = generation.get('latest_run')
        if ordinary_run(latest) < ordinary_run(activation['premise_declaration_cutover_run']):
            raise ValueError('generated ordinary run precedes premise-declaration cutover')
        gate = report.get('new_artifact_publication_gate', {})
        joined = [e for e in snapshot.get('publication_entities', []) if e.get('run_id') == latest]
        joined = joined or [e for e in snapshot.get('run_entities', []) if e.get('id') == latest and e.get('kind') == 'PAPER']
        if len(joined) != 1 or gate.get('entity_id') != joined[0]['id']:
            raise ValueError('new-artifact gate is not joined to the exact generated run')
        if gate.get('premise_declaration_required') is not True or gate.get('premise_declaration', {}).get('status') != 'PASS':
            raise ValueError('actual required premise-declaration gate did not PASS')
        # Reuse the real publication/claim/premise consumer against the pinned
        # snapshot, never a caller's self-declared gate PASS. Source is read only
        # for parity; the Comparator-bound certificate remains proof authority.
        source_runs = [e for e in snapshot.get('run_entities', []) if e.get('id') == latest and e.get('kind') == 'PAPER']
        if len(source_runs) != 1:
            raise ValueError('generated run has no unique source/mirror parity row')
        from mirror_parity import run_parity
        parity = run_parity(root, source_runs[0]['path'])
        if parity.get('status') != 'MATCH' or parity.get('errors') or parity.get('differences'):
            raise ValueError('fresh generated-run source/mirror parity failed')
        from publication_gate import evaluate_publication
        fresh_gate = evaluate_publication(root / joined[0]['path'], snapshot,
                                         entity_id=joined[0]['id'], enforce=True,
                                         require_premise_declaration=True)
        if (fresh_gate.get('status') != 'PASS' or fresh_gate.get('exact_publication_binding') is not True
                or fresh_gate.get('claim_gate', {}).get('status') != 'PASS'
                or fresh_gate.get('premise_declaration_required') is not True
                or fresh_gate.get('premise_declaration', {}).get('status') != 'PASS'):
            raise ValueError('fresh actual publication/claim/premise gate failed')
    if window.get('satisfied') is not True:
        raise ValueError('generation did not satisfy the checkpoint window')
    return day.isoformat(), finish


def _clean(report: dict, finish: dict) -> bool:
    coverage = report.get('coverage', {})
    gate = report.get('new_artifact_publication_gate', {})
    counts = coverage.get('receipt_era', {})
    return (report.get('mode') == 'ENFORCING' and report.get('enforcement') is True
            and report.get('status') == 'ENFORCING_PASS'
            and finish.get('status') == 'NIGHTLY_PROGRESS_PASS' and finish.get('incidents') == []
            and coverage.get('errors') == [] and coverage.get('mirror_drift') == []
            and type(counts.get('total')) is int and type(counts.get('certified')) is int
            and gate.get('status') == 'PASS' and gate.get('exact_publication_binding') is True
            and gate.get('claim_gate', {}).get('status') == 'PASS')


def collect_streak(root: Path, reports: list[Path], *, now: dt.datetime | None = None) -> dict:
    """Count closed consecutive nightly windows once; replay cannot increase the count."""
    now = now or dt.datetime.now(dt.timezone.utc)
    if now.tzinfo is None:
        raise ValueError('now must include timezone')
    grouped, rejected, ineligible = {}, [], []
    local = now.astimezone(TZ)
    current_day = local.date() if local.hour >= 1 else local.date() - dt.timedelta(days=1)
    last_closed = current_day - dt.timedelta(days=1)
    try:
        activation = load_enforcement_activation(root, now=now)
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        return {'standard': 'VRS-SEVEN-NIGHTLY-WINDOWS-1', 'observed_at_utc': now.isoformat(),
                'status': 'HOLD_ENFORCEMENT_ACTIVATION', 'required': 7,
                'consecutive_clean_closed_windows': 0, 'last_closed_window': last_closed.isoformat(),
                'windows': {}, 'ineligible': [],
                'counting_rule': 'Only distinct genuine closed post-activation NY 01:00 windows count; an invalid activation cannot support a streak.',
                'rejected': [{'cause': type(exc).__name__ + ': ' + str(exc)}],
                'proof_execution': False, 'zenodo_writes': False}
    for path in sorted(set(Path(p).resolve() for p in reports)):
        try:
            report = json.loads(path.read_text())
            # Report-only history never counts toward or breaks an enforcing streak.
            if report.get('mode') != 'ENFORCING' or report.get('enforcement') is not True:
                continue
            day, finish = checkpoint_window(Path(root), report, now, activation=activation)
            grouped.setdefault(day, []).append({'report': binding(path), 'clean': _clean(report, finish)})
        except PreActivationIneligible as exc:
            ineligible.append({'report': binding(path), 'status': 'PRE_ACTIVATION_INELIGIBLE', 'cause': str(exc)})
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            rejected.append({'path': str(path), 'cause': type(exc).__name__ + ': ' + str(exc)})
    count, day = 0, last_closed
    while day.isoformat() in grouped and all(row['clean'] for row in grouped[day.isoformat()]):
        count += 1
        day -= dt.timedelta(days=1)
    # Untrusted/malformed enforcing evidence cannot support a clean streak.
    if rejected:
        count = 0
    return {'standard': 'VRS-SEVEN-NIGHTLY-WINDOWS-1', 'observed_at_utc': now.isoformat(),
            'status': 'SEVEN_CLEAN_NIGHTLY_WINDOWS' if count >= 7 else 'PENDING_GENUINE_NIGHTLY_WINDOWS',
            'required': 7, 'consecutive_clean_closed_windows': count,
            'last_closed_window': last_closed.isoformat(), 'windows': grouped, 'rejected': rejected, 'ineligible': ineligible,
            'enforcement_activation': activation['binding'], 'activated_at_utc': activation['activated_at_utc'],
            'first_eligible_window': activation['first_eligible_window'],
            'premise_declaration_cutover_run': activation['premise_declaration_cutover_run'],
            'counting_rule': 'Distinct closed America/New_York 01:00 nightly windows; all enforcing reports in a counted window must be clean; missing dates break the streak.',
            'proof_execution': False, 'zenodo_writes': False}


def weekly_report(root: Path, ledger: dict, checkpoint: dict, *, now: dt.datetime | None = None) -> dict:
    """Persist the first fresh ledger snapshot of each ISO week without rewriting it."""
    now = now or dt.datetime.now(dt.timezone.utc)
    year, week, _ = now.astimezone(TZ).isocalendar()
    output = Path(root) / 'reports/verification-coverage/weekly' / f'{year}-W{week:02}'
    report_path = output / 'WEEKLY_LEDGER_REPORT.json'
    if report_path.exists():
        previous = json.loads(report_path.read_text())
        snapshot = output / 'corpus_ledger.json'
        if previous['ledger']['sha256'] != binding(snapshot)['sha256']:
            raise ValueError('weekly ledger snapshot hash mismatch')
        return previous
    from corpus_ledger import render_markdown
    output.mkdir(parents=True, exist_ok=True)
    snapshot = output / 'corpus_ledger.json'
    with snapshot.open('x') as handle:
        handle.write(json.dumps(ledger, ensure_ascii=False, sort_keys=True, indent=2) + '\n')
    with (output / 'LEDGER.md').open('x') as handle:
        handle.write(render_markdown(ledger))
    report = {'standard': 'VRS-WEEKLY-COVERAGE-1', 'week': f'{year}-W{week:02}',
              'observed_at_utc': now.isoformat(), 'ledger': binding(snapshot), 'checkpoint': checkpoint,
              'coverage': {key: ledger[key] for key in ('file_counts', 'run_counts', 'receipt_era', 'mirror_drift', 'errors')},
              'status': 'HOLD' if ledger['errors'] or ledger['mirror_drift'] else 'REPORTED',
              'zenodo_writes': False, 'proof_execution': False}
    with report_path.open('x') as handle:
        handle.write(json.dumps(report, sort_keys=True, indent=2) + '\n')
    return report
