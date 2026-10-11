"""PDF layout regression fixtures only; never certification or admission."""
from pathlib import Path
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
GATES = Path(__file__).resolve().parent
sys.path.insert(0, str(GATES))
import nightly_minimal_policy as policy

WRAP_LINE = r'\AtBeginDocument{\DeclareRobustCommand{\_}{\textunderscore\allowbreak}}'
NAMES = {
    'Run-189': 'Viridis.Computation.ReplicatedChecker.adding_checker_weakly_reduces_independent_miss',
    'Run-190': 'Viridis.IntelligenceBound.PositiveCostCapacity.capacity_from_positive_cost_floor',
}

def fixture_scope(qualified):
    return [{
        'lean_theorem': qualified.rsplit('.', 1)[1],
        'english_claim': 'Under every hypothesis in the frozen statement, ' + qualified +
                         ' establishes exactly its quoted conclusion. No empirical identification or additional physical law is asserted.',
        'evidence_class': 'FORMALLY_VERIFIED',
    }]

class NoteTypographyTests(unittest.TestCase):
    def test_fixed_template_still_rejects_changed_scientific_sentence(self):
        scope = fixture_scope(NAMES['Run-189'])
        paper = policy.expected_paper('Run-189', 'INDEPENDENT', scope)
        policy.validate_exact_body('Run-189', 'INDEPENDENT', scope, paper)
        with self.assertRaises(ValueError):
            policy.validate_exact_body('Run-189', 'INDEPENDENT', scope,
                paper.replace(b'No empirical identification', b'Empirical validation established', 1))

    def test_long_identifiers_render_fully_without_overfull_lines(self):
        executable = shutil.which('tectonic')
        text_tool = shutil.which('pdftotext')
        cache = Path(os.environ.get('VIRIDIS_TEST_TECTONIC_CACHE', '/nonexistent'))
        if not executable or not text_tool or not cache.is_dir():
            self.skipTest('requires cached Tectonic and pdftotext; no resources are downloaded')
        with tempfile.TemporaryDirectory(prefix='nightly-note-typography-') as temporary:
            root = Path(temporary)
            for run, qualified in NAMES.items():
                with self.subTest(run=run):
                    scope = fixture_scope(qualified)
                    fixed = policy.expected_paper(run, 'INDEPENDENT', scope)
                    # Reproduce the actual previous rendering defect using the
                    # same scientific bytes, only removing the typography hook.
                    prior = fixed.replace((WRAP_LINE + '\n\n').encode(), b'', 1)
                    results = {}
                    for label, tex in [('prior', prior), ('fixed', fixed)]:
                        folder = root / (run + '-' + label)
                        (folder / 'rendered').mkdir(parents=True)
                        (folder / 'paper.tex').write_bytes(tex)
                        for filename in ['statement-001.txt', 'FROZEN_CONTEXT.txt', 'HISTORICAL_SOURCE.txt']:
                            (folder / 'rendered' / filename).write_text('Unit layout fixture; no proof or publication evidence.\n')
                        local_cache = folder / 'cache'
                        shutil.copytree(cache, local_cache)
                        environment = os.environ.copy()
                        environment['TECTONIC_CACHE_DIR'] = str(local_cache)
                        render = subprocess.run([executable, '--only-cached', '--keep-logs', 'paper.tex'],
                            cwd=folder, env=environment, capture_output=True, timeout=180)
                        self.assertEqual(render.returncode, 0, render.stderr.decode(errors='replace'))
                        log = (folder / 'paper.log').read_text(errors='replace')
                        text = subprocess.run([text_tool, str(folder / 'paper.pdf'), '-'],
                            capture_output=True, text=True, check=True).stdout
                        results[label] = (log, text)
                    self.assertIn('Overfull \\hbox', results['prior'][0])
                    self.assertNotIn('Overfull \\hbox', results['fixed'][0])
                    self.assertIn(qualified, re.sub(r'\s+', '', results['fixed'][1]))
                    self.assertIn(policy.DISCLAIMER, re.sub(r'\s+', ' ', results['fixed'][1]))

if __name__ == '__main__':
    unittest.main()
