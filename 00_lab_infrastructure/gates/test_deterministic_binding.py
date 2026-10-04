import unittest
from deterministic_binding import strict_status_only,normalized_pdf_text
class DeterministicReviewTests(unittest.TestCase):
    def paper(self,text):return '\\documentclass{article}\n\\begin{document}\n'+text+'\n\\end{document}'
    def test_status_only_passes(self):
        a=self.paper('Comparator certification pending.\n\n\\[r=2\\]')
        b=self.paper('Comparator certification completed.\n\n\\[r=2\\]')
        self.assertTrue(strict_status_only(a,b)[0])
    def test_changed_equation_holds(self):
        self.assertFalse(strict_status_only(self.paper('Comparator pending. $r=2$'),self.paper('Comparator certified. $r=3$'))[0])
    def test_non_status_section_title_holds(self):
        self.assertFalse(strict_status_only(self.paper('\\section{Scalar scope} Same claim.'),self.paper('\\section{Vector scope} Same claim.'))[0])
    def test_status_title_permitted(self):
        self.assertTrue(strict_status_only(self.paper('\\section{Verification status} Same claim.'),self.paper('\\section{Comparator status} Same claim.'))[0])
    def test_pdf_text_normalizes_layout_not_numbers_or_claims(self):
        self.assertEqual(normalized_pdf_text('same\nclaim 26,691'),normalized_pdf_text('same claim 26,691'))
        self.assertNotEqual(normalized_pdf_text('26,691'),normalized_pdf_text('27,131'))
        self.assertNotEqual(normalized_pdf_text('x >= y'),normalized_pdf_text('x <= y'))
    def test_complete_issuance_validates_its_receipt(self):
        import tempfile,json
        from pathlib import Path
        from unittest.mock import patch
        from deterministic_binding import issue
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);artifact=root/'paper';artifact.mkdir();cert=root/'cert.json';cert.write_text(json.dumps({'issued_at_utc':'2026-01-01T00:00:00Z'}))
            tex=artifact/'paper.tex';pdf=artifact/'paper.pdf';tex.write_text(self.paper('Same scientific claim. $r=2$'));pdf.write_bytes(b'%PDF-1.4\n%%EOF')
            import hashlib
            digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
            inspection={'valid':True,'sealed_paper_inputs':{'SEALED_paper.tex':{'path':str(tex),'sha256':digest(tex)},'SEALED_paper.pdf':{'path':str(pdf),'sha256':digest(pdf)}}}
            authority=root/'GAME_PLAN.md';authority.write_text('Gate 1 decisions & full-completion authorization — 2026-10-04\n27 status-only bindings')
            with patch('deterministic_binding.inspect_certificate',return_value=inspection):
                result=issue(artifact,cert,root,authority,root/'review')
            self.assertEqual(result['status'],'RULE_PASS')
            self.assertTrue((artifact/'PUBLICATION_BINDING.json').exists())
