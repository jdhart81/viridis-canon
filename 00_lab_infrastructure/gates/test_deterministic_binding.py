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
