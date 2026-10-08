"""Exact legacy serialization of already-validated own native PDF previews.

No ignore, returned-field adoption, new server rule or acceptance authority.
The caller must first execute the unchanged full native guard with its actual
source-bound preview context. Every other legacy field remains exact.
"""
from copy import deepcopy
import re
from digest_metadata import check
OWN_ID='23226761'
REQUIRED_CHECKS=frozenset(['content_metadata', 'created_updated_revision_id', 'custom_fields.legacy:communities', 'deletion_status', 'derived_previews', 'expires_at', 'file_entry_order', 'links_and_stats', 'minted_doi_and_existing_concept', 'pids.oai', 'record_identity', 'revision_id', 'swh', 'ui.is_draft', 'ui_display_fields', 'unlisted_fields', 'versions_index_latest_parent'])
SIZES=frozenset({'10','50','100','250','750','1200'})
def project(native,expected,native_audit,sm):
 check(isinstance(native_audit,dict)and native_audit.get('status')=='SERVER_MANAGED_READBACK_PASS'and native_audit.get('operation')=='NEW_VERSION'and native_audit.get('phase')=='DRAFT'and native_audit.get('record_id')==OWN_ID and native_audit.get('checks',{}).get('derived_previews',{}).get('status')=='PASS','DIRECT_FULL_NATIVE_PREVIEW_GUARD_REQUIRED')
 checks=native_audit.get('checks');check(isinstance(checks,dict)and set(checks)==REQUIRED_CHECKS and all(isinstance(row,dict)and row.get('status')=='PASS'for row in checks.values()),'ALL_FULL_NATIVE_GUARD_ROWS_REQUIRED')
 check(native.get('id')==OWN_ID and str(expected.get('id'))==OWN_ID,'OWN_PRIVATE_PREVIEW_RECORD_ONLY')
 result=deepcopy(expected);urls=native.get('links',{}).get('thumbnails')
 if urls is None:
  check(not any(k in expected.get('links',{})for k in('thumb250','thumbs')),'LEGACY_PREVIEW_DISAPPEARANCE_NOT_PREDICTED');return result
 check(isinstance(urls,dict)and set(urls)==SIZES,'CLOSED_NATIVE_THUMBNAIL_SIZE_SET')
 keys={sm._preview_url(url,host='zenodo.org',record_id=OWN_ID,allowed_keys={'paper.pdf'})for url in urls.values()}
 check(keys=={'paper.pdf'}and 'paper.pdf'in native.get('files',{}).get('entries',{}),'APPROVED_OWN_PDF_PREVIEW_ONLY')
 result['links']['thumbs']={size:'https://zenodo.org/record/'+OWN_ID+'/thumb'+size for size in urls}
 result['links']['thumb250']=result['links']['thumbs']['250']
 return result
