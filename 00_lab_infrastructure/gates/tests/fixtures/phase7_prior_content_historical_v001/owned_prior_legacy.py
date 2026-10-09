"""Complete predecessor legacy closure after the unchanged paired native audit.

Only existing native-to-legacy scalars and the already audited latest flag
are serialized. All remaining legacy keys, metadata and main bytes stay exact.
"""
from copy import deepcopy
from digest_metadata import check,exact

def require_prior_legacy(actual,saved,native,source_native,*,sm,preservation,chain=None):
    rid=source_native.get('id')
    check(isinstance(rid,str)and native.get('id')==rid,'PRIOR_ID')
    context={'host':'zenodo.org','record_id':rid,'phase':'PUBLISHED'}
    if chain is not None:context.update(version_chain_context=chain,own_operation_record_id=chain['successor_record_id'])
    sm.validate_prior_version(native,source_native,**context)
    expected=deepcopy(saved)
    for legacy_key,native_key in (('modified','updated'),('updated','updated'),('revision','revision_id'),('links','links')):
        if legacy_key in expected:
            check(native_key in native,'AUDITED_PRIOR_SERIALIZER_SOURCE:'+native_key)
            expected[legacy_key]=deepcopy(native[native_key])
    relation=expected.get('metadata',{}).get('relations',{})
    check(set(relation)=={'version'}and isinstance(relation['version'],list)and len(relation['version'])==1,'CLOSED_PRIOR_VERSION_RELATION')
    row=relation['version'][0];index=source_native.get('versions',{}).get('index');parent=source_native.get('parent',{}).get('id')
    check(set(row)=={'index','is_last','parent'}and type(index)is int and index>=1 and row['index']==index-1 and row['is_last']is source_native['versions']['is_latest']and row['parent']=={'pid_type':'recid','pid_value':parent},'SOURCE_PRIOR_ORDINAL_FLAG_PARENT')
    check(native['versions']['index']==index and type(native['versions']['is_latest'])is bool,'AUDITED_PRIOR_VERSION_STATE')
    row['is_last']=native['versions']['is_latest']
    preservation.require_public_metadata(actual['metadata'],expected['metadata'])
    preservation.require_file_preservation(actual['files'],expected['files'])
    left,right=deepcopy(actual),deepcopy(expected)
    for key in('metadata','files','stats'):left.pop(key,None);right.pop(key,None)
    check(exact(left,right),'PRIOR_LEGACY_UNLISTED_OR_SCALAR_CHANGED')
    sm.require_links_stats({'links':actual.get('links',{}),'stats':actual.get('stats',{}),'pids':native['pids']},{'links':expected['links'],'stats':{}},host='zenodo.org',record_id=rid)
    return expected
