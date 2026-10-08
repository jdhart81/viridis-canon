from pathlib import Path
import sys,unittest,sysconfig
from zoneinfo import ZoneInfo
sysconfig.get_config_vars();ZoneInfo('America/New_York')
root=Path.cwd().resolve().parent
standard=[Path(sys.base_prefix).resolve(),Path(sys.prefix).resolve()]
def guard(event,args):
 if event=='open' and args and isinstance(args[0],(str,bytes)):
  p=Path(args[0].decode()if isinstance(args[0],bytes)else args[0]).resolve()
  if not p.is_relative_to(root) and not any(p.is_relative_to(q)for q in standard) and str(p)!='/dev/null':raise RuntimeError('CI_EXTERNAL_FILE_ACCESS_BLOCKED:'+str(p))
 if event in {'socket.connect','socket.getaddrinfo','subprocess.Popen'}:raise RuntimeError('CI_NETWORK_OR_PROCESS_BLOCKED:'+event)
sys.addaudithook(guard)
unittest.main(module=None,argv=['isolated-public-fixtures',*sys.argv[1:]],exit=True)
