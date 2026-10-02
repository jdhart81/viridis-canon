"""Read current in-flight receipts without changing the foundry state."""
import hashlib
import json
from pathlib import Path
import re


def binding(path):
    return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def flow(root, row):
    rid = row['id']
    result = {'state': 'CERTIFIED' if row['certificate_valid'] else 'UNCERTIFIED', 'receipts': [], 'causes': []}
    try:
        certdir = root / 'RESEARCH_PIPELINE_v2/lean_certificates' / rid
        cloud_path = certdir / 'COMPARATOR_CLOUD_RECEIPT.json'
        if cloud_path.is_file():
            cloud = json.loads(cloud_path.read_text())
            result['receipts'].append(binding(cloud_path))
            if cloud.get('status') == 'HOLD':
                result['state'] = 'IN_FLIGHT_HELD'
                raw = cloud.get('provider_response', {})
                errors = re.findall(r'error:[^\n]+', raw.get('output', ''))
                result['causes'] += errors or ['Comparator verification did not pass']
        if rid == 'Run-177':
            holds = sorted((root/'RESEARCH_PIPELINE_v2/nightly_checkpoints').glob('*/RUN177_ATTEMPT2_TRANSPORT_SECURITY_HOLD.json'))
            if holds:
                path = holds[-1]
                receipt = json.loads(path.read_text())
                result['receipts'].append(binding(path))
                result['state'] = 'GAP_HOLD_TRANSPORT_SECURITY_REVIEW'
                result['causes'].append(receipt.get('automatic_rejection', {}).get('exact_reason', receipt.get('status','transport HOLD')))
        if rid in ('Run-182','Run-183') and not row['certificate_valid']:
            result['state'] = 'IN_FLIGHT_HELD'
        manifest_path = root/row['path']/'RUN_MANIFEST.json'
        if rid == 'Run-182' and manifest_path.is_file():
            manifest = json.loads(manifest_path.read_text())
            hashes = manifest.get('artifact_sha256', {})
            actual = {str(p.relative_to(manifest_path.parent)) for p in manifest_path.parent.rglob('*') if p.is_file() and p != manifest_path}
            undeclared = sorted(actual-set(hashes))
            if undeclared:
                result['causes'].append('sealed inventory omits: ' + ', '.join(undeclared))
                result['receipts'].append(binding(manifest_path))
        return result
    except (OSError, ValueError, TypeError) as exc:
        result['state'] = 'HOLD_MISSING_OR_MALFORMED_RECEIPT'
        result['causes'].append(str(exc))
        return result
