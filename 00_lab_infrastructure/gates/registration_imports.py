"""Source-bound namespace for the four unchanged private readback helpers.

No verdict is added and no data/transport/field rule is modified. This composes
imports only, for ordinary callers that do not already use the complete runtime
source session. Source paths and hashes are the existing approved runtime pins.
"""
from __future__ import annotations
import contextlib,hashlib,importlib.abc,importlib.machinery,importlib.util
from pathlib import Path
import sys

SOURCES=(
 ('server_managed_fields','reports/verification-coverage/2026-10-05/game-plan-completion/canon-hub-successor-execution-v003/server_managed_fields.py','ce8ad2002a11938966201a44d2714ee866bb922649cd572e36f09e8cc0f062a1'),
 ('publication_preservation','reports/verification-coverage/2026-10-04/game-plan-completion/late-version-chain-consolidated-review-v004/implementation/publication_preservation.py','4fb48f40fd76cae1f973dca66253813bfd1c8edcdffa07c02945d28ddf170e2b'),
 ('file_byte_metadata','reports/verification-coverage/2026-10-05/game-plan-completion/canon-hub-successor-execution-v003/file_byte_metadata.py','4a21de5efd74531b135682f92ce4d49b1d8ad71d044795548ea9877756fa50ef'),
 ('zenodo_transport','reports/verification-coverage/2026-10-05/game-plan-completion/canon-hub-successor-execution-v003/zenodo_transport.py','69bcfa0c7008f052a0c30d06d23e94a226c5b40707905550e41c40e16c379b65'),
)
class NamespaceHold(ValueError):pass

def _read_source(root,relative,expected):
 p=root/relative
 if not p.resolve(strict=True).is_relative_to(root)or not p.is_file()or any(q.is_symlink()for q in(p,*p.parents)):raise NamespaceHold('regular contained unchanged readback source required')
 first=p.stat();raw=p.read_bytes();last=p.stat()
 if (first.st_ino,first.st_size,first.st_mtime_ns)!=(last.st_ino,last.st_size,last.st_mtime_ns)or hashlib.sha256(raw).hexdigest()!=expected:raise NamespaceHold('unchanged readback source hash differs')
 return p,raw

def _verify_cached(root):
 for name,relative,expected in SOURCES:
  p,_=_read_source(root,relative,expected);cached=sys.modules.get(name)
  if cached is not None:
   origin=getattr(cached,'__file__',None)
   if not isinstance(origin,str)or origin!=str(p)or Path(origin).resolve(strict=True)!=p:raise NamespaceHold('foreign cached private readback helper: '+name)

class _Loader(importlib.abc.Loader):
 def __init__(self,root,relative,expected):self.root=root;self.relative=relative;self.expected=expected
 def create_module(self,spec):return None
 def exec_module(self,module):
  p,raw=_read_source(self.root,self.relative,self.expected);module.__file__=str(p)
  exec(compile(raw,str(p),'exec'),module.__dict__)
  _read_source(self.root,self.relative,self.expected)

class _Finder(importlib.abc.MetaPathFinder):
 def __init__(self,root):self.root=root;self.names={name:(relative,expected)for name,relative,expected in SOURCES}
 def find_spec(self,fullname,path=None,target=None):
  if fullname in self.names:
   relative,expected=self.names[fullname];p,_=_read_source(self.root,relative,expected)
   return importlib.util.spec_from_loader(fullname,_Loader(self.root,relative,expected),origin=str(p))
  # The ordinary caller's existing scientific namespace/guard remains intact.
  return None

@contextlib.contextmanager
def source_session(root):
 """Expose exactly the existing approved helpers, preserving the original guard."""
 root=Path(root).resolve(strict=True);_verify_cached(root)
 cached={name:sys.modules[name]for name,_,_ in SOURCES if name in sys.modules};finder=_Finder(root);before_path=list(sys.path);sys.meta_path.insert(0,finder)
 try:yield
 finally:
  if finder in sys.meta_path:sys.meta_path.remove(finder)
  _verify_cached(root)
  if sys.path!=before_path:raise NamespaceHold('readback namespace changed search paths')
  if any(sys.modules.get(name)is not original for name,original in cached.items()):raise NamespaceHold('readback namespace changed existing module identity')
