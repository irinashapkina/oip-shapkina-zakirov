import math
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable, Mapping


def load_document_tokens(tokens_path: Path) -> list[str]:
    """
    Загружает токены документа из файла задания 2.

    Формат: один токен в строке. Кодировка: UTF-8.
    """
    terms: list[str] = []
    for line in tokens_path.read_text(encoding="utf-8").splitlines():
        token = line.strip().lower()
        if token:
            terms.append(token)
    return terms


def iter_token_files(tokens_dir: Path) -> list[Path]:
    """Возвращает список per-document файлов токенов (*_tokens.txt) в стабильном порядке."""
    return sorted(path for path in tokens_dir.glob("*_tokens.txt") if path.is_file())


def compute_df(token_files: Iterable[Path]) -> tuple[dict[str, int], int]:
    """
    Считает DF(term) по корпусу.

    DF(term) — количество документов, где термин встречается хотя бы один раз.
    N — количество документов в корпусе (количество token-файлов).
    """
    df: dict[str, int] = {}
    n_docs = 0

    for path in token_files:
        n_docs += 1
        terms_in_doc = set(load_document_tokens(path))
        for term in terms_in_doc:
            df[term] = df.get(term, 0) + 1

    return df, n_docs


def compute_tf(tokens: list[str]) -> dict[str, float]:
    """
    TF(term) для одного документа.

    TF(term) = count(term) / total_terms_in_doc.
    """
    total = len(tokens)
    if total == 0:
        return {}
    counts = Counter(tokens)
    return {term: count / total for term, count in counts.items()}


def idf(term: str, df: Mapping[str, int], n_docs: int, *, smooth: bool = True) -> float:
    """
    IDF(term) по всему корпусу.

    По умолчанию сглаживание:
        log((N + 1) / (df + 1)) + 1
    """
    if n_docs <= 0:
        return 0.0
    dft = df.get(term, 0)
    if smooth:
        return math.log((n_docs + 1) / (dft + 1)) + 1.0
    if dft <= 0:
        return 0.0
    return math.log(n_docs / dft)


def compute_idf(df: Mapping[str, int], n_docs: int, *, smooth: bool = True) -> dict[str, float]:
    """Считает IDF для всех терминов, которые есть в df."""
    return {term: idf(term, df=df, n_docs=n_docs, smooth=smooth) for term in df}


def compute_tf_idf_for_document(
    tokens: list[str],
    *,
    df: Mapping[str, int],
    n_docs: int,
    smooth_idf: bool = True,
) -> tuple[dict[str, float], dict[str, float], dict[str, float]]:
    """
    Считает TF, IDF и TF-IDF для одного документа.

    Возвращает (tf_map, idf_map_for_doc_terms, tfidf_map).
    """
    tf_map = compute_tf(tokens)
    if not tf_map:
        return {}, {}, {}

    idf_map: dict[str, float] = {}
    tfidf_map: dict[str, float] = {}
    for term, tf_value in tf_map.items():
        idf_value = idf(term, df=df, n_docs=n_docs, smooth=smooth_idf)
        idf_map[term] = idf_value
        tfidf_map[term] = tf_value * idf_value

    return tf_map, idf_map, tfidf_map


def load_document_lemmas(lemmas_path: Path) -> dict[str, list[str]]:
    """
    Загружает леммы документа из файла задания 2.
    """
    lemma_groups: dict[str, list[str]] = {}
    for line in lemmas_path.read_text(encoding="utf-8").splitlines():
        parts = line.strip().split()
        if not parts:
            continue
        lemma = parts[0].lower()
        tokens = {token.lower() for token in parts[1:] if token}
        lemma_groups[lemma] = sorted(tokens)
    return lemma_groups


def iter_lemma_files(lemmas_dir: Path) -> list[Path]:
    """Возвращает список per-document файлов лемм (*_lemmas.txt) в стабильном порядке."""
    return sorted(path for path in lemmas_dir.glob("*_lemmas.txt") if path.is_file())


def compute_lemma_df(lemma_files: Iterable[Path]) -> tuple[dict[str, int], int]:
    """
    Считает DF(lemma) по корпусу.

    DF(lemma) — количество документов, где lemma_count > 0.
    N — количество документов в корпусе (количество файлов лемм).
    """
    df: dict[str, int] = {}
    n_docs = 0

    for path in lemma_files:
        n_docs += 1
        lemma_groups = load_document_lemmas(path)
        for lemma in lemma_groups:
            df[lemma] = df.get(lemma, 0) + 1

    return df, n_docs


def compute_lemma_tf_for_document(
    tokens: list[str],
    lemma_groups: Mapping[str, Iterable[str]],
) -> dict[str, float]:
    """
    Считает TF для лемм одного документа.

    lemma_count = сумма вхождений всех токенов леммы в документе;
    total_terms = общее число терминов (размер списка tokens с повторами);
    TF(lemma) = lemma_count / total_terms.
    """
    total = len(tokens)
    if total == 0 or not lemma_groups:
        return {}

    counts = Counter(tokens)
    tf_lemma: dict[str, float] = {}
    for lemma, lemma_tokens in lemma_groups.items():
        lemma_count = 0
        for token in lemma_tokens:
            lemma_count += counts.get(token, 0)
        if lemma_count > 0:
            tf_lemma[lemma] = lemma_count / total

    return tf_lemma


def compute_lemma_tf_idf_for_document(
    tokens: list[str],
    lemma_groups: Mapping[str, Iterable[str]],
    *,
    df_lemma: Mapping[str, int],
    n_docs: int,
    smooth_idf: bool = True,
) -> tuple[dict[str, float], dict[str, float], dict[str, float]]:
    """
    Считает TF, IDF и TF-IDF для лемм одного документа.

    Возвращает (tf_lemma_map, idf_lemma_map_for_doc_lemmas, tfidf_lemma_map).
    """
    tf_lemma = compute_lemma_tf_for_document(tokens, lemma_groups)
    if not tf_lemma:
        return {}, {}, {}

    idf_lemma: dict[str, float] = {}
    tfidf_lemma: dict[str, float] = {}
    for lemma, tf_value in tf_lemma.items():
        idf_value = idf(lemma, df=df_lemma, n_docs=n_docs, smooth=smooth_idf)
        idf_lemma[lemma] = idf_value
        tfidf_lemma[lemma] = tf_value * idf_value

    return tf_lemma, idf_lemma, tfidf_lemma


def demo_tfidf(tokens_dir: Path, doc_tokens: Path | None = None, top_k: int = 10) -> int:
    """
    Демо-функция: строит df/idf по каталогу токенов и печатает top-K TF-IDF для одного документа.

   Только вычисления и вывод в stdout/stderr.
    """
    if not tokens_dir.exists():
        print(f"demo-tfidf: tokens directory not found: {tokens_dir}", file=sys.stderr)
        return 1
    if not tokens_dir.is_dir():
        print(f"demo-tfidf: tokens path is not a directory: {tokens_dir}", file=sys.stderr)
        return 1

    token_files = iter_token_files(tokens_dir)
    if not token_files:
        print(f"demo-tfidf: no token files in {tokens_dir}", file=sys.stderr)
        return 1

    df, n_docs = compute_df(token_files)

    if doc_tokens is None:
        doc_tokens = token_files[0]
    if not doc_tokens.exists() or not doc_tokens.is_file():
        print(f"demo-tfidf: document tokens file not found: {doc_tokens}", file=sys.stderr)
        return 1

    tokens = load_document_tokens(doc_tokens)
    _tf, _idf, tfidf = compute_tf_idf_for_document(tokens, df=df, n_docs=n_docs, smooth_idf=True)

    ranked = sorted(tfidf.items(), key=lambda kv: (-kv[1], kv[0]))
    print(f"Document: {doc_tokens.name}")
    print(f"N={n_docs}, unique_terms_in_doc={len(set(tokens))}, total_terms_in_doc={len(tokens)}")
    print("Top TF-IDF terms:")
    for term, score in ranked[: max(0, top_k)]:
        print(f"{term}\t{score:.6f}")

    return 0

