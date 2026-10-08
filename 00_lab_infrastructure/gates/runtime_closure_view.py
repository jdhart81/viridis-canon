"""Closed runtime/purpose scope composition; never hides a foreign source."""
from __future__ import annotations
import contextlib,hashlib,sys
from pathlib import Path
class ScopeHold(ValueError):pass
def need(v,r):
    if not v:raise ScopeHold('HOLD_'+r)
def verify_own_cache(root,pins):
    root=Path(root).resolve(strict=True);paths={r['path']:r['sha256']for r in pins}
    need(len(paths)==len(pins),'UNIQUE_SOURCE_PATHS')
    for row in pins:
        p=Path(row['path']);need(p.is_absolute()and p.resolve(strict=True).is_relative_to(root)and not any(x.is_symlink()for x in(p,*p.parents))and hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'],'CURRENT_PURPOSE_SOURCE')
    for name,module in list(sys.modules.items()):
        origin=getattr(module,'__file__',None)
        if isinstance(origin,str)and Path(origin).resolve().is_relative_to(root):need(origin in paths and hashlib.sha256(Path(origin).read_bytes()).hexdigest()==paths[origin],'FOREIGN_CACHED_OWN_SOURCE:'+name)
    return paths
@contextlib.contextmanager
def exact_runtime_view(root,purpose_pins,runtime_pins):
    """Remove only proved purpose-only module cache entries, restore identities."""
    paths=verify_own_cache(root,purpose_pins);runtime={r['path']:r['sha256']for r in runtime_pins}
    need(all(paths.get(p)==h for p,h in runtime.items()),'MEASURED_RUNTIME_EXACT_SUBSET')
    hidden={name:module for name,module in list(sys.modules.items())if isinstance(getattr(module,'__file__',None),str)and getattr(module,'__file__')in paths and getattr(module,'__file__')not in runtime}
    for name,module in hidden.items():need(sys.modules.get(name)is module,'CACHE_RACE');sys.modules.pop(name)
    try:
        verify_own_cache(root,runtime_pins);yield
        verify_own_cache(root,runtime_pins)
    finally:
        for name,module in hidden.items():
            need(name not in sys.modules,'PURPOSE_ONLY_IMPORT_IN_RUNTIME_SCOPE');sys.modules[name]=module
        verify_own_cache(root,purpose_pins)

def require_current(consumer,binding,*,root,purpose_pins,bound=None):
    # This pure reader proves the actual closed receipt/table first. It does
    # not admit activation; require_current_closure recomputes that inside the
    # exact measured cache view and restores every purpose identity afterward.
    receipt=consumer.read_bound_closure(binding);runtime=receipt.get('source_pins')
    need(isinstance(runtime,list)and runtime,'BOUND_RUNTIME_SOURCE_TABLE')
    with exact_runtime_view(root,purpose_pins,runtime):return consumer.require_current_closure(binding)
