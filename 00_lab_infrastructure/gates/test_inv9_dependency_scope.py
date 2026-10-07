import unittest,json,copy
from pathlib import Path
import inv9_dependency_scope as d

class DependencyScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        f=Path(__file__).parent/'fixtures/inv9_dependency_scope'
        cls.args={'candidate':(f/'candidate.lean').read_text(),'formal':(f/'formal.lean').read_text(),'paper':(f/'narrowed.tex').read_text(),'prior_tex':(f/'prior.tex').read_text(),'statement_scope':json.loads((f/'scope.json').read_text())['statement_scope']}
        cls.receipt=d.make_receipt(**cls.args)
    def evaluate(self,receipt=None,**changes):
        args={**copy.deepcopy(self.args),**changes}
        return d.evaluate(copy.deepcopy(self.receipt if receipt is None else receipt),certificate_sha256=d.CERTIFICATE_SHA,**args)
    def test_unchanged_nonproduct_lemma_passes(self):
        r=self.evaluate();self.assertEqual('PASS',r['status']);self.assertFalse(r['certifies']);self.assertFalse(r['local_lean_execution'])
        self.assertEqual(22,r['dependency_count'])
    def test_regions_cover_all_bytes(self):
        regions=self.receipt['whole_paper_regions'];self.assertEqual(0,regions[0]['byte_start'])
        for a,b in zip(regions,regions[1:]):self.assertEqual(a['byte_end_exclusive'],b['byte_start'])
        self.assertEqual(len(self.args['paper'].encode()),regions[-1]['byte_end_exclusive'])
    def test_omitted_required_definition_fails(self):
        x=copy.deepcopy(self.receipt);x['candidate_dependency_inventory']=[n for n in x['candidate_dependency_inventory']if n['name']!='capacityFloor']
        self.assertEqual('HOLD',self.evaluate(x)['status'])
    def test_omitted_product_dependency_cannot_be_laundered(self):
        source='def product_form (P D K : Real) := P * D / K\ntheorem retained (P D K : Real) : product_form P D K = product_form P D K := rfl\n'
        recorded=d.declaration_inventory(source,['retained'])
        with self.assertRaises(ValueError):d.validate_inventory(source,['retained'],[n for n in recorded if n['name']!='product_form'])
        with self.assertRaises(ValueError):d.validate_inventory(source,['retained'],recorded)
    def test_changed_dependency_span_and_context_fail(self):
        for field,value in [('byte_start',0),('source_sha256','0'*64),('ambient_source_context',[])]:
            x=copy.deepcopy(self.receipt);n=next(n for n in x['candidate_dependency_inventory']if n['ambient_source_context'])
            n[field]=value;self.assertEqual('HOLD',self.evaluate(x)['status'])
    def test_dropped_hypothesis_statement_or_ambient_fail(self):
        for mutate in ('signature','ambient','binder_map','conclusion_map'):
            scopes=copy.deepcopy(self.args['statement_scope'])
            if mutate=='signature':scopes[0]['exact_source_signature']=scopes[0]['exact_source_signature'].replace('(hsigma : 0 < sigma)','')
            elif mutate=='ambient':scopes[0]['ambient_source_context']=[{'line':1,'source_text':'variable (hidden : False)'}]
            elif mutate=='binder_map':scopes[0]['explicit_binders_and_hypotheses']=''
            else:scopes[0]['conclusion']='True'
            self.assertEqual('HOLD',self.evaluate(statement_scope=scopes)['status'])
    def test_different_source_family_fails(self):
        for key in ('candidate','formal','prior_tex'):
            self.assertEqual('HOLD',self.evaluate(**{key:self.args[key]+'\n'})['status'])
    def test_wrong_certificate_fails(self):
        self.assertEqual('HOLD',d.evaluate(self.receipt,certificate_sha256='0'*64,**self.args)['status'])
    def test_product_target_added_to_scope_fails(self):
        s=copy.deepcopy(self.args['statement_scope']);s.append({**s[0],'lean_theorem':'cantelli_capacity_certificate'})
        self.assertEqual('HOLD',self.evaluate(statement_scope=s)['status'])
    def test_excluded_certified_headline_leakage_fails(self):
        paper=self.args['paper'].replace(r'\section*{Conjectural context}',r'\section*{Certified-scope statement S127-01}\section*{Conjectural context}',1)
        self.assertEqual('HOLD',self.evaluate(paper=paper)['status'])
    def test_excluded_name_in_main_fails(self):
        paper=self.args['paper'].replace(r'\section*{Conjectural context}','cantelli_capacity_certificate is a certified result.\n'+r'\section*{Conjectural context}',1)
        self.assertEqual('HOLD',self.evaluate(paper=paper)['status'])
    def test_formula_leak_in_main_fails(self):
        paper=self.args['paper'].replace(r'\section*{Conjectural context}',r'$P * D / K$\section*{Conjectural context}',1)
        args={**self.args,'paper':paper};receipt=d.make_receipt(**args)
        self.assertEqual('HOLD',d.evaluate(receipt,certificate_sha256=d.CERTIFICATE_SHA,**args)['status'])
    def test_archival_content_changed_fails(self):
        paper=self.args['paper'].replace('14 PASS / 0 FAIL / 14 CHECKS','15 PASS / 0 FAIL / 15 CHECKS')
        self.assertNotEqual(paper,self.args['paper']);self.assertEqual('HOLD',self.evaluate(paper=paper)['status'])
    def test_missing_foundation_and_conditional_reference_fail(self):
        for value in ('10.5281/zenodo.23141592','conditional on premises PL and PD'):
            self.assertEqual('HOLD',self.evaluate(paper=self.args['paper'].replace(value,'missing'))['status'])
    def test_wrong_or_unlisted_receipt_field_fail(self):
        for mutate in ('extra','regions'):
            r=copy.deepcopy(self.receipt)
            if mutate=='extra':r['ignore_me']=True
            else:r['whole_paper_regions'].pop()
            self.assertEqual('HOLD',self.evaluate(r)['status'])
    def test_unresolved_source_command_fail(self):
        with self.assertRaises(ValueError):d.declaration_inventory('macro "unsafeAlias" : term => `(0)\ntheorem test : True := True.intro',['test'])

if __name__=='__main__':unittest.main()
