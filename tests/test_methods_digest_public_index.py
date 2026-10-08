"""Read-only projection tests; fixture consumers confer no real certification."""
from __future__ import annotations
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from canon_core.methods_digests import (DISCLAIMER, GROUP_FIELDS, NOTE_FIELDS, LABEL_FIELDS,
    load_methods_digest_joins, validate_methods_digests)
from canon_core.catalog import build_catalog, validate_catalog, validate_catalog_sources
from scripts import methods_digest_index as projection

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('digest_public_index', ROOT/'scripts/generate_public_index.py')
index = importlib.util.module_from_spec(spec); spec.loader.exec_module(index)


def pointer():
    labels = [{'lean_theorem':'conditional_bound','semantic_tier':'SUBSTANTIVE',
               'nonvacuity_label':'CERTIFIED_WITNESS: example','headline_eligible':True}]
    notes = [{'entity_id':'publication:methods-note:2026-W41:'+run, 'run_id':run,
        'title':'Exact '+run, 'claim_scope':'(h_landauer : PhysicalPremise.Landauer P) implies the exact bound',
        'foundation_basis':'CONDITIONAL_PL_PD', 'certifies':'LISTED_NOTE_SCOPE_ONLY',
        'disclaimer':DISCLAIMER, 'certificate_sha256':'c'*64, 'publication_binding_sha256':'d'*64,
        'semantic_labels':deepcopy(labels)} for run in ('Run-125','Run-126')]
    return {'entity_id':'publication:methods-digest:2026-W41:23226761', 'record_id':'23226761',
        'doi':'10.5281/zenodo.23226761', 'release_week':'2026-W41','title':'Exact digest title',
        'certifies':False,'disclaimer':DISCLAIMER,'registration_receipt_sha256':'a'*64,
        'public_readback_sha256':'b'*64,'publication_binding_sha256':'e'*64,'notes':notes}


class MethodsDigestPointerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.path=self.root/'digests.json'
        self.group=pointer()

    def config(self, rows=None):
        self.path.write_text(json.dumps({'standard':'PUBLIC_METHODS_DIGEST_POINTERS_1',
                                        'methods_digests':[self.group] if rows is None else rows}))
        return {'methods_digest_joins':{'path':'digests.json','sha256':hashlib.sha256(self.path.read_bytes()).hexdigest()}}

    def test_shared_doi_is_one_uncertified_group_with_independent_note_scopes(self):
        got=load_methods_digest_joins(self.root,self.config())
        self.assertEqual(got,[self.group]);self.assertIs(got[0]['certifies'],False)
        self.assertEqual(len(got[0]['notes']),2)
        self.assertEqual({n['certifies']for n in got[0]['notes']},{'LISTED_NOTE_SCOPE_ONLY'})
        self.assertIn('h_landauer',got[0]['notes'][0]['claim_scope'])
        self.assertNotIn('certificate_sha256',got[0]);self.assertNotIn('doi',got[0]['notes'][0])

    def test_aggregate_certification_or_spine_injection_rejects(self):
        for key,value in [('certifies',True),('status','verified'),('tier','spine'),
                          ('certificate_sha256','c'*64),('canon_eligible',True)]:
            v=deepcopy(self.group);v[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):load_methods_digest_joins(self.root,self.config([v]))

    def test_note_cannot_expand_scope_or_inject_source_labels(self):
        for key,value in [('certifies',True),('status','verified'),('tier','spine'),
                          ('claim_scope',''),('certificate_sha256',''),('disclaimer','empirical proof'),
                          ('foundation_basis','UNCONDITIONAL')]:
            v=deepcopy(self.group);v['notes'][0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):load_methods_digest_joins(self.root,self.config([v]))

    def test_same_week_note_and_group_identities_and_record_doi_are_exact(self):
        for key,value in [('doi','10.5281/zenodo.999'),('record_id','023226761'),('release_week','2026-W99'),
                          ('entity_id','publication:foundation')]:
            v=deepcopy(self.group);v[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):load_methods_digest_joins(self.root,self.config([v]))
        v=deepcopy(self.group);v['notes'][0]['entity_id']='publication:methods-note:2026-W40:Run-125'
        with self.assertRaises(ValueError):load_methods_digest_joins(self.root,self.config([v]))

    def test_duplicates_missing_notes_and_malformed_labels_reject(self):
        for change in ('duplicate_group','duplicate_note','no_notes','duplicate_label','missing_label','uppercase_hash'):
            v=deepcopy(self.group);rows=[v]
            if change=='duplicate_group':rows.append(deepcopy(v))
            elif change=='duplicate_note':v['notes'].append(deepcopy(v['notes'][0]))
            elif change=='no_notes':v['notes']=[]
            elif change=='duplicate_label':v['notes'][0]['semantic_labels']*=2
            elif change=='missing_label':v['notes'][0]['semantic_labels'][0].pop('nonvacuity_label')
            else:v['registration_receipt_sha256']='A'*64
            with self.subTest(change=change),self.assertRaises(ValueError):load_methods_digest_joins(self.root,self.config(rows))

    def test_triviality_and_undemonstrated_witness_remain_non_headline(self):
        for changes in ({'semantic_tier':'DEFINITIONAL'},
                        {'nonvacuity_label':'certified; nonvacuity not demonstrated'}):
            v=deepcopy(self.group);v['notes'][0]['semantic_labels'][0].update(changes)
            with self.assertRaises(ValueError):validate_methods_digests([v])
            v['notes'][0]['semantic_labels'][0]['headline_eligible']=False
            self.assertEqual(validate_methods_digests([v]),[v])

    def test_one_byte_join_change_and_path_escape_reject(self):
        config=self.config();self.path.write_bytes(self.path.read_bytes()+b' ')
        with self.assertRaisesRegex(ValueError,'SHA-256'):load_methods_digest_joins(self.root,config)
        config=self.config();link=self.root/'link.json';link.symlink_to(self.path)
        directory=self.root/'alias';directory.symlink_to(self.root,target_is_directory=True)
        for path in ['link.json','alias/digests.json','../digests.json',str(self.path)]:
            with self.subTest(path=path),self.assertRaises(ValueError):load_methods_digest_joins(self.root,{'methods_digest_joins':{**config['methods_digest_joins'],'path':path}})

    def test_missing_join_defaults_empty_not_certified(self):
        self.assertEqual(load_methods_digest_joins(self.root,{}),[])

    def test_schema_exact_closed_group_note_and_label_fields(self):
        schema=json.loads((ROOT/'docs/schemas/research-catalog-v1.json').read_text())
        group=schema['properties']['methods_digests']['items'];note=group['properties']['notes']['items'];label=note['properties']['semantic_labels']['items']
        for obj,fields in [(group,GROUP_FIELDS),(note,NOTE_FIELDS),(label,LABEL_FIELDS)]:
            self.assertFalse(obj['additionalProperties']);self.assertEqual(set(obj['properties']),fields)
            self.assertEqual(set(obj['required']),fields)
        self.assertIs(group['properties']['certifies']['const'],False)
        self.assertEqual(note['properties']['certifies']['const'],'LISTED_NOTE_SCOPE_ONLY')
        self.assertIn('methods_digests',schema['required'])

    def test_catalog_addition_preserves_generic_joins_and_source_counts(self):
        legacy={'entity_id':'publication:foundation','record_id':'23141592','doi':'10.5281/zenodo.23141592',
            'title':'Foundation','claim_scope':'Premise implies bound','disclaimer':DISCLAIMER,
            'public_readback_sha256':'1'*64,'publication_binding_sha256':'2'*64,'certificate_sha256':'3'*64}
        file=self.root/'legacy.json';file.write_text(json.dumps({'standard':'PUBLIC_SCOPED_PUBLICATION_POINTERS_1','publications':[legacy]}))
        config={'release':'test','repository':'','concept_doi':'','include':[],**self.config(),
            'publication_joins':{'path':'legacy.json','sha256':hashlib.sha256(file.read_bytes()).hexdigest()}}
        path=self.root/'config.json';path.write_text(json.dumps(config));v=build_catalog(self.root,path)
        self.assertEqual(v['publications'],[legacy]);self.assertEqual(v['methods_digests'],[self.group])
        self.assertEqual(v['stats']['records'],0);self.assertEqual(v['stats']['verified'],0);self.assertEqual(v['stats']['spine'],0)
        self.assertEqual(validate_catalog(v),[]);self.assertEqual(validate_catalog_sources(v,self.root,path),[])
        v['methods_digests'][0]['notes'][0]['claim_scope']='omitted premise'
        self.assertTrue(validate_catalog_sources(v,self.root,path))
        for mutate in ('doi','entity'):
            changed=deepcopy(legacy)
            if mutate=='doi':changed.update(record_id=self.group['record_id'],doi=self.group['doi'])
            else:changed['entity_id']=self.group['notes'][0]['entity_id']
            file.write_text(json.dumps({'standard':'PUBLIC_SCOPED_PUBLICATION_POINTERS_1','publications':[changed]}))
            config['publication_joins']['sha256']=hashlib.sha256(file.read_bytes()).hexdigest();path.write_text(json.dumps(config))
            with self.subTest(mutate=mutate),self.assertRaisesRegex(ValueError,'generic'):build_catalog(self.root,path)


class RegisteredProjectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.binding={'path':'registration.json','sha256':'a'*64};self.group=pointer()
        self.rows=[{'id':self.group['entity_id'],'path':'digest','registration_route':projection.GROUP_ROUTE,
            'entity_type':'METHODS_DIGEST_GROUP','registration_receipt':self.binding,'doi':self.group['doi'],
            'status':'SCOPED_DIGEST','certificate_valid':False,'certifies':False}]
        notes=[];children=[]
        for n in self.group['notes']:
            folder=self.root/n['run_id'];folder.mkdir();metadata=folder/'metadata.json';metadata.write_text(json.dumps({'title':n['title']}))
            claims=[{'english_claim':'Named premise implies bound','lean_theorem':'conditional_bound',
                'exact_source_signature':'theorem conditional_bound (h_landauer : PhysicalPremise.Landauer P) : bound',
                'explicit_binders_and_hypotheses':'h_landauer : PhysicalPremise.Landauer P',
                'ambient_source_context':[{'source_text':'variable P'}],'conclusion':'bound',
                'model_fidelity':{'defined':['P'],'empirically_identified':[]},'printed_disclaimer':DISCLAIMER}]
            notes.append({'run_id':n['run_id'],'path':str(folder),'metadata_binding':{'filename':'metadata.json','sha256':hashlib.sha256(metadata.read_bytes()).hexdigest()},
                          'statement_scope':claims,'claim_table':n['semantic_labels'],'foundation_basis':n['foundation_basis']})
            children.append({'id':n['entity_id'],'run_id':n['run_id'],'certificate':{'sha256':n['certificate_sha256']},'publication_binding':{'sha256':n['publication_binding_sha256']}})
            self.rows.append({'id':n['entity_id'],'path':n['run_id'],'registration_route':projection.NOTE_ROUTE,
                'entity_type':'METHODS_DIGEST_NOTE','registration_receipt':self.binding,'doi':self.group['doi'],
                'status':'CERTIFIED','certificate_valid':True,'certifies':'LISTED_NOTE_SCOPE_ONLY'})
        self.current={'receipt':{'record_id':self.group['record_id'],'doi':self.group['doi'],
            'release_week':self.group['release_week'],'children':children,'public_evidence':{'sha256':'b'*64},
            'digest_publication_binding':{'sha256':'e'*64}},'manifest':{'notes':notes},
            'public_legacy':{'metadata':{'title':self.group['title']}}}
        self.ledger={'tree_root':str(self.root),'file_entities':[],'run_entities':[], 'publication_entities':deepcopy(self.rows)}
        self.consume=Mock(return_value=self.current)
        self.registrar=SimpleNamespace(require_registration=self.consume,
            entity_rows=lambda root,binding,ledger,consume: (self.assertEqual(consume(root,binding,ledger),self.current) or deepcopy(self.rows)))

    def test_group_and_shared_doi_notes_render_without_claim_gate_or_aggregate_canon(self):
        with patch.object(projection,'_registrar',return_value=self.registrar),patch.object(index,'evaluate_publication',side_effect=AssertionError('no legacy intake for digest rows')):
            rendered=index.render_index(self.ledger)
        self.consume.assert_called_once_with(self.root.resolve(),self.binding,self.ledger)
        canon=json.loads(rendered['CANON_INDEX.json']);self.assertEqual(canon['entries'],[])
        digest=canon['methods_digests'][0];self.assertIs(digest['certifies'],False)
        self.assertEqual(len(digest['notes']),2)
        self.assertEqual(json.loads(digest['notes'][0]['claim_scope']),self.current['manifest']['notes'][0]['statement_scope'])
        self.assertEqual(digest['notes'][0]['semantic_labels'],self.current['manifest']['notes'][0]['claim_table'])
        self.assertEqual(digest['title'],'Exact digest title')
        self.assertEqual(json.loads(rendered['METHODS_DIGESTS.json'])['methods_digests'],canon['methods_digests'])
        labels=json.loads(rendered['ZENODO_DESCRIPTIONS.json'])['publication_registrations']
        self.assertIn('aggregate uncertified',labels[0]['label']);self.assertTrue(all(x['label']=='CERTIFIED_LISTED_NOTE_SCOPE_ONLY'for x in labels[1:]))
        self.assertNotIn('CERTIFIED_SCOPED_CLAIMS',rendered['README.md'])

    def test_actual_registrar_failure_holds_every_member_without_cached_pass(self):
        self.consume.side_effect=ValueError('current certificate or parity HOLD')
        with patch.object(projection,'_registrar',return_value=self.registrar):rendered=index.render_index(self.ledger)
        self.assertEqual(json.loads(rendered['METHODS_DIGESTS.json'])['methods_digests'],[])
        labels=json.loads(rendered['ZENODO_DESCRIPTIONS.json'])['publication_registrations'];self.assertTrue(all(x['label']=='UNCERTIFIED'for x in labels))
        self.assertTrue(all('current certificate or parity HOLD'in x['gate_reasons'][0]for x in labels))

    def test_changed_held_missing_duplicate_or_orphaned_ssot_member_never_qualifies(self):
        for kind in ('changed_scope','missing_child','duplicate_child','orphan'):
            ledger=deepcopy(self.ledger)
            if kind=='changed_scope':ledger['publication_entities'][1]['certifies']=True
            elif kind=='missing_child':ledger['publication_entities'].pop()
            elif kind=='duplicate_child':ledger['publication_entities'].append(deepcopy(ledger['publication_entities'][1]))
            else:ledger['publication_entities']=ledger['publication_entities'][1:]
            with self.subTest(kind=kind),patch.object(projection,'_registrar',return_value=self.registrar):
                pointers,held=projection.registered_digest_pointers(self.root,ledger)
                self.assertEqual(pointers,[]);self.assertEqual(set(held),{r['id']for r in ledger['publication_entities']})

    def test_one_byte_bound_note_metadata_change_holds_entire_cohort(self):
        file=self.root/'Run-125/metadata.json';file.write_bytes(file.read_bytes()+b' ')
        with patch.object(projection,'_registrar',return_value=self.registrar):pointers,held=projection.registered_digest_pointers(self.root,self.ledger)
        self.assertEqual(pointers,[]);self.assertEqual(len(held),3)
        self.assertTrue(all('metadata changed'in value[0]for value in held.values()))

    def test_public_scope_projection_redacts_local_roots_without_editing_evidence(self):
        claim=self.current['manifest']['notes'][0]['statement_scope'][0];claim['diagnostic']=str(self.root)+'/note'
        with patch.object(projection,'_registrar',return_value=self.registrar):rendered=index.render_index(self.ledger)
        for value in rendered.values():self.assertNotIn(str(self.root),value)
        self.assertEqual(claim['diagnostic'],str(self.root)+'/note')
        digest=json.loads(rendered['METHODS_DIGESTS.json'])['methods_digests'][0]
        self.assertIn('[canonical mirror]/note',digest['notes'][0]['claim_scope'])

    def test_portal_collection_display_uses_text_and_preserves_note_labels(self):
        page=(ROOT/'docs/index.html').read_text();app=(ROOT/'docs/assets/app.js').read_text()
        self.assertIn('id="methods-digest-links"',page);self.assertIn('no aggregate theorem certificate',page)
        body=app.split('function renderMethodsDigestPointers(digests) {',1)[1].split('\nasync function init()',1)[0]
        self.assertNotIn('innerHTML',body);self.assertIn('scope.textContent = note.claim_scope',body)
        self.assertIn('claim.semantic_tier',body);self.assertIn('claim.nonvacuity_label',body)
        self.assertIn('aggregate uncertified',body)

    def test_registrar_resolver_requires_own_or_exact_byte_identical_installed_source(self):
        source=ROOT/'00_lab_infrastructure/gates/methods_digest_registration.py'
        installed=self.root/'RESEARCH_PIPELINE_v2/verification_coverage_gates/methods_digest_registration.py'
        installed.parent.mkdir(parents=True);installed.write_bytes(source.read_bytes())
        module=SimpleNamespace(__file__=str(installed))
        with patch.object(projection.importlib,'import_module',return_value=module):
            self.assertIs(projection._registrar(self.root),module)
            installed.write_bytes(source.read_bytes()+b' ')
            with self.assertRaisesRegex(ValueError,'different checkout'):projection._registrar(self.root)
        foreign=self.root/'foreign.py';foreign.write_bytes(source.read_bytes())
        with patch.object(projection.importlib,'import_module',return_value=SimpleNamespace(__file__=str(foreign))):
            with self.assertRaisesRegex(ValueError,'different checkout'):projection._registrar(self.root)


if __name__=='__main__':unittest.main()
