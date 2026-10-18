"""Owned subprocess/cache controls over synthetic DATA, no native TeX or Core."""
from pathlib import Path
import json
import os
import signal
import select
import shutil
import subprocess
import sys
import tempfile
import types
import time
import unittest
from unittest.mock import patch,MagicMock

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parent)]
from w42_portable_fixture import PortableFixture, _portable_renderer_prerequisites
import nightly_manuscript_access as access
import methods_digest_v2 as digest


class _FixtureOwnership:
    """Actual child objects registered BEFORE constructor; no automatic deletion.

    Unknown constructor or closure retains every input/cache and raises HOLD.
    Registry keeps child objects alive so GC cannot silently release reservation.
    """
    def __init__(self):
        self.entries={};self.caches=[];self.root=None;self.root_inode=None
    def set_temporary(self, temporary):
        temporary._finalizer.detach()  # Own guarded cleanup replaces finalizer.
        self.root=Path(temporary.name)
        s=self.root.lstat();self.root_inode=(s.st_dev,s.st_ino)
    def arm(self, process):
        self.entries[id(process)]={'process':process,'constructed':False,'isolated':False,
            'quiet':False,'reason':None,'final_signal_attempted':False,'reap_started':False,
            'reaped':False,'reap_deadline':None,'absence_deadline':None}
    def bind(self, process):
        entry=self.entries[id(process)];entry['constructed']=True
        state=access.native_render_reservation(process)  # Own child only; NOT isolation.
        if access.native_render_observe(state) is None:
            # Independent fixture fallback records actual live isolation before
            # the exact production shim receives GO. Exit alone never binds it.
            sid=os.getsid(process.pid);pgid=os.getpgid(process.pid)
            if sid==pgid==process.pid and access.native_render_observe(state) is None:
                entry['isolated']=True
    def close_one(self, process):
        entry=self.entries[id(process)]
        if entry['quiet']:return
        pid=getattr(process,'pid',None)
        if type(pid)is not int or pid<=1:
            raise RuntimeError('TEST_ONLY_CONSTRUCTOR_OWNERSHIP_UNKNOWN_RETAIN')
        if getattr(process,'returncode',None)is not None:
            # Candidate already reaped its real child: zero probes ONLY.
            entry['reap_started']=True;entry['reaped']=True
        if not entry['reaped']:
            def observe():
                try:value=os.waitid(os.P_PID,pid,os.WEXITED|os.WNOHANG|os.WNOWAIT)
                except (ChildProcessError,OSError)as exc:
                    raise RuntimeError('TEST_ONLY_OWN_RESERVATION_LOST_NO_SIGNAL_RETAIN')from exc
                if value is not None and value.si_pid!=pid:
                    raise RuntimeError('TEST_ONLY_WRONG_NATIVE_CHILD_NO_SIGNAL_RETAIN')
                return value
            if not entry['reap_started']:
                if not entry['final_signal_attempted']:
                    seen=observe()  # Fresh exact own unreaped child BEFORE signal.
                    entry['final_signal_attempted']=True  # Interruption closes signal phase.
                    try:(os.killpg if entry['isolated']else os.kill)(pid,signal.SIGKILL)
                    except ProcessLookupError:pass
                    except PermissionError:
                        if observe() is None:raise RuntimeError('TEST_ONLY_LIVE_PERMISSION_UNKNOWN_RETAIN')
                entry['reap_started']=True
            if entry['reap_deadline']is None:entry['reap_deadline']=time.monotonic()+5
            while observe()is None:
                if time.monotonic()>=entry['reap_deadline']:raise RuntimeError('TEST_ONLY_EXIT_UNPROVED_RETAIN')
                time.sleep(.01)
            actual,status=os.waitpid(pid,0)
            if actual!=pid:raise RuntimeError('TEST_ONLY_WRONG_REAP_RETAIN')
            # An interrupt after kernel reap cannot reopen the signal phase.
            entry['reaped']=True;process.returncode=os.waitstatus_to_exitcode(status)
        if not entry['constructed']or not entry['isolated']:
            raise RuntimeError('TEST_ONLY_UNBOUND_GROUP_UNKNOWN_RETAIN')
        if entry['absence_deadline']is None:entry['absence_deadline']=time.monotonic()+5
        while True:
            try:os.killpg(pid,0)
            except ProcessLookupError:entry['quiet']=True;return
            except PermissionError:pass
            if time.monotonic()>=entry['absence_deadline']:raise RuntimeError('TEST_ONLY_ABSENCE_UNPROVED_RETAIN')
            time.sleep(.01)
    def failed_constructor_or_callback(self, process):
        try:self.close_one(process)
        except BaseException as exc:self.entries[id(process)]['reason']=type(exc).__name__+':'+str(exc)
    def close_all(self):
        failures=[]
        for entry in self.entries.values():
            try:self.close_one(entry['process'])
            except BaseException as exc:failures.append(type(exc).__name__+':'+str(exc))
        if failures:raise RuntimeError('TEST_ONLY_OWNERSHIP_HOLD_RETAIN_SCRATCH:'+repr(failures))
    def cleanup_directory(self):
        self.close_all()  # Failure leaves detached-finalizer root AND caches intact.
        for cache,expected_inode in self.caches:
            if cache.exists():
                value=cache.lstat()
                if (value.st_dev,value.st_ino)!=expected_inode:
                    raise RuntimeError('TEST_ONLY_CACHE_NAMESPACE_CHANGED_RETAIN')
                shutil.rmtree(cache)
        if self.root is not None and self.root.exists():
            value=self.root.lstat()
            if (value.st_dev,value.st_ino)!=self.root_inode:
                raise RuntimeError('TEST_ONLY_SCRATCH_REPLACED_RETAIN')
            shutil.rmtree(self.root)
    def constructor(self, original):
        ownership=self
        class OwnedPopen(original):
            def __init__(self,*args,**kwargs):
                _portable_renderer_prerequisites()  # BEFORE any real constructor.
                ownership.arm(self)
                try:
                    super().__init__(*args,**kwargs)
                    ownership.bind(self)
                except BaseException:
                    ownership.failed_constructor_or_callback(self)
                    raise
        return OwnedPopen


class _ModuleProxy:
    def __init__(self,module,**values):self.module=module;self.__dict__.update(values)
    def __getattr__(self,name):return getattr(self.module,name)


def _actual_popen_after(ownership,callback):
    """Registered actual constructor; callback failure closes BEFORE return."""
    original=access.subprocess.Popen
    class InstrumentedPopen(original):
        def __init__(self,*args,**kwargs):
            try:
                super().__init__(*args,**kwargs)
                callback(self,*args,**kwargs)
            except BaseException:
                if id(self)in ownership.entries:ownership.failed_constructor_or_callback(self)
                raise
    return InstrumentedPopen


class LabelledNativeRenderTests(unittest.TestCase):
    def setUp(self):
        self.ownership=_FixtureOwnership()
        self.temp=tempfile.TemporaryDirectory(prefix='labelled-native-controls-')
        self.ownership.set_temporary(self.temp)
        self.addCleanup(self.ownership.cleanup_directory)
        self.f=PortableFixture(self.temp.name,renderer_mode=('timeout180'if self._testMethodName=='test_timeout_uses_term_then_group_kill_even_when_parent_exits'else'normal'))
        self.context=self.f.context();self.context.__enter__();self.addCleanup(self.context.__exit__,None,None,None)
        self.process_proxy=_ModuleProxy(subprocess,Popen=self.ownership.constructor(subprocess.Popen))
        process_patch=patch.object(access,'subprocess',self.process_proxy);process_patch.start();self.addCleanup(process_patch.stop)
        original_mkdtemp=tempfile.mkdtemp
        def owned_cache(**kw):
            value=original_mkdtemp(**kw);path=Path(value);seen=path.lstat()
            self.ownership.caches.append((path,(seen.st_dev,seen.st_ino)));return value
        cache_patch=patch.object(access,'tempfile',_ModuleProxy(tempfile,mkdtemp=owned_cache))
        cache_patch.start();self.addCleanup(cache_patch.stop)
        self.tex=self.f.root/'owned-render/paper.tex';self.tex.parent.mkdir()
        self.tex.write_bytes(b'\\documentclass{article}\n\\begin{document}synthetic\\end{document}\n')
        self.cache=json.loads(Path(self.f.cache['path']).read_bytes())
    def render(self):return access.native_render(self.tex,root=self.f.root)
    def test_fixed_callback_emits_closed_observation_and_deletes_only_owned_cache(self):
        original=access.tempfile.mkdtemp;made=[]
        def record(**kw):
            p=original(**kw);made.append(Path(p));return p
        with patch.object(access.tempfile,'mkdtemp',side_effect=record):pdf=self.render()
        observation=json.loads((self.tex.parent/'render-observation/RENDERER_OBSERVATION.json').read_bytes())
        self.assertTrue(pdf.startswith(b'%PDF-'));self.assertEqual(observation['returncode'],0)
        self.assertTrue(observation['cache_and_binary_exact_after'])
        self.assertEqual(observation['command'][:4],['/opt/homebrew/bin/tectonic','--only-cached','--keep-logs','--outdir'])
        self.assertEqual(len(made),1);self.assertFalse(made[0].exists())
        self.assertEqual(access.cache_snapshot(Path(self.cache['cache_root'])),self.cache['files'])
    def test_changed_binary_is_rejected_before_any_spawn(self):
        self.f.binary.write_bytes(b'not the pinned executable')
        with patch.object(access.subprocess,'Popen',side_effect=access.AccessHold('UNSAFE_SPAWN_REACHED'))as spawn:
            with self.assertRaisesRegex(ValueError,'pinned renderer and cache before execution'):self.render()
        spawn.assert_not_called();self.assertFalse((self.tex.parent/'render-observation').exists())
    def test_changed_cache_asset_is_rejected_before_any_spawn(self):
        (Path(self.cache['cache_root'])/'asset-000.dat').write_bytes(b'changed')
        with patch.object(access.subprocess,'Popen',side_effect=access.AccessHold('UNSAFE_SPAWN_REACHED'))as spawn:
            with self.assertRaisesRegex(ValueError,'all pinned renderer assets before execution'):self.render()
        spawn.assert_not_called()
    def test_changed_cache_manifest_is_rejected_before_any_spawn(self):
        Path(self.f.cache['path']).write_bytes(b'{}')
        with patch.object(access.subprocess,'Popen')as spawn:
            with self.assertRaisesRegex(ValueError,'bound input changed'):self.render()
        spawn.assert_not_called()
    def test_cache_drift_after_spawn_cannot_clear_provenance(self):
        def drift(process,*a,**kw):
            (Path(self.cache['cache_root'])/'asset-000.dat').write_bytes(b'changed during child')
            return process
        with patch.object(access.subprocess,'Popen',_actual_popen_after(self.ownership,drift)):
            with self.assertRaisesRegex(ValueError,'native renderer failed or input closure changed'):self.render()
        o=json.loads((self.tex.parent/'render-observation/RENDERER_OBSERVATION.json').read_bytes())
        self.assertFalse(o['cache_and_binary_exact_after'])
    def test_source_drift_after_spawn_cannot_clear_provenance(self):
        def drift(process,*a,**kw):
            self.tex.write_bytes(b'changed during child');return process
        with patch.object(access.subprocess,'Popen',_actual_popen_after(self.ownership,drift)):
            with self.assertRaisesRegex(ValueError,'native renderer failed or input closure changed'):self.render()
    def test_missing_glyph_in_each_retained_channel_is_rejected_even_when_child_succeeds(self):
        for channel in ['stdout','stderr','paper.log']:
            with self.subTest(channel=channel):
                directory=self.f.root/('warning-'+channel);directory.mkdir();tex=directory/'paper.tex';tex.write_bytes(self.tex.read_bytes())
                def warning(process,*a,**kw):
                    if channel=='paper.log':(directory/'render-observation/paper.log').write_bytes(b'Missing character: synthetic missing glyph\n')
                    else:kw[channel].write(b'Missing character: synthetic missing glyph\n');kw[channel].flush()
                    return process
                with patch.object(access.subprocess,'Popen',_actual_popen_after(self.ownership,warning)):
                    with self.assertRaisesRegex(ValueError,'native renderer missing glyph'):
                        access.native_render(tex,root=self.f.root)
                observed=json.loads((directory/'render-observation/RENDERER_OBSERVATION.json').read_bytes())
                self.assertEqual(observed['returncode'],0);self.assertTrue(observed['cache_and_binary_exact_after'])
    def test_log_growth_or_replacement_cannot_be_accepted_as_fresh_identity(self):
        self.render();seen={};access.require_render_logs(self.tex.parent,seen)
        self.assertEqual(set(Path(p).name for p in seen),{'stdout.txt','stderr.txt'})
        log=self.tex.parent/'render-observation/stderr.txt';log.write_bytes(b'x'*4194305)
        with self.assertRaisesRegex(ValueError,'bounded stable renderer log'):access.require_render_logs(self.tex.parent,{})
    def test_fifo_log_is_rejected_before_open_without_blocking(self):
        directory=self.tex.parent/'render-observation';directory.mkdir()
        os.mkfifo(directory/'stdout.txt')
        with patch.object(access.os,'open')as opened:
            with self.assertRaisesRegex(ValueError,'regular renderer log'):access.require_render_logs(self.tex.parent,{})
        opened.assert_not_called()
    def test_symlinked_log_is_rejected_without_following_it(self):
        self.render();log=self.tex.parent/'render-observation/stderr.txt';log.unlink();log.symlink_to(self.tex)
        with self.assertRaisesRegex(ValueError,'regular renderer log ancestry'):access.require_render_logs(self.tex.parent,{})
    def test_same_bytes_path_replacement_after_fd_read_is_rejected(self):
        self.render();log=self.tex.parent/'render-observation/stderr.txt';log.write_bytes(b'allowed log bytes')
        inode=log.stat().st_ino;original=access.os.fstat;count=[]
        def replace(fd):
            value=original(fd)
            if value.st_ino==inode:
                count.append(1)
                if len(count)==2:
                    alternate=log.with_name('replacement.txt');alternate.write_bytes(log.read_bytes());alternate.replace(log)
            return value
        with patch.object(access.os,'fstat',side_effect=replace):
            with self.assertRaisesRegex(ValueError,'bounded stable renderer log'):access.require_render_logs(self.tex.parent,{})
        self.assertEqual(log.read_bytes(),b'allowed log bytes');self.assertEqual(len(count),2)
    def test_timeout_uses_term_then_group_kill_even_when_parent_exits(self):
        # Real180 caller budget and exact production READY/GO shim. The closed
        # synthetic renderer sleeps220 (no forks), so this is no TeX/native claim.
        processes=[];made=[];signals=[];real_kill=os.killpg
        class NativeOS:
            def __getattr__(inner,name):return getattr(os,name)
            def killpg(inner,pid,sig):
                if sig:
                    self.assertIsNone(processes[0].returncode)
                    seen=os.waitid(os.P_PID,pid,os.WEXITED|os.WNOHANG|os.WNOWAIT)
                    self.assertTrue(seen is None or seen.si_pid==pid)
                signals.append(sig);return real_kill(pid,sig)
        original_mkdtemp=access.tempfile.mkdtemp
        def record(**kw):
            value=original_mkdtemp(**kw);made.append(Path(value));return value
        def remember(process,*a,**kw):processes.append(process)
        started=time.monotonic()
        try:
            with patch.object(access.subprocess,'Popen',_actual_popen_after(self.ownership,remember)),patch.object(access,'os',NativeOS()),patch.object(access.tempfile,'mkdtemp',side_effect=record):
                with self.assertRaisesRegex(ValueError,'HOLD_NATIVE_RENDER_180S_WITH_CLEANUP'):self.render()
            elapsed=time.monotonic()-started
            self.assertGreaterEqual(elapsed,180);self.assertLess(elapsed,205)
            self.assertIn(signal.SIGTERM,signals);self.assertIn(signal.SIGKILL,signals)
            self.assertEqual(len(processes),1);self.assertIsNotNone(processes[0].returncode)
            with self.assertRaises(ProcessLookupError):os.killpg(processes[0].pid,0)
            self.assertFalse(made[0].exists())
            self.assertFalse((self.tex.parent/'render-observation/RENDERER_OBSERVATION.json').exists())
        finally:
            self.ownership.close_all()

    def test_group_cleanup_kills_owned_descendant_after_parent_exit(self):
        _portable_renderer_prerequisites()  # BEFORE pipes/constructor/native bind.
        process=None;fds=[];signals=[];state=None;admission=None;constructor_patch=None
        real_kill=os.killpg;real_reap=os.waitpid
        child_code=("import json,os,signal,time;"
            "signal.signal(signal.SIGTERM,signal.SIG_IGN);"
            "w=int(__import__('sys').argv[1]);r=int(__import__('sys').argv[2]);"
            "os.write(w,(json.dumps({'kind':'READY','pid':os.getpid(),'group':os.getpgrp(),'session':os.getsid(0),'ignores_term':signal.getsignal(signal.SIGTERM)==signal.SIG_IGN})+'\\n').encode());"
            "assert os.read(r,1)==b'Q';"
            "os.write(w,(json.dumps({'kind':'ACK','pid':os.getpid(),'ignores_term':signal.getsignal(signal.SIGTERM)==signal.SIG_IGN})+'\\n').encode());time.sleep(30)")
        try:
            ready_r,ready_w=os.pipe();fds.extend([ready_r,ready_w])
            command_r,command_w=os.pipe();fds.extend([command_r,command_w])
            leader=("#!"+sys.executable+"\nimport json,os,subprocess,sys\n"
                +"w="+repr(ready_w)+";r="+repr(command_r)+"\n"
                +"p=subprocess.Popen([sys.executable,'-I','-S','-B','-c',"+repr(child_code)+",str(w),str(r)],pass_fds=(w,r),stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)\n"
                +"os.write(w,(json.dumps({'kind':'LEADER','pid':os.getpid(),'descendant':p.pid})+'\\n').encode())\n")
            binary=self.f.root/'descendant-platform/leader';binary.parent.mkdir()
            binary.write_text(leader);binary.chmod(0o700)
            original=self.process_proxy.Popen
            class DescendantPopen(original):
                def __init__(inner,*args,**kwargs):
                    # Retain exact production shim/argv. Add ONLY these fixed
                    # fixture pipes, inherited by its closed synthetic payload.
                    kwargs=dict(kwargs)
                    self.assertEqual(len(kwargs['pass_fds']),2)
                    kwargs['pass_fds']=tuple(kwargs['pass_fds'])+(ready_w,command_r)
                    super().__init__(*args,**kwargs)
            command=['/opt/homebrew/bin/tectonic','--only-cached','--keep-logs','--outdir',str(self.tex.parent/'render-observation'),'paper.tex']
            admission=access.NativeRenderAdmission(binary,command,self.tex.parent,{},subprocess.DEVNULL,subprocess.DEVNULL,time.monotonic()+5)
            constructor_patch=patch.object(access.subprocess,'Popen',DescendantPopen)
            constructor_patch.start()  # Actual exact class remains bound through native cleanup.
            admission.start();admission.bind_ready();admission.go()
            process=admission.process;state=admission.reservation
            self.assertTrue(state['isolated']);self.assertTrue(state['bound_before_go'])
            os.close(ready_w);fds.remove(ready_w);os.close(command_r);fds.remove(command_r)
            buffer=b'';messages={}
            def receive(kind):
                nonlocal buffer
                end=time.monotonic()+5
                while kind not in messages:
                    self.assertLess(time.monotonic(),end,'actual descendant handshake deadline')
                    if not select.select([ready_r],[],[],.05)[0]:continue
                    data=os.read(ready_r,4096);self.assertTrue(data,'actual descendant READY/ACK EOF')
                    buffer+=data;self.assertLessEqual(len(buffer),8192)
                    while b'\n'in buffer:
                        line,buffer=buffer.split(b'\n',1);value=json.loads(line)
                        self.assertIn(value['kind'],('READY','LEADER','ACK'));self.assertNotIn(value['kind'],messages)
                        messages[value['kind']]=value
                return messages[kind]
            ready=receive('READY');parent=receive('LEADER')
            self.assertEqual(parent['pid'],process.pid);self.assertEqual(parent['descendant'],ready['pid'])
            self.assertIs(type(ready['pid']),int);self.assertNotEqual(ready['pid'],process.pid)
            self.assertEqual(ready['group'],process.pid);self.assertEqual(ready['session'],process.pid)
            self.assertIs(ready['ignores_term'],True)
            end=time.monotonic()+5;observed=access.native_render_observe(state)
            while observed is None:
                self.assertLess(time.monotonic(),end);time.sleep(.01);observed=access.native_render_observe(state)
            self.assertEqual(observed.si_status,0,'leader must actually finish successfully')
            self.assertEqual(observed.si_code,os.CLD_EXITED)
            os.write(command_w,b'Q');ack=receive('ACK')
            self.assertEqual(ack['pid'],ready['pid']);self.assertIs(ack['ignores_term'],True)
            # The fresh post-leader-exit challenge proves a LIVE descendant;
            # reported PID is only an oracle, never authority for nonzero signal.
            self.assertEqual(os.getpgid(ready['pid']),process.pid)
            self.assertEqual(os.getsid(ready['pid']),process.pid)
            class NativeOS:
                def __getattr__(inner,name):return getattr(os,name)
                def killpg(inner,pid,sig):
                    if sig:
                        self.assertIsNone(process.returncode)
                        seen=os.waitid(os.P_PID,pid,os.WEXITED|os.WNOHANG|os.WNOWAIT)
                        self.assertTrue(seen is None or seen.si_pid==pid)
                    signals.append(sig);return real_kill(pid,sig)
                def waitpid(inner,pid,options):
                    self.assertIn(signal.SIGKILL,signals,'own descendant must receive final group KILL before own reap')
                    return real_reap(pid,options)
            with patch.object(access,'os',NativeOS()):access.close_render_group(state)
            self.assertTrue(state['reaped']);self.assertTrue(state['group_absent'])
            with self.assertRaises(ProcessLookupError):os.killpg(process.pid,0)
            self.assertEqual(os.read(ready_r,1),b'','actual descendant writer must close')
        finally:
            try:
                if admission is not None:admission.close_control()
                self.ownership.close_all()
            finally:
                try:
                    for fd in fds:os.close(fd)
                finally:
                    if constructor_patch is not None:constructor_patch.stop()
    def test_input_symlink_never_reaches_spawn(self):
        alternate=self.tex.with_name('alternate.tex');self.tex.rename(alternate);self.tex.symlink_to(alternate)
        with patch.object(access.subprocess,'Popen')as spawn:
            with self.assertRaisesRegex(ValueError,'regular native render input ancestry'):self.render()
        spawn.assert_not_called()
    def test_ambient_access_module_cannot_supply_wrapper_provenance(self):
        (self.tex.parent/'paper.pdf').write_bytes(b'%PDF-synthetic')
        counterfeit=types.ModuleType('nightly_manuscript_access');counterfeit.frozen_sources=MagicMock();counterfeit.require_render_logs=MagicMock()
        with patch.dict(sys.modules,{'nightly_manuscript_access':counterfeit}),patch.object(digest,'_current_access',side_effect=digest.DigestHold('fixed source loader refused counterfeit')):
            with self.assertRaisesRegex(ValueError,'fixed source loader refused counterfeit'):
                digest.require_wrapper_render(self.tex.parent,self.f.root)
        counterfeit.frozen_sources.assert_not_called()
        counterfeit.require_render_logs.assert_not_called()


class LabelledPublicationFormatTests(unittest.TestCase):
    def test_only_labelled_wrapper_uses_native_unicode_font_environment(self):
        archival=digest.wrapper_tex('2026-W42',[])
        note={'access_standard':digest.LABELLED_ACCESS_STANDARD,'artifact_label':digest.ARTIFACT_LABEL,
            'run_id':'Run-191','foundation_basis':'INDEPENDENT','section':'MAIN_NOTES','claim_table':[]}
        labelled=digest.wrapper_tex('2026-W42',[note])
        self.assertIn(br'\usepackage[T1]{fontenc}',archival)
        self.assertNotIn(br'\usepackage[T1]{fontenc}',labelled)
        self.assertEqual(labelled.count(digest.ARTIFACT_LABEL.encode()),1)
        self.assertNotIn(digest.ARTIFACT_LABEL.encode(),archival)
    def test_labelled_top_copy_selection_keeps_both_exact_admitted_names(self):
        note={'run_id':'Run-191','manuscripts':[{'filename':'paper.pdf'},
            {'filename':'Run-191-Historical-Paper-UNCERTIFIED.pdf'}]}
        self.assertEqual(digest.manuscript_copies(note),[('Run-191-Paper.pdf','paper.pdf'),
            ('Run-191-Historical-Paper-UNCERTIFIED.pdf','Run-191-Historical-Paper-UNCERTIFIED.pdf')])
    def test_new_publication_rejects_archival_or_unlabelled_digest(self):
        for standard in [digest.STANDARD,None,'invented']:
            with self.subTest(standard=standard),self.assertRaisesRegex(ValueError,'labelled artifact envelope'):
                digest.require_new_publication({'standard':standard})
    def test_approved_wording_does_not_silently_extend_to_w43_or_mixed_notes(self):
        note={'access_standard':digest.LABELLED_ACCESS_STANDARD,'artifact_label':digest.ARTIFACT_LABEL}
        digest.require_new_publication({'standard':digest.LABELLED_STANDARD,'release_week':'2026-W42','notes':[note]})
        with self.assertRaisesRegex(ValueError,'scoped to 2026-W42'):
            digest.require_new_publication({'standard':digest.LABELLED_STANDARD,'release_week':'2026-W43','notes':[note]})
        with self.assertRaisesRegex(ValueError,'every current manuscript'):
            digest.require_new_publication({'standard':digest.LABELLED_STANDARD,'release_week':'2026-W42','notes':[note,{}]})


if __name__=='__main__':unittest.main()
