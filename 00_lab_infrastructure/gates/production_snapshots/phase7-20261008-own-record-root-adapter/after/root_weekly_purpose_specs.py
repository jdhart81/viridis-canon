"""Closed root-call extension; reviewed29b3e0 successor proves all final bytes.

These three are immutable purpose copies, never extra runtime namespace writes.
No automatic copy, API, credential, install, status or acceptance operation.
"""
from pathlib import Path
PINS={'nightly_release_checkpoint.py':'35c2d8ba078aec91100a3b7cb987cadc7e3d172405eeab48fc08ced232ba2c9f','prepare_nightly_note.py':'f2421402521d9316d61895b84ab033d8e3cc7f744f4b77c15502a445775cc2a2','digest_weekly_render.py':'03bb0f605d42fcb46a1ef3be68f6bf7e9f5556af4b7805eeefeced39e63c9443'}
ADOPTER_SHA='cec387e1d993ec93f001e8eb33b2c8c89ad53104db93a0ab4da12554cb462129'
def add_purpose_specs(adopter,checkout,tree,specs):
 adopter.need(adopter.sha(adopter.__file__)==ADOPTER_SHA,'UNCHANGED_REVIEWED_ADOPTER');checkout=Path(checkout).resolve(strict=True);adopter.need(isinstance(specs,list)and not(set(PINS)&{r.get('name')for r in specs}),'NO_PURPOSE_SPEC_REPLAY_OR_COLLISION');result=[dict(r)for r in specs]
 for name,pin in PINS.items():
  gp='00_lab_infrastructure/gates/'+name;source=checkout/gp;adopter.need(adopter.sha(source)==pin,'EXACT_REVIEWED_WEEKLY_PURPOSE:'+name);result.append({'name':name,'source':str(source),'git_path':gp,'destination':name})
 adopter.exact_sources(tree,result);return result
if __name__=='__main__':raise SystemExit('HOLD: root explicit actual merged-tree caller only')
