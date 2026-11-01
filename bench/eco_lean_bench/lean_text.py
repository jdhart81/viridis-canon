"""Comment-aware reading of Lean 4 source for the Eco-Lean Bench precheck.

This is a text-level reader, not a Lean parser. It is enough to find the
top-level declarations in a challenge or solution file, give each its fully
qualified name, and pull out a theorem's statement (everything between the
name and the top-level `:=`). The authoritative verdict always comes from the
Lean kernel through comparator; this module only lets a score be prechecked
in a second, with no Lean install.

--- INVARIANTS ---
T1  strip() blanks every comment (line, nested block, doc) and the inside of
    every string literal, and keeps every newline, so offsets and line
    numbers in the stripped text match the original.
T2  A `sorry`, `admit` or `axiom` that appears only in a comment or a string
    is never reported.
T3  declarations() returns top-level commands in source order; each one's
    `qualname` is the namespace stack joined with its own name, with a
    leading `_root_.` honoured.
T4  statement() is whitespace-normalised: two statements that differ only in
    spacing or line breaks compare equal; any other difference does not.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

DECL_KINDS = ("theorem", "lemma", "def", "abbrev", "structure", "instance",
              "inductive", "class", "axiom", "opaque", "example")
MODIFIERS = ("private", "protected", "noncomputable", "partial", "unsafe", "nonrec")
# Commands that end the previous declaration when they start a line.
OTHER_COMMANDS = ("namespace", "end", "section", "open", "variable", "universe",
                  "set_option", "import", "attribute", "noncomputable section",
                  "#check", "#eval", "#print", "#exit", "mutual", "omit", "include",
                  "local", "scoped", "macro", "syntax", "notation", "infix", "infixl",
                  "infixr", "prefix", "postfix", "elab", "deriving")

_ID_CHAR = re.compile(r"[\w'!?.·₀-ₜᵢ-ᵪ]")


def strip(src: str) -> str:
    """T1/T2: blank comments and string contents; keep newlines and length."""
    out = list(src)
    i, n = 0, len(src)

    def blank(a: int, b: int) -> None:
        for k in range(a, b):
            if out[k] != "\n":
                out[k] = " "

    while i < n:
        c = src[i]
        if src.startswith("--", i):
            j = src.find("\n", i)
            j = n if j == -1 else j
            blank(i, j)
            i = j
        elif src.startswith("/-", i):
            depth, j = 1, i + 2
            while j < n and depth:
                if src.startswith("/-", j):
                    depth += 1
                    j += 2
                elif src.startswith("-/", j):
                    depth -= 1
                    j += 2
                else:
                    j += 1
            blank(i, j)
            i = j
        elif c == '"':
            j = i + 1
            while j < n and src[j] != '"':
                j += 2 if src[j] == "\\" else 1
            blank(i + 1, min(j, n))  # keep the quotes, blank the contents
            i = j + 1
        elif c == "'" and (i == 0 or not _ID_CHAR.match(src[i - 1])):
            m = re.compile(r"'(\\.|[^\\'\n])'").match(src, i)
            if m:
                blank(i + 1, m.end() - 1)
                i = m.end()
            else:
                i += 1
        elif c == "«":  # «guillemet identifiers» may hold anything
            j = src.find("»", i)
            i = n if j == -1 else j + 1
        else:
            i += 1
    return "".join(out)


def has_token(code: str, word: str) -> list[int]:
    """1-based line numbers where `word` appears as a whole token in stripped code."""
    pat = re.compile(r"(?<![\w'.])" + re.escape(word) + r"(?![\w'!?])")
    return [code.count("\n", 0, m.start()) + 1 for m in pat.finditer(code)]


_ATTR = r"(?:@\[[^\]]*\]\s*)*"
_MODS = r"(?:(?:" + "|".join(MODIFIERS) + r")\s+)*"
_DECL_RE = re.compile(r"^" + _ATTR + _MODS + r"(" + "|".join(DECL_KINDS) + r")\b", re.M)
_CMD_RE = re.compile(r"^(?:" + "|".join(re.escape(c) for c in OTHER_COMMANDS) + r")\b", re.M)
_NAME_RE = re.compile(r"\s*((?:«[^»]*»|[^\s:({\[⦃]+))")


@dataclass
class Decl:
    kind: str
    name: str            # as written ("" for example / anonymous instance)
    qualname: str
    text: str            # stripped source of the whole declaration
    line: int            # 1-based line of the keyword
    namespace: tuple = field(default_factory=tuple)
    signature_at: int = 0  # offset in `text` just after the name

    def _split(self) -> tuple[str, str]:
        rest = self.text[self.signature_at:]
        k = _proof_start(rest)
        return rest[:k], rest[k:]

    def statement(self) -> str:
        """T4: the text after the name up to the top-level `:=`, `|` or `where`."""
        return normalize(self._split()[0])

    def proof(self) -> str:
        return normalize(self._split()[1])


def normalize(s: str) -> str:
    return " ".join(s.split())


def _proof_start(s: str) -> int:
    """Index of the proof: the first top-level `:=` not owned by a `let`/`have`
    in the statement, an equation `| pat =>` at line start, or `where`."""
    depth, i, n, pending = 0, 0, len(s), 0
    while i < n:
        c = s[i]
        if c in "([{⟨⦃":
            depth += 1
        elif c in ")]}⟩⦄":
            depth = max(0, depth - 1)
        elif depth == 0:
            word = _word_at(s, i)
            if word in ("let", "have"):
                pending += 1
            elif s.startswith(":=", i):
                if not pending:
                    return i
                pending -= 1
                i += 2
                continue
            elif c == "|" and s[:i].rstrip(" \t").endswith("\n") and s[i + 1:i + 2].isspace() \
                    and "=>" in s[i:s.find("\n", i) if "\n" in s[i:] else n]:
                return i
            elif word == "where":
                return i
            if word:
                i += len(word)
                continue
        i += 1
    return n


def _word_at(s: str, i: int) -> str:
    """The identifier starting at i, or "" if i is inside or not at an identifier."""
    if i > 0 and _ID_CHAR.match(s[i - 1]):
        return ""
    m = re.compile(r"[A-Za-z_][\w'!?]*").match(s, i)
    return m.group(0) if m else ""


def declarations(src: str) -> list[Decl]:
    """T3: top-level declarations with namespace-qualified names."""
    code = strip(src)
    starts = sorted({m.start() for m in _DECL_RE.finditer(code)} |
                    {m.start() for m in _CMD_RE.finditer(code)})
    starts.append(len(code))
    stack: list[tuple[str, str]] = []  # ("ns" | "sec", name)
    decls: list[Decl] = []
    for a, b in zip(starts, starts[1:]):
        chunk = code[a:b]
        head = chunk.split(None, 2)
        if not head:
            continue
        if head[0] == "namespace" and len(head) > 1:
            stack.append(("ns", head[1]))
            continue
        if head[0] == "section" or chunk.startswith("noncomputable section"):
            parts = chunk.split()
            stack.append(("sec", parts[2] if chunk.startswith("noncomputable") and len(parts) > 2
                          else (parts[1] if len(parts) > 1 and head[0] == "section" else "")))
            continue
        if head[0] == "end":
            if stack:
                stack.pop()
            continue
        m = _DECL_RE.match(chunk)
        if not m:
            continue
        kind = m.group(1)
        after = chunk[m.end():]
        nm = _NAME_RE.match(after)
        name, sig = "", m.end()
        if kind != "example" and nm and nm.group(1) not in (":=",) and not nm.group(1).startswith(("(", "[", "{")):
            name = nm.group(1)
            sig = m.end() + nm.end()
            if kind == "instance" and (name.startswith(":") or name in ("where",)):
                name, sig = "", m.end()
        ns = tuple(n for k, n in stack if k == "ns")
        if name.startswith("_root_."):
            qual = name[len("_root_."):]
        else:
            qual = ".".join(p for p in (".".join(ns), name) if p) if name else ""
        decls.append(Decl(kind, name, qual, chunk.rstrip(), code.count("\n", 0, a) + 1 + chunk[:m.start(1)].count("\n"), ns, sig))
    return decls


def theorem_map(src: str) -> dict[str, Decl]:
    """Qualified name -> theorem/lemma declaration (last one wins, as in Lean errors)."""
    return {d.qualname: d for d in declarations(src) if d.kind in ("theorem", "lemma") and d.qualname}
