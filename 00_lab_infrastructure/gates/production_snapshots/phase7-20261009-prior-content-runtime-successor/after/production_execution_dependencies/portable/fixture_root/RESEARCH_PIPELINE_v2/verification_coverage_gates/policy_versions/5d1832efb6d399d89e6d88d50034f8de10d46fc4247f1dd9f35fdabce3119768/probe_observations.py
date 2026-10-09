"""Decode source-position-bound probe observations; not a verifier.

The caller must first use the unchanged Comparator/issuer and existing
certificate consumer to establish own-job acceptance. Absence is never
interpreted as substantive, and this module never certifies a theorem.
"""
import re
from collections import defaultdict

TAG=re.compile(r'info:\s+(?:/project/)?(Challenge|Solution)\.lean:(\d+):(\d+):\s*\(\s*([012])\s*,\s*"(PHASE7_PROBE:Run-\d{3}:S\d{2})"\s*\)',re.MULTILINE)
TIER={0:'DEFINITIONAL',1:'ROUTINE',2:'SUBSTANTIVE'}

def observation_positions(source):
    result={}
    for no,line in enumerate(source.splitlines(),1):
        m=re.search(r'^#reduce \([^,]+, "(PHASE7_PROBE:Run-\d{3}:S\d{2})"\)$',line)
        if m:
            if m.group(1) in result:raise ValueError('duplicate print label in source')
            result[m.group(1)]={'line':no,'column':0}
    return result

def extract_tags(output,challenge_source,solution_source,expected_labels):
    """Only observed labels; the result is not publication/certification PASS."""
    if not isinstance(output,str):raise ValueError('missing own-job output')
    if not expected_labels or len(set(expected_labels))!=len(expected_labels):raise ValueError('bad expected labels')
    positions={'Challenge':observation_positions(challenge_source),'Solution':observation_positions(solution_source)}
    expected=set(expected_labels)
    if any(set(p)!=expected for p in positions.values()):raise ValueError('source label set mismatch')
    seen=defaultdict(list);matches=list(TAG.finditer(output))
    if output.count('PHASE7_PROBE:')!=len(matches):raise ValueError('unbound or malformed probe marker')
    for m in matches:
        module,line,column,value,label=m.groups()
        if label not in expected:raise ValueError('unexpected probe marker')
        if {'line':int(line),'column':int(column)}!=positions[module][label]:raise ValueError('probe source position mismatch')
        seen[(module,label)].append(int(value))
    result={}
    for label in expected_labels:
        a=seen[('Challenge',label)];b=seen[('Solution',label)]
        if len(a)!=1 or len(b)!=1:raise ValueError('missing or duplicate own-module probe tag')
        if a!=b:raise ValueError('challenge/solution probe disagreement')
        result[label]={'observed_numeric_tier':a[0],'observed_label':TIER[a[0]],'source_positions':{k:p[label] for k,p in positions.items()},'certifies':False,'downgrade_only':True}
    return result
