# -*- coding: utf-8 -*-
import re
import sys
from pathlib import Path

OPERATORS = {"AND", "OR", "NOT"}
TERM_RE = re.compile(r"[A-Za-zА-Яа-яЁё-]+")


def _doc_id_from_lemma_file(path: Path) -> str:
    stem = path.stem
    if stem.endswith("_lemmas"):
        stem = stem[: -len("_lemmas")]
    return f"{stem}.html"


def _parse_lemmas_file(path: Path) -> set[str]:
    """Читает файл лемм, возвращает множество лемм документа (первое слово в каждой строке)."""
    lemmas: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.strip().split()
        if not parts:
            continue
        lemmas.add(parts[0].lower())
    return lemmas


def _build_inverted_index_from_lemmas(lemmas_dir: Path) -> tuple[dict[str, set[str]], set[str]]:
    """Строит инвертированный индекс по леммам: лемма -> множество id документов."""
    lemma_files = sorted(lemmas_dir.glob("*_lemmas.txt"))
    if not lemma_files:
        raise ValueError(f"no lemma files in {lemmas_dir}")

    index: dict[str, set[str]] = {}
    all_docs: set[str] = set()

    for lemma_file in lemma_files:
        if not lemma_file.is_file():
            continue
        doc_id = _doc_id_from_lemma_file(lemma_file)
        all_docs.add(doc_id)
        for lemma in _parse_lemmas_file(lemma_file):
            index.setdefault(lemma, set()).add(doc_id)

    return index, all_docs


def _write_inverted_index(path: Path, index: dict[str, set[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    for term in sorted(index):
        docs = sorted(index[term])
        lines.append(f"{term}\t{' '.join(docs)}")
    content = "\n".join(lines)
    if content:
        content += "\n"
    path.write_text(content, encoding="utf-8")


def build_index(lemmas_dir: Path, out_path: Path) -> int:
    """Строит инвертированный индекс по леммам и записывает в out_path."""
    if not lemmas_dir.exists():
        print(f"build-index: lemmas directory not found: {lemmas_dir}", file=sys.stderr)
        return 1
    if not lemmas_dir.is_dir():
        print(f"build-index: lemmas path is not a directory: {lemmas_dir}", file=sys.stderr)
        return 1

    try:
        index, _all_docs = _build_inverted_index_from_lemmas(lemmas_dir)
    except ValueError as e:
        print(f"build-index: {e}", file=sys.stderr)
        return 1

    _write_inverted_index(out_path, index)
    return 0


def _read_inverted_index(path: Path) -> tuple[dict[str, set[str]], set[str]]:
    if not path.exists():
        raise ValueError(f"index file not found: {path}")
    if not path.is_file():
        raise ValueError(f"index path is not a file: {path}")

    index: dict[str, set[str]] = {}
    all_docs: set[str] = set()

    for line_no, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        if "\t" not in line:
            raise ValueError(f"invalid index format at line {line_no}: expected 'term<TAB>docs'")
        term, docs_part = line.split("\t", 1)
        term = term.strip().lower()
        if not term:
            raise ValueError(f"invalid index format at line {line_no}: empty term")
        docs = {doc for doc in docs_part.split() if doc}
        index[term] = docs
        all_docs.update(docs)

    return index, all_docs


def _tokenize_query(query: str) -> list[tuple[str, str]]:
    tokens: list[tuple[str, str]] = []
    i = 0

    while i < len(query):
        ch = query[i]
        if ch.isspace():
            i += 1
            continue
        if ch == "(":
            tokens.append(("LPAREN", ch))
            i += 1
            continue
        if ch == ")":
            tokens.append(("RPAREN", ch))
            i += 1
            continue

        match = TERM_RE.match(query, i)
        if not match:
            raise ValueError(f"invalid character in query at position {i + 1}: '{ch}'")

        word = match.group(0)
        upper = word.upper()
        if upper in OPERATORS:
            tokens.append((upper, upper))
        else:
            tokens.append(("TERM", word.lower()))
        i = match.end()

    if not tokens:
        raise ValueError("empty query")
    return tokens


class _BooleanQueryParser:
    def __init__(
        self,
        tokens: list[tuple[str, str]],
        index: dict[str, set[str]],
        all_docs: set[str],
    ) -> None:
        self.tokens = tokens
        self.index = index
        self.all_docs = all_docs
        self.pos = 0

    def _peek(self) -> tuple[str, str] | None:
        if self.pos >= len(self.tokens):
            return None
        return self.tokens[self.pos]

    def _accept(self, expected_kind: str) -> tuple[str, str] | None:
        token = self._peek()
        if token is not None and token[0] == expected_kind:
            self.pos += 1
            return token
        return None

    def _expect(self, expected_kind: str) -> tuple[str, str]:
        token = self._accept(expected_kind)
        if token is None:
            raise ValueError(f"expected {expected_kind}")
        return token

    def parse(self) -> set[str]:
        result = self._parse_or()
        if self._peek() is not None:
            raise ValueError("unexpected tail in query")
        return result

    def _parse_or(self) -> set[str]:
        result = self._parse_and()
        while self._accept("OR") is not None:
            result = result | self._parse_and()
        return result

    def _parse_and(self) -> set[str]:
        result = self._parse_not()
        while self._accept("AND") is not None:
            result = result & self._parse_not()
        return result

    def _parse_not(self) -> set[str]:
        if self._accept("NOT") is not None:
            return self.all_docs - self._parse_not()
        return self._parse_primary()

    def _parse_primary(self) -> set[str]:
        term = self._accept("TERM")
        if term is not None:
            # Индекс по леммам: ищем термин как есть (пользователь вводит лемму)
            return set(self.index.get(term[1].lower(), set()))

        if self._accept("LPAREN") is not None:
            expr = self._parse_or()
            self._expect("RPAREN")
            return expr

        raise ValueError("expected TERM, NOT or '('")


def search(index_path: Path, query: str | None = None) -> int:
    try:
        index, all_docs = _read_inverted_index(index_path)
    except ValueError as e:
        print(f"search: {e}", file=sys.stderr)
        return 1

    if query is None:
        try:
            query = input("Введите булев запрос: ").strip()
        except EOFError:
            query = ""

    try:
        tokens = _tokenize_query(query)
        parser = _BooleanQueryParser(tokens=tokens, index=index, all_docs=all_docs)
        docs = sorted(parser.parse())
    except ValueError as e:
        print(f"search: invalid query: {e}", file=sys.stderr)
        return 1

    for doc in docs:
        print(doc)
    return 0
