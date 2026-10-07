import unittest,tempfile,json,os,datetime as dt
from pathlib import Path
from unittest.mock import patch
import phase7_mutation_baseline as m

class MutationTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.r=Path(self.t.name).resolve();self.reports=self.r/'reports/verification-coverage';self.reports.mkdir(parents=True);self.now='2026-10-07T15:00:00+00:00';self.old='2026-10-07T14:00:00+00:00';self.p=self.put('evidence.json',{'source':'actual'},self.old)
 def put(self,name,v,at=None):
  p=self.reports/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v));stamp=m.utc(at or self.now).timestamp();os.utime(p,(stamp,stamp));return p
 def receipt(self,name='actual.json',status='HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE',environment='zenodo.org',url='https://zenodo.org/api/records/123/draft'):
  v={'environment':environment,'method':'PUT','url':url,'status':status,'request_body_sha256':'a'*64}
  if status=='HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE':v.update(response_sha256='b'*64,response={'modified':self.old})
  return self.put(name,v,self.now if hasattr(self,'ip')else self.old)
 def activate(self,capture=None):
  baseline=capture or m.capture(self.r,self.old);bp=self.r/Path(m.JOURNAL).parent/'MUTATION_BASELINE-v001.json';bp.parent.mkdir(parents=True,exist_ok=True);bp.write_text(json.dumps(baseline));self.index={'standard':m.INDEX_STANDARD,'status':'ACTIVE','baseline':{'path':str(bp),'sha256':m.sha(bp.read_bytes())},'reservations':[],'updated_at_utc':self.old};self.ip=self.r/m.JOURNAL;self.ip.write_text(json.dumps(self.index));return bp
 def saveindex(self):self.ip.write_text(json.dumps(self.index))
 def reserve(self,id='own-1',at=None):
  v={'operation_id':id,'method':'PUT','url':'https://zenodo.org/api/records/123/draft','request_body_sha256':'a'*64,'transport_receipt_path':str(self.reports/'actual.json')};p=self.put(id+'-request.json',v,self.now);r={'operation_id':id,'method':'PUT','host':'zenodo.org','at_utc':at or self.old,'status':'STARTED_NO_RETRY','receipt_binding':{'path':str(p),'sha256':m.sha(p.read_bytes())}};rp=self.put(id+'-reservation.json',r,self.now);self.index['reservations'].append({'path':str(rp),'sha256':m.sha(rp.read_bytes())});self.saveindex();return rp
 def test_missing_baseline_hold(self):
  with self.assertRaises(Exception):m.require_events(self.r,self.now)
 def test_empty_complete_cannot_supply(self):
  b=m.capture(self.r,self.old);b['source_inventory']=[];self.activate(b)
  with self.assertRaisesRegex(ValueError,'empty baseline'):m.require_events(self.r,self.now)
 def test_complete_unknown_flag_rejected(self):
  b=m.capture(self.r,self.old);b['complete']=True;self.activate(b)
  with self.assertRaisesRegex(ValueError,'capture'):m.require_events(self.r,self.now)
 def test_omitted_earlier_input_hold(self):
  self.put('other.json',{},self.old);b=m.capture(self.r,self.old);b['source_inventory']=b['source_inventory'][:1];self.activate(b)
  with self.assertRaisesRegex(ValueError,'omitted'):m.require_events(self.r,self.now)
 def test_identical_success_without_origin_counts_both(self):
  self.receipt();self.receipt('copy.json');self.activate();self.assertEqual(len(m.require_events(self.r,self.now)),2)
 def test_uncertain_copies_never_dedup(self):
  self.receipt(status='HOLD_TRANSPORT_UNCERTAIN_NO_RETRY');self.receipt('copy.json',status='HOLD_TRANSPORT_UNCERTAIN_NO_RETRY');self.activate();self.assertEqual(len(m.require_events(self.r,self.now)),2)
 def test_started_attempt_counts(self):
  self.receipt(status='STARTED_NO_RETRY');self.activate();self.assertEqual(len(m.require_events(self.r,self.now)),1)
 def test_sandbox_ignored(self):
  self.receipt(environment='sandbox.zenodo.org',url='https://sandbox.zenodo.org/api/x');self.activate();self.assertEqual(m.require_events(self.r,self.now),[])
 def test_wrong_url_hold(self):
  self.receipt(url='https://zenodo.org.evil/api/x')
  with self.assertRaisesRegex(ValueError,'own-host'):m.capture(self.r,self.old)
 def test_missing_request_hash_hold(self):
  p=self.receipt();v=json.loads(p.read_text());v.pop('request_body_sha256');p.write_text(json.dumps(v))
  with self.assertRaises(ValueError):m.capture(self.r,self.old)
 def test_public_receipt_disappears_hold(self):
  p=self.receipt();self.activate();p.unlink()
  with self.assertRaisesRegex(ValueError,'disappeared'):m.require_events(self.r,self.now)
 def test_public_receipt_changed_hold(self):
  p=self.receipt();self.activate();p.write_text(p.read_text()+' ')
  with self.assertRaisesRegex(ValueError,'receipt changed'):m.require_events(self.r,self.now)
 def test_later_receipt_counts(self):
  self.activate();p=self.receipt();stamp=m.utc(self.now).timestamp();os.utime(p,(stamp,stamp));self.assertEqual(len(m.require_events(self.r,self.now)),1)
 def test_reservation_subsumed_exact_once(self):
  self.activate();self.reserve();self.reserve('own-2');p=self.receipt();stamp=m.utc(self.now).timestamp();os.utime(p,(stamp,stamp));self.assertEqual(len(m.require_events(self.r,self.now)),2)
 def test_same_success_copy_does_not_subsume_two(self):
  self.activate();self.reserve();self.reserve('own-2');self.receipt();self.receipt('copy.json');self.assertEqual(len(m.require_events(self.r,self.now)),3)
 def test_uncertain_plus_reservation_counts_once(self):
  self.activate();self.reserve();self.receipt(status='HOLD_TRANSPORT_UNCERTAIN_NO_RETRY');self.assertEqual(len(m.require_events(self.r,self.now)),1)
 def test_unattempted_reservation_counts(self):
  self.activate();self.reserve();self.assertEqual(len(m.require_events(self.r,self.now)),1)
 def test_unordered_reservation_hold(self):
  self.activate();self.reserve(at=self.now);self.reserve('own-2',at=self.old)
  with self.assertRaisesRegex(ValueError,'order/time'):m.require_events(self.r,self.now)
 def test_reservation_future_hold(self):
  self.activate();self.reserve(at='2026-10-08T00:00:00Z')
  with self.assertRaisesRegex(ValueError,'order/time'):m.require_events(self.r,self.now)
 def test_forged_reservation_body_hash_hold(self):
  self.activate();p=self.reserve();v=json.loads(p.read_text());v['receipt_binding']['sha256']='c'*64;p.write_text(json.dumps(v));os.utime(p,(m.utc(self.now).timestamp(),)*2);self.index['reservations'][0]['sha256']=m.sha(p.read_bytes());self.saveindex()
  with self.assertRaisesRegex(ValueError,'binding changed'):m.require_events(self.r,self.now)
 def test_future_uncertain_conservative_today(self):
  p=self.receipt(status='HOLD_TRANSPORT_UNCERTAIN_NO_RETRY');self.activate();events=m.require_events(self.r,self.now);stat=m.read(p)[1];stat['mtime_ns']=int(m.utc('2026-11-01T00:00:00Z').timestamp()*1e9);self.assertEqual(m._receipt_events([{'path':str(p),'stat':stat,'receipt':json.loads(p.read_text())}],m.utc(self.now))[0]['at_utc'],m.utc(self.now).isoformat())
 def test_symlink_hold(self):
  (self.reports/'link.json').symlink_to(self.p)
  with self.assertRaisesRegex(ValueError,'symlink'):m.capture(self.r,self.old)
 def test_new_york_day_boundary(self):
  from zoneinfo import ZoneInfo
  r={'path':'x','stat':{'mtime_ns':0,'sha256':'f'*64},'receipt':{'environment':'zenodo.org','method':'PUT','url':'https://zenodo.org/api/x','status':'HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE','request_body_sha256':'a'*64,'response_sha256':'b'*64,'response':{'modified':'2026-10-07T03:59:00Z'}}};e=m._receipt_events([r],m.utc(self.now))[0];self.assertEqual(m.utc(e['at_utc']).astimezone(ZoneInfo('America/New_York')).date().isoformat(),'2026-10-06')
 def test_inventory_race_hold(self):
  real=m._paths;n=0
  def altered(root):
   nonlocal n;n+=1;return real(root)if n==1 else[]
  with patch.object(m,'_paths',altered),self.assertRaisesRegex(ValueError,'inventory changed'):m.capture(self.r,self.old)

class DailyBudgetTests(unittest.TestCase):
 def test_nine_attempts_allow_one_not_more(self):
  from methods_digest import require_write_budget
  rows=[{'operation_id':str(i),'method':'PUT','host':'zenodo.org','at_utc':'2026-10-07T15:00:00Z','status':'STARTED_NO_RETRY','receipt_binding':{'path':'synthetic:'+str(i),'sha256':'a'*64}}for i in range(9)]
  self.assertEqual(require_write_budget(rows,'POST','2026-10-07T16:00:00Z',complete=True)['remaining_including_next'],1)
 def test_ten_attempts_hold(self):
  from methods_digest import require_write_budget
  rows=[{'operation_id':str(i),'method':'PUT','host':'zenodo.org','at_utc':'2026-10-07T15:00:00Z','status':'STARTED_NO_RETRY','receipt_binding':{'path':'synthetic:'+str(i),'sha256':'a'*64}}for i in range(10)]
  with self.assertRaises(ValueError):require_write_budget(rows,'POST','2026-10-07T16:00:00Z',complete=True)

if __name__=='__main__':unittest.main()
