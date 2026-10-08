"""Polling classification only: a full strict PASS is still required.

No acceptance, metadata normalization, HTTP mutation or general retry rule.
"""
from copy import deepcopy

PENDING='READBACK_MISMATCH_SERVER_MANAGED:PREVIEW_THUMBNAIL_DISAPPEARANCE_REQUIRES_OWN_DELETE'

def preview_pending_only(sm,actual,expected,context,error):
    report=getattr(error,'report',None)
    if not isinstance(report,dict)or report.get('status')!='HOLD':return False
    checks=report.get('checks',{});preview=checks.get('derived_previews',{})
    if preview.get('status')!='HOLD'or preview.get('reason')!=PENDING:return False
    reasons=report.get('reasons')
    if not isinstance(reasons,list)or not reasons or any(r.get('rule')not in {'derived_previews','unlisted_fields','file_entry_order','links_and_stats'}for r in reasons):return False
    if 'thumbnails'in actual.get('links',{})or not isinstance(expected.get('links',{}).get('thumbnails'),dict)or not expected['links']['thumbnails']:return False
    # Removing only this one missing derived display field must let the SAME
    # unchanged closed validator pass. That result grants a GET wait only;
    # the unmodified record must subsequently pass the full validator.
    a,e=deepcopy(actual),deepcopy(expected);e['links'].pop('thumbnails')
    kwargs=dict(context);kwargs.pop('operation',None)
    try:result=sm.validate_new_version(a,e,**kwargs)
    except Exception:return False
    return result.get('status')=='SERVER_MANAGED_READBACK_PASS'
