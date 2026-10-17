"""Owned subprocess/cache controls over synthetic DATA, no native TeX or Core."""
from pathlib import Path
import json
import os
import signal
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch,MagicMock

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parent)]
from w42_portable_fixture import PortableFixture
import nightly_manuscript_access as access
import methods_digest_v2 as digest


class LabelledNativeRenderTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='labelled-native-controls-');self.addCleanup(self.temp.cleanup)
        self.f=PortableFixture(self.temp.name)
        self.context=self.f.context();self.context.__enter__();self.addCleanup(self.context.__exit__,None,None,None)
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
        original=access.subprocess.Popen
        def drift(*a,**kw):
            process=original(*a,**kw)
            (Path(self.cache['cache_root'])/'asset-000.dat').write_bytes(b'changed during child')
            return process
        with patch.object(access.subprocess,'Popen',side_effect=drift):
            with self.assertRaisesRegex(ValueError,'native renderer failed or input closure changed'):self.render()
        o=json.loads((self.tex.parent/'render-observation/RENDERER_OBSERVATION.json').read_bytes())
        self.assertFalse(o['cache_and_binary_exact_after'])
    def test_source_drift_after_spawn_cannot_clear_provenance(self):
        original=access.subprocess.Popen
        def drift(*a,**kw):
            process=original(*a,**kw);self.tex.write_bytes(b'changed during child');return process
        with patch.object(access.subprocess,'Popen',side_effect=drift):
            with self.assertRaisesRegex(ValueError,'native renderer failed or input closure changed'):self.render()
    def test_missing_glyph_in_each_retained_channel_is_rejected_even_when_child_succeeds(self):
        original=access.subprocess.Popen
        for channel in ['stdout','stderr','paper.log']:
            with self.subTest(channel=channel):
                directory=self.f.root/('warning-'+channel);directory.mkdir();tex=directory/'paper.tex';tex.write_bytes(self.tex.read_bytes())
                def warning(*a,**kw):
                    process=original(*a,**kw)
                    if channel=='paper.log':(directory/'render-observation/paper.log').write_bytes(b'Missing character: synthetic missing glyph\n')
                    else:kw[channel].write(b'Missing character: synthetic missing glyph\n');kw[channel].flush()
                    return process
                with patch.object(access.subprocess,'Popen',side_effect=warning):
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
        class Process:
            pid=987654321;returncode=None
            def __init__(self):self.waits=[]
            def wait(self,timeout):
                self.waits.append(timeout)
                if len(self.waits)==1:raise subprocess.TimeoutExpired('synthetic',timeout)
                self.returncode=0;return 0
            def poll(self):return self.returncode
        process=Process();signals=[];made=[];original=access.tempfile.mkdtemp
        def kill(pid,sig):
            self.assertEqual(pid,process.pid);signals.append(sig)
            if sig==0:raise ProcessLookupError()
        def record(**kw):
            p=original(**kw);made.append(Path(p));return p
        with patch.object(access.subprocess,'Popen',return_value=process),patch.object(access.os,'killpg',side_effect=kill),patch.object(access.tempfile,'mkdtemp',side_effect=record):
            with self.assertRaisesRegex(ValueError,'HOLD_NATIVE_RENDER_180S_WITH_CLEANUP'):self.render()
        self.assertEqual(process.waits,[180,10,5]);self.assertIn(signal.SIGTERM,signals);self.assertIn(signal.SIGKILL,signals)
        self.assertFalse(made[0].exists())
        self.assertFalse((self.tex.parent/'render-observation/RENDERER_OBSERVATION.json').exists())
    def test_group_cleanup_kills_owned_descendant_after_parent_exit(self):
        code="import subprocess,sys; subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)"
        process=subprocess.Popen([sys.executable,'-c',code],start_new_session=True,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        self.addCleanup(lambda:access.close_render_group(process))
        process.wait(timeout=5)
        os.killpg(process.pid,0)
        access.close_render_group(process)
        with self.assertRaises(ProcessLookupError):os.killpg(process.pid,0)
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
