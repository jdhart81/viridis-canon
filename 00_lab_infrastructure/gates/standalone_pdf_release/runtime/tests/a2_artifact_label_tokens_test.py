"""Source-only label derivation controls over synthetic, self-contained TeX.

These cases exercise the new pure derivation seam. They do not establish PDF
rendering, genuine predecessor admission, certification or publication authority.
No installed Core module, renderer, cache or manuscript is loaded here.
"""
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import nightly_manuscript_access as access


APPROVED_TEXT = (
    "UNCERTIFIED — no issuer-produced Viridis Comparator certificate binds the "
    "exact bytes of this derived manuscript. Attached certificates cover only "
    "their exact sealed predecessors and quoted formal statements under their "
    "stated hypotheses. They do not certify this new PDF, its prose, the "
    "historical manuscript, or empirical claims. Results remain conditional on "
    "the stated model assumptions."
)

ARTICLE = br"""\documentclass[10pt]{article}
\usepackage[margin=0.78in]{geometry}
\usepackage{amsmath,amssymb,amsthm,booktabs,microtype,hyperref}
\hypersetup{hidelinks}
\newtheorem{proposition}{Proposition}
\title{A Synthetic {Nested Title} Note}
\author{Example Author\\Example Research\\\texttt{fixture@example.invalid}}
\date{17 October 2026}
\begin{document}
\maketitle
\begin{abstract}
This synthetic manuscript states no production or scientific admission.
\end{abstract}
\begin{proposition}
For every real number $x$, $x=x$.
\end{proposition}
\begin{proof}
Reflexivity.
\end{proof}
\end{document}
"""

CURRENT_TEMPLATE = br"""\documentclass[10pt]{article}
\usepackage[margin=0.75in]{geometry}
\usepackage{amsmath,amssymb,fvextra}
\emergencystretch=4em
\AtBeginDocument{\sloppy}
\AtBeginDocument{\DeclareRobustCommand{\_}{\textunderscore\allowbreak}}
\title{Run-191: exact certified mathematical statement scope}
\author{Example Author}
\date{}
\begin{document}
\maketitle
\begin{abstract}
Only the exact quoted mathematical scope of this synthetic fixture is asserted.
\end{abstract}
\VerbatimInput[fontsize=\scriptsize,breaklines=true,breakanywhere=true]{rendered/FROZEN_CONTEXT.txt}
\end{document}
"""


class ArtifactLabelTokenTests(unittest.TestCase):
    def derive(self, original, *, historical=True):
        return access.labelled_tex(original, historical=historical)

    def inserted_only(self, original, *, historical=True):
        """Check correspondence independently of the insertion's TeX styling."""
        actual = self.derive(original, historical=historical)
        self.assertIsInstance(actual, bytes)
        marker = br'\maketitle'
        position = original.index(marker) + len(marker)
        extra = len(actual) - len(original)
        self.assertGreater(extra, 0)
        self.assertEqual(actual[:position], original[:position])
        self.assertEqual(actual[position + extra:], original[position:])
        self.assertEqual(actual[:position] + actual[position + extra:], original)
        insertion = actual[position:position + extra]
        self.assertEqual(insertion.count(APPROVED_TEXT.encode('utf-8')), 1)
        self.assertEqual(actual.count(APPROVED_TEXT.encode('utf-8')), 1)
        self.assertNotIn(b'[U+2014]', insertion)
        self.assertNotIn(br'\u2014', insertion)
        return actual, insertion

    def holds(self, original, *, historical=True):
        with self.assertRaises(ValueError):
            self.derive(original, historical=historical)

    def test_exact_approved_unicode_label_is_not_reworded(self):
        self.assertEqual(access.LABEL_TEXT, APPROVED_TEXT)
        self.assertIn('—', access.LABEL_TEXT)

    def test_native_article_label_is_single_insertion_and_exact_inverse(self):
        self.inserted_only(ARTICLE)

    def test_current_template_keeps_fixed_verbatim_and_begin_document_hooks(self):
        # This pure seam receives a template already admitted by its genuine
        # predecessor owner. It cannot apply historical N1 to that template.
        self.inserted_only(CURRENT_TEMPLATE, historical=False)
        self.holds(CURRENT_TEMPLATE, historical=True)

    def test_ordinary_nested_title_braces_do_not_move_the_insertion(self):
        original = ARTICLE.replace(b'{Nested Title}', b'{Nested {Title} Detail}')
        self.inserted_only(original)

    def test_comment_lookalikes_do_not_count_as_document_or_title_commands(self):
        original = ARTICLE.replace(
            br'\title{',
            b'% fake \\begin{document} \\maketitle \\end{document}\n' + br'\title{',
            1,
        )
        actual = self.derive(original)
        # The first raw occurrence is a comment; the real title is the one
        # between the genuine document start and the abstract.
        position = original.index(b'\n\\maketitle\n') + len(b'\n\\maketitle')
        extra = len(actual) - len(original)
        self.assertEqual(actual[:position] + actual[position + extra:], original)
        self.assertIn(APPROVED_TEXT.encode(), actual[position:position + extra])

    def test_comment_cr_lf_and_crlf_boundaries_keep_later_commands_active(self):
        for ending in (b'\n', b'\r', b'\r\n'):
            with self.subTest(ending=ending):
                original = ARTICLE.replace(
                    b'\n\\maketitle\n',
                    b'\n% fake \\maketitle' + ending + b'\\maketitle\n',
                )
                actual = self.derive(original)
                self.assertEqual(actual.count(APPROVED_TEXT.encode()), 1)
                self.assertIn(b'% fake \\maketitle' + ending + b'\\maketitle', actual)

    def test_escaped_controls_and_percent_do_not_create_extra_active_titles(self):
        original = ARTICLE.replace(
            b'Reflexivity.',
            br'Reflexivity. Literal \\maketitle, escaped \% and \{braces\}.',
        )
        self.inserted_only(original)

    def test_comment_between_document_start_and_real_title_is_preserved(self):
        original = ARTICLE.replace(
            b'\\begin{document}\n\\maketitle',
            b'\\begin{document}\n% only a comment\n\t\\maketitle',
        )
        self.inserted_only(original)

    def test_nested_active_title_command_cannot_be_a_label_anchor(self):
        original = ARTICLE.replace(
            br'\title{A Synthetic {Nested Title} Note}',
            br'\title{A Synthetic {\maketitle} Note}',
        )
        self.holds(original)

    def test_nested_document_begin_cannot_be_a_label_anchor(self):
        original = ARTICLE.replace(
            br'\title{A Synthetic {Nested Title} Note}',
            br'\title{A Synthetic {\begin{document}} Note}',
        )
        self.holds(original)

    def test_duplicate_active_titles_hold_in_both_modes(self):
        original = ARTICLE.replace(br'\maketitle', br'\maketitle\maketitle')
        for historical in (True, False):
            with self.subTest(historical=historical):
                self.holds(original, historical=historical)

    def test_only_commented_title_does_not_count(self):
        self.holds(ARTICLE.replace(br'\maketitle', b'% \\maketitle'))

    def test_only_escaped_title_does_not_count(self):
        self.holds(ARTICLE.replace(br'\maketitle', br'\\maketitle'))

    def test_title_before_document_start_holds(self):
        original = ARTICLE.replace(
            b'\\begin{document}\n\\maketitle',
            b'\\maketitle\n\\begin{document}',
        )
        self.holds(original)

    def test_title_after_document_end_holds(self):
        original = ARTICLE.replace(b'\\maketitle\n', b'', 1)
        self.holds(original + b'\\maketitle\n')

    def test_missing_or_repeated_document_boundaries_hold(self):
        for original in (
            ARTICLE.replace(br'\begin{document}', b''),
            ARTICLE.replace(br'\end{document}', b''),
            ARTICLE.replace(br'\begin{document}', br'\begin{document}\begin{document}'),
            ARTICLE.replace(br'\end{document}', br'\end{document}\end{document}'),
        ):
            with self.subTest(original=original):
                self.holds(original)

    def test_body_content_before_title_is_not_a_page_one_title_contract(self):
        original = ARTICLE.replace(
            b'\\begin{document}\n\\maketitle',
            b'\\begin{document}\nBody before title.\n\\maketitle',
        )
        self.holds(original)

    def test_unbalanced_source_braces_hold_before_any_derivation(self):
        for original in (
            ARTICLE.replace(br'\title{A Synthetic {Nested Title} Note}',
                            br'\title{A Synthetic {Nested Title} Note'),
            ARTICLE.replace(br'\title{A Synthetic {Nested Title} Note}',
                            br'\title{A Synthetic {Nested Title} Note}}'),
        ):
            with self.subTest(original=original):
                self.holds(original)

    def test_historical_file_readers_macro_aliases_and_cache_escape_hold(self):
        for dangerous in (
            br'\input{other.tex}',
            br'\include{other.tex}',
            br'\includegraphics{other.pdf}',
            br'\bibliography{refs}',
            br'\openin1=other.tex',
            br'\write18{command}',
            br'\catcode`\%=12',
            br'\def\alias{\input}\alias{other.tex}',
            br'\let\alias\input\alias{other.tex}',
            br'\csname input\endcsname{other.tex}',
            br'\usepackage{../../outside}',
            br'\documentclass{../outside}',
            br'\begin{filecontents}{other}\end{filecontents}',
        ):
            with self.subTest(dangerous=dangerous):
                self.holds(ARTICLE.replace(br'\end{document}', dangerous + br'\end{document}'))

    def test_historical_translation_and_format_characters_hold(self):
        for dangerous in (
            br'\in^^70ut{other.tex}',
            '\\in\x00put{other.tex}'.encode(),
            '\\in\u200bput{other.tex}'.encode(),
            '\\in\ufeffput{other.tex}'.encode(),
        ):
            with self.subTest(dangerous=dangerous):
                self.holds(ARTICLE.replace(br'\end{document}', dangerous + br'\end{document}'))

    def test_existing_approved_banner_cannot_be_nested_or_repeated(self):
        already = ARTICLE.replace(br'\maketitle', br'\maketitle' + APPROVED_TEXT.encode())
        self.holds(already)
        self.holds(self.derive(ARTICLE), historical=False)


if __name__ == '__main__':
    unittest.main(verbosity=2)
