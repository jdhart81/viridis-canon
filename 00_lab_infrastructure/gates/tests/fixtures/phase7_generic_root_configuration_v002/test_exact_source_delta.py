"""Reversing the approved relocation seam restores the exact old source."""
from pathlib import Path
import unittest
class SourceDelta(unittest.TestCase):
 def test_only_copy_reference_seam_changed(self):
  current=(Path(__file__).parent/'root_weekly_configuration.py').read_bytes()
  original=(Path(__file__).parent/'repo_sources/predecessor/root_weekly_configuration.py').read_bytes()
  a=current.index(b'def _exact_rebound_merge_references(');b=current.index(b'def require_merge(',a)
  reverted=current[:a]+current[b:]
  reverted=reverted.replace(b"TMP=Path('/private/tmp')\n",b'')
  before=b" for field,name in [('merged_pr','MERGED_PR.json'),('merged_commit','MERGED_COMMIT.json'),('merged_tree','COMPLETE_MERGED_TREE.json')]:need(result.get(field)==evidence[name],'OWN_MERGE_REFERENCES')\n"
  reverted=reverted.replace(b' _exact_rebound_merge_references(evidence,result)\n',before)
  self.assertEqual(reverted,original)
if __name__=='__main__':unittest.main()
