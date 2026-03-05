import sys
from collections import Counter
from pathlib import Path

from .text_processing import TOKEN_RE, _collect_unique_tokens, _group_by_lemmas

DEFAULT_TFIDF_DIR = Path("output/tfidf")


def _normalize_doc_id(doc_id: str) -> str:
    normalized = doc_id.strip()
    if normalized.endswith(".html"):
        normalized = normalized[: -len(".html")]
    return normalized


def _iter_tfidf_files(tfidf_dir: Path) -> list[Path]:
    return sorted(path for path in tfidf_dir.glob("tfidf_lemmas_*.txt") if path.is_file())


def _doc_id_from_tfidf_file(path: Path) -> str:
    stem = path.stem
    prefix = "tfidf_lemmas_"
    if stem.startswith(prefix):
        return stem[len(prefix) :]
    return stem


def _load_idf_map(tfidf_dir: Path = DEFAULT_TFIDF_DIR) -> dict[str, float]:
    idf_map: dict[str, float] = {}
    for tfidf_file in _iter_tfidf_files(tfidf_dir):
        for line in tfidf_file.read_text(encoding="utf-8").splitlines():
            parts = line.strip().split()
            if len(parts) != 3:
                continue
            term = parts[0].lower()
            if term in idf_map:
                continue
            try:
                idf_map[term] = float(parts[1])
            except ValueError:
                continue
    return idf_map


def _tokenize_query_terms(text: str) -> list[str]:
    raw_tokens = TOKEN_RE.findall(text.lower())
    query_terms: list[str] = []
    for raw in raw_tokens:
        accepted = _collect_unique_tokens([raw])
        if accepted:
            query_terms.append(accepted[0])
    return query_terms


def _lemmatize_terms(terms: list[str]) -> list[str]:
    unique_terms = sorted(set(terms))
    try:
        lemma_groups = _group_by_lemmas(unique_terms)
    except RuntimeError as exc:
        raise ValueError(str(exc)) from exc
    token_to_lemma: dict[str, str] = {}
    for lemma, tokens in lemma_groups.items():
        for token in tokens:
            token_to_lemma[token] = lemma
    return [token_to_lemma.get(term, term) for term in terms]


def load_doc_vector(doc_id: str, tfidf_dir: Path = DEFAULT_TFIDF_DIR) -> dict[str, float]:
    """
    Загружает разреженный вектор документа из существующего файла TF-IDF лемм.
    Возвращает dict: term -> tf-idf weight.
    """
    normalized_doc_id = _normalize_doc_id(doc_id)
    path = tfidf_dir / f"tfidf_lemmas_{normalized_doc_id}.txt"
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"TF-IDF file not found for doc_id='{doc_id}': {path}")

    vector: dict[str, float] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.strip().split()
        if len(parts) != 3:
            continue
        term = parts[0].lower()
        try:
            weight = float(parts[2])
        except ValueError:
            continue
        vector[term] = weight
    return vector


def build_query_vector(text: str, tfidf_dir: Path = DEFAULT_TFIDF_DIR) -> dict[str, float]:
    """
    Строит TF-IDF вектор запроса в пространстве лемм корпуса.
    TF(query_term) = count(term) / len(terms_in_query).
    IDF(term) берётся из уже построенных TF-IDF файлов корпуса.
    """
    if not text or not text.strip():
        raise ValueError("query is empty")

    query_terms = _tokenize_query_terms(text)
    if not query_terms:
        raise ValueError("query is empty after tokenization/filtering")

    query_lemmas = _lemmatize_terms(query_terms)
    if not query_lemmas:
        raise ValueError("query is empty after lemmatization")

    idf_map = _load_idf_map(tfidf_dir)
    if not idf_map:
        raise ValueError(f"no TF-IDF corpus data found in: {tfidf_dir}")

    total = len(query_lemmas)
    counts = Counter(query_lemmas)

    vector: dict[str, float] = {}
    for term, count in counts.items():
        idf_value = idf_map.get(term)
        if idf_value is None:
            continue
        tf_query = count / total
        vector[term] = tf_query * idf_value

    if not vector:
        raise ValueError("all query terms are absent in corpus vocabulary")
    return vector


def cosine_similarity_sparse(vec_a: dict[str, float], vec_b: dict[str, float]) -> float:
    """Косинусная близость двух разреженных векторов."""
    if not vec_a or not vec_b:
        return 0.0

    if len(vec_a) <= len(vec_b):
        smaller, larger = vec_a, vec_b
    else:
        smaller, larger = vec_b, vec_a

    dot = 0.0
    for term, weight in smaller.items():
        dot += weight * larger.get(term, 0.0)

    norm_a = sum(weight * weight for weight in vec_a.values()) ** 0.5
    norm_b = sum(weight * weight for weight in vec_b.values()) ** 0.5
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot / (norm_a * norm_b)


def search(query: str, top_k: int, tfidf_dir: Path = DEFAULT_TFIDF_DIR) -> list[tuple[str, float]]:
    """
    Возвращает top_k документов как список (doc_id, score),
    отсортированный по убыванию cosine similarity.
    """
    if top_k <= 0:
        return []

    try:
        query_vector = build_query_vector(query, tfidf_dir=tfidf_dir)
    except ValueError as exc:
        print(f"vector-search: {exc}", file=sys.stderr)
        return []

    candidates: list[tuple[str, float]] = []
    for tfidf_file in _iter_tfidf_files(tfidf_dir):
        doc_id = _doc_id_from_tfidf_file(tfidf_file)
        doc_vector = load_doc_vector(doc_id, tfidf_dir=tfidf_dir)
        score = cosine_similarity_sparse(doc_vector, query_vector)
        if score > 0.0:
            candidates.append((doc_id, score))

    candidates.sort(key=lambda item: (-item[1], item[0]))
    return candidates[:top_k]
