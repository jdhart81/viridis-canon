"""PRIVATE TEST ONLY bind closed modern runtime DATA into exact source loader."""
from pathlib import Path
from build_source_chain import sha

FIXED_RUNTIME_DATA=frozenset({'LEGACY_CLOSURE','LEGACY_CONSUMER','LEGACY_SCOPE','SESSION_CONSUMER','HISTORICAL_PUBLISHER','DATA_ALIAS_OBSERVATION','PLATFORM_TIMEZONE_OBSERVATION','PREDECESSOR_PROFILE','PREDECESSOR_NOMINATION','PREDECESSOR_PLAN','PREDECESSOR_INSTALLATION','SCIENTIFIC_ALIAS_PATH','SCIENTIFIC_ALIAS_READLINK','PLATFORM_TZ_LOGICAL','PLATFORM_TZ_PHYSICAL','PLATFORM_TZ_LINK_PATHS','LEGACY_TRANSIENT_SOURCES','LEGACY_TRANSIENT_ROOT','TRANSIENT_REHYDRATION_POLICY','PROVIDER_SHA'}|{'V%03d_%s'%(v,f)for v in range(1,12)for f in('PROFILE','NOMINATION','PLAN','INSTALLATION')})

def expression(value):
 if isinstance(value,Path):return 'Path('+repr(str(value))+')'
 if type(value)in(str,bytes,int,float,bool,type(None)):return repr(value)
 if type(value)is dict:return '{'+','.join(expression(k)+':'+expression(v)for k,v in value.items())+'}'
 if type(value)is list:return '['+','.join(expression(v)for v in value)+']'
 if type(value)is tuple:return '('+','.join(expression(v)for v in value)+',)'
 raise ValueError('CLOSED_RUNTIME_DATA_TYPE')

def bind_runtime_data(loader,constructor,current):
 row=next(r for r in current['module_rows']if r['name']=='packaging_runtime.py')
 path=Path(row['path']);raw=path.read_bytes();digest=sha(raw)
 loader.register_source(path,raw)
 assert set(constructor.remaps)<=FIXED_RUNTIME_DATA
 loader.explicit_extra_allowlist[digest]=FIXED_RUNTIME_DATA
 loader.remaps[digest].update({name:expression(value)for name,value in constructor.remaps.items()})
 for row in current['shared_rows']:
  path=Path(row['path']);loader.register_source(path,path.read_bytes())
 for row in current['module_rows']:
  if row['name']=='nightly_manuscript_access.py':continue # external finite platformDATA seam declared separately
  path=Path(row['path']);loader.register_source(path,path.read_bytes())
 return {'runtime_source_sha256':digest,'data_globals':sorted(constructor.remaps),'contextvar_or_validator_remaps':False}
