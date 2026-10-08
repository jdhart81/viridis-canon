"""Exact unchanged weekly-wrapper typography through the closed cached renderer.

No note or public-status admission is implemented. The original default scope
consumers supply the current note bytes before and after typesetting. This
purpose callback never downloads, certifies, writes SSOT or calls Zenodo.
"""
from pathlib import Path
import datetime as dt,hashlib,json,os,subprocess
import methods_digest as d
ROOT=Path('/Users/justinhart/Desktop/Cowork /Viridis Core docs 2.0')
MANIFEST=ROOT/'reports/verification-coverage/2026-10-06/phase-7-science-catchup-v001/runtime-install-v001/RENDERER_CACHE_MANIFEST.json'
MANIFEST_SHA='d312006417a3eef3fca66a51db558b1853476cd9a8ed0479fe04ed351f8a9dc4'
BINARY_SHA='568dea0a81f4ceed859e33734bbbea85d54a25f14b12665a48c98b536a887986'
DIGEST_SOURCE_SHA='5fcdc53f68d008357e0aef1dbb93f74695aa91119792f78151a8c61a0a9e05e5'
EXECUTABLE=Path('/opt/homebrew/bin/tectonic')
PROLOGUE=b'\\AtBeginDocument{\\renewcommand{\\labelitemi}{--}}\\input{paper.tex}\n'
PROLOGUE_SHA='441f918995bae17b07d77dafaa46e1de4599ce73455573401fd6fe867f0db359'
STANDARD='VRS-GENERIC-EXACT-WEEKLY-WRAPPER-TYPOGRAPHY-RENDER-1'

def need(value,reason):
 if not value:raise ValueError('HOLD_RENDER_'+reason)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(path):
 p=Path(path);need(p.is_file()and not any(v.is_symlink()for v in(p,*p.parents)),'REGULAR_UNSYMLINKED_INPUT')
 before=p.stat();raw=p.read_bytes();after=p.stat()
 need((before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns),'INPUT_READ_RACE');return raw
def snapshot(folder):
 p=Path(folder);need(p.is_dir()and not any(v.is_symlink()for v in(p,*p.parents)),'CACHE_DIRECTORY')
 result={}
 for q in sorted(p.rglob('*')):
  need(not q.is_symlink(),'CACHE_SYMLINK')
  if q.is_file():result[str(q.relative_to(p))]=read(q)
 return result
def immutable(path,raw):
 p=Path(path);need(not any(v.is_symlink()for v in(p,*p.parents)),'OUTPUT_SYMLINK');p.parent.mkdir(parents=True,exist_ok=True)
 fd=os.open(p,os.O_EXCL|os.O_CREAT|os.O_WRONLY,0o600)
 with os.fdopen(fd,'wb')as f:f.write(raw);f.flush();os.fsync(f.fileno())
 need(read(p)==raw,'OUTPUT_BYTES_READBACK')
def require_resources():
 need(sha(PROLOGUE)==PROLOGUE_SHA,'EXACT_ASCII_MARKER_DRIVER')
 need(sha(read(d.__file__))==DIGEST_SOURCE_SHA,'UNCHANGED_WRAPPER_CONSUMER_SOURCE')
 raw=read(MANIFEST);need(sha(raw)==MANIFEST_SHA,'EXACT_CACHE_MANIFEST');m=json.loads(raw);cache=Path(m['cache_root']);sources=snapshot(cache)
 need(len(sources)==556 and {n:sha(b)for n,b in sources.items()}==m['files'],'CLOSED_556_CACHE_BYTES')
 binary=EXECUTABLE.resolve(strict=True);need(sha(read(binary))==BINARY_SHA,'EXACT_RENDERER_BINARY')
 return raw,cache,sources,binary

def render_for_package(root,week,note_specs,authority):
 """Return one-use callback after actual unchanged default scope consumption.

 Pass this callback directly to unchanged methods_digest.prepare. Arbitrary
 note snapshots or alternate admission consumers cannot be supplied here.
 """
 root=Path(root).resolve(strict=True);d.week_title(week);need(root==ROOT,'CANONICAL_RENDER_ROOT')
 adapter=Path(__file__).resolve();adapter_raw=read(adapter)
 resources=require_resources();consumed=d.consume_notes(root,note_specs,authority)
 expected=d.wrapper_tex(week,consumed['notes']);expected_sha=sha(expected)
 def fresh():
  need(read(adapter)==adapter_raw,'RENDER_ADAPTER_CHANGED')
  need(d.consume_notes(root,note_specs,authority)==consumed,'DEFAULT_NOTE_SCOPE_CHANGED')
  need(d.wrapper_tex(week,consumed['notes'])==expected,'WRAPPER_RECOMPUTE_MISMATCH')
 def render(path):
  fresh();need(require_resources()==resources,'RESOURCES_CHANGED_BEFORE_RENDER')
  p=Path(path);need(p.name=='paper.tex'and p.resolve(strict=True).is_relative_to(root/'RESEARCH_PIPELINE_v2/science_release_queue/digests'),'CANONICAL_EXACT_WRAPPER_PATH')
  source=read(p);need(source==expected and sha(source)==expected_sha,'EXACT_RECOMPUTED_CURRENT_WRAPPER')
  mr,cache,sources,binary=resources;build=p.parent/'render-observation';build.mkdir(mode=0o700,exist_ok=False)
  for name,raw in sources.items():immutable(build/'cache'/name,raw)
  immutable(build/'paper.tex',source);driver=build/'render_driver.tex';immutable(driver,PROLOGUE)
  command=[str(EXECUTABLE),'--only-cached','--keep-logs','--outdir',str(build),str(driver)]
  environment=os.environ.copy();environment['TECTONIC_CACHE_DIR']=str(build/'cache')
  started=dt.datetime.now(dt.timezone.utc).isoformat();proc=subprocess.run(command,cwd=p.parent,env=environment,capture_output=True,timeout=180);ended=dt.datetime.now(dt.timezone.utc).isoformat()
  immutable(build/'stdout.txt',proc.stdout);immutable(build/'stderr.txt',proc.stderr)
  fresh();need(require_resources()==resources,'RESOURCES_CHANGED_AFTER_RENDER')
  need(snapshot(build/'cache')==sources,'COPIED_CACHE_CHANGED');need(read(p)==source and read(build/'paper.tex')==source,'WRAPPER_SOURCE_CHANGED');need(read(driver)==PROLOGUE,'FIXED_DRIVER_CHANGED')
  pdf=read(build/'render_driver.pdf')if proc.returncode==0 and(build/'render_driver.pdf').is_file()else None
  observation={'standard':STANDARD,'status':'EXACT_RENDER_BYTES_OBSERVED_NOT_SCIENTIFIC_ADMISSION','release_week':week,'run_ids':[n['run_id']for n in consumed['notes']],'source_tex':{'path':str(p),'sha256':expected_sha},'render_adapter':{'path':str(adapter),'sha256':sha(adapter_raw)},'unchanged_methods_digest_sha256':DIGEST_SOURCE_SHA,'cache_manifest':{'path':str(MANIFEST),'sha256':MANIFEST_SHA},'cache_file_count':556,'binary':{'path':str(binary),'sha256':BINARY_SHA},'typographic_driver':{'path':str(driver),'sha256':PROLOGUE_SHA},'only_typesetting_change':'itemize marker changed from default bullet to ASCII --','command':command,'returncode':proc.returncode,'rendered_pdf_sha256':sha(pdf)if pdf else None,'started_at_utc':started,'ended_at_utc':ended,'network_resource_fetch_disabled':True,'certifies':False,'local_lean_execution':False,'zenodo_writes':0,'ssot_writes':0}
  immutable(build/'RENDERER_OBSERVATION.json',d.raw_json(observation))
  need(proc.returncode==0 and isinstance(pdf,bytes)and pdf.startswith(b'%PDF-'),'ACTUAL_PDF_RENDER_FAILED');return pdf
 return render
