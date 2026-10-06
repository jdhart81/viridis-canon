"""Authoritative successor inventory; never modifies an earlier publication."""
import re
from zenodo_transport import TransportHold
from publication_preservation import require_file_preservation


def _valid_name(value):
    return (isinstance(value,str) and bool(value) and value not in ('.','..')
            and '/' not in value and '\\' not in value
            and all(ord(c)>=32 and ord(c)!=127 for c in value))


def _valid_size(value):
    return type(value) is int and value>=0


def _valid_md5(value):
    return isinstance(value,str) and re.fullmatch(r'[0-9a-f]{32}',value) is not None


def _approved(approved, prefix):
    if (not isinstance(approved,list) or not approved
        or any(not isinstance(f,dict) or not _valid_name(f.get('name'))
               or not _valid_size(f.get('size')) or not _valid_md5(f.get('md5'))
               for f in approved)):
        raise TransportHold(prefix+'_INPUT')
    names=[f['name'] for f in approved]
    if len(names)!=len(set(names)):raise TransportHold(prefix+'_DUPLICATE_NAME')
    return names


def inventory_plan(inherited, approved):
    names=_approved(approved,'HOLD_INVENTORY')
    if (not isinstance(inherited,list)
        or any(not isinstance(f,dict) or not _valid_name(f.get('filename'))
               or not _valid_size(f.get('filesize')) or not _valid_md5(f.get('checksum'))
               or not isinstance(f.get('id'),str) or not f['id'] for f in inherited)):
        raise TransportHold('HOLD_INVENTORY_INPUT')
    oldnames=[f['filename'] for f in inherited]
    if len(set(oldnames))!=len(oldnames):
        raise TransportHold('HOLD_INVENTORY_DUPLICATE_OR_INVALID_NAME')
    wanted={f['name']:f for f in approved};drop=[];keep=[]
    for old in inherited:
        target=wanted.get(old['filename'])
        if target and target.get('md5')==old.get('checksum') and target.get('size')==old.get('filesize'):
            keep.append(old)
        else:
            drop.append({'name':old['filename'],'size':old['filesize'],'checksum':old['checksum'],'file_id':old['id'],'reason':'REPLACE_DIFFERENT_CERTIFIED_BYTES' if target else 'NOT_IN_APPROVED_INVENTORY','original_entry':old})
    return {'drop':drop,'keep':keep,'upload':[f for f in approved if f['name'] not in {x['filename'] for x in keep}]}


def require_approved_inventory(entries, approved, *, exact_entries=None):
    names=_approved(approved,'READBACK_MISMATCH_APPROVED_INVENTORY')
    if not isinstance(entries,dict):
        raise TransportHold('READBACK_MISMATCH_APPROVED_INVENTORY_INPUT')
    if set(entries)!=set(names):raise TransportHold('READBACK_MISMATCH_APPROVED_FILENAME_SET')
    for f in approved:
        row=entries[f['name']]
        if not isinstance(row,dict) or row.get('key')!=f['name'] or not _valid_size(row.get('size')) or row['size']!=f['size'] or row.get('checksum')!='md5:'+f['md5']:
            raise TransportHold('READBACK_MISMATCH_APPROVED_FILE_BYTES:'+f['name'])
    if exact_entries is not None:
        if (not isinstance(exact_entries,dict) or set(exact_entries)!=set(names)
            or any(not isinstance(v,dict) or v.get('key')!=k for k,v in exact_entries.items())):
            raise TransportHold('READBACK_MISMATCH_APPROVED_INVENTORY_INPUT')
        return require_file_preservation(list(entries.values()),list(exact_entries.values()))
    return {'mode':'EXACT_APPROVED_FILENAME_SIZE_CHECKSUM_SET','count':len(entries)}
