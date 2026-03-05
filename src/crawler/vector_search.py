import json
import math
import sys
from collections import Counter
from pathlib import Path

from .text_processing import TOKEN_RE, _collect_unique_tokens, _group_by_lemmas

DEFAULT_TFIDF_DIR = Path("output/tfidf")
DEFAULT_VECTOR_INDEX_DIR = Path("output/vector_index")
VECTOR_INDEX_FILENAME = "vector_index.json"


# JSON schema (output/vector_index/vector_index.json):
# {
#   "format": "vector-index-v1",
#   "source_tfidf_dir": "output/tfidf",
#   "doc_vectors": {"0001": {"term": 0.123, ...}, ...},
#   "doc_norms": {"0001": 1.234, ...},
#   "idf_map": {"term": 2.345, ...}
# }


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


def _norm_sparse(vector: dict[str, float]) -> float:
    return math.sqrt(sum(weight * weight for weight in vector.values()))


def _vector_index_path(index_dir: Path) -> Path:
    return index_dir / VECTOR_INDEX_FILENAME


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


def build_query_vector(
    text: str,
    tfidf_dir: Path = DEFAULT_TFIDF_DIR,
    idf_map: dict[str, float] | None = None,
) -> dict[str, float]:
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

    effective_idf_map = idf_map if idf_map is not None else _load_idf_map(tfidf_dir)
    if not effective_idf_map:
        raise ValueError(f"no TF-IDF corpus data found in: {tfidf_dir}")

    total = len(query_lemmas)
    counts = Counter(query_lemmas)

    vector: dict[str, float] = {}
    for term, count in counts.items():
        idf_value = effective_idf_map.get(term)
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


def build_vector_index(
    tfidf_dir: Path = DEFAULT_TFIDF_DIR,
    index_dir: Path = DEFAULT_VECTOR_INDEX_DIR,
) -> dict[str, dict[str, dict[str, float]] | dict[str, float] | str]:
    """
    Строит и сохраняет векторный индекс по существующим TF-IDF файлам лемм.
    """
    tfidf_files = _iter_tfidf_files(tfidf_dir)
    if not tfidf_files:
        raise ValueError(f"no TF-IDF lemma files found in: {tfidf_dir}")

    doc_vectors: dict[str, dict[str, float]] = {}
    doc_norms: dict[str, float] = {}
    idf_map = _load_idf_map(tfidf_dir)
    if not idf_map:
        raise ValueError(f"failed to load idf map from TF-IDF files in: {tfidf_dir}")

    for tfidf_file in tfidf_files:
        doc_id = _doc_id_from_tfidf_file(tfidf_file)
        vector = load_doc_vector(doc_id, tfidf_dir=tfidf_dir)
        doc_vectors[doc_id] = vector
        doc_norms[doc_id] = _norm_sparse(vector)

    index_payload: dict[str, dict[str, dict[str, float]] | dict[str, float] | str] = {
        "format": "vector-index-v1",
        "source_tfidf_dir": str(tfidf_dir),
        "doc_vectors": doc_vectors,
        "doc_norms": doc_norms,
        "idf_map": idf_map,
    }

    index_dir.mkdir(parents=True, exist_ok=True)
    index_path = _vector_index_path(index_dir)
    index_path.write_text(
        json.dumps(index_payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    return index_payload


def load_vector_index(
    index_dir: Path = DEFAULT_VECTOR_INDEX_DIR,
) -> dict[str, dict[str, dict[str, float]] | dict[str, float] | str]:
    """
    Загружает сериализованный индекс из JSON.
    """
    index_path = _vector_index_path(index_dir)
    if not index_path.exists() or not index_path.is_file():
        raise FileNotFoundError(f"vector index file not found: {index_path}")

    payload = json.loads(index_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("invalid vector index format: expected top-level JSON object")
    if payload.get("format") != "vector-index-v1":
        raise ValueError("invalid vector index format version")

    doc_vectors = payload.get("doc_vectors")
    doc_norms = payload.get("doc_norms")
    idf_map = payload.get("idf_map")
    if not isinstance(doc_vectors, dict) or not isinstance(doc_norms, dict) or not isinstance(idf_map, dict):
        raise ValueError("invalid vector index payload: doc_vectors/doc_norms/idf_map are required")

    cast_doc_vectors: dict[str, dict[str, float]] = {}
    for doc_id, vector in doc_vectors.items():
        if not isinstance(doc_id, str) or not isinstance(vector, dict):
            continue
        cast_vector: dict[str, float] = {}
        for term, weight in vector.items():
            if isinstance(term, str) and isinstance(weight, (int, float)):
                cast_vector[term] = float(weight)
        cast_doc_vectors[doc_id] = cast_vector

    cast_doc_norms: dict[str, float] = {}
    for doc_id, norm in doc_norms.items():
        if isinstance(doc_id, str) and isinstance(norm, (int, float)):
            cast_doc_norms[doc_id] = float(norm)

    cast_idf_map: dict[str, float] = {}
    for term, idf_value in idf_map.items():
        if isinstance(term, str) and isinstance(idf_value, (int, float)):
            cast_idf_map[term] = float(idf_value)

    return {
        "format": "vector-index-v1",
        "source_tfidf_dir": str(payload.get("source_tfidf_dir", "")),
        "doc_vectors": cast_doc_vectors,
        "doc_norms": cast_doc_norms,
        "idf_map": cast_idf_map,
    }


def _cosine_similarity_with_doc_norm(
    query_vector: dict[str, float],
    query_norm: float,
    doc_vector: dict[str, float],
    doc_norm: float,
) -> float:
    if query_norm == 0.0 or doc_norm == 0.0 or not query_vector or not doc_vector:
        return 0.0

    if len(query_vector) <= len(doc_vector):
        smaller, larger = query_vector, doc_vector
    else:
        smaller, larger = doc_vector, query_vector

    dot = 0.0
    for term, weight in smaller.items():
        dot += weight * larger.get(term, 0.0)
    return dot / (query_norm * doc_norm)


def search(
    query: str,
    top_k: int,
    tfidf_dir: Path = DEFAULT_TFIDF_DIR,
    index_dir: Path = DEFAULT_VECTOR_INDEX_DIR,
) -> list[tuple[str, float]]:
    """
    Возвращает top_k документов как список (doc_id, score),
    отсортированный по убыванию cosine similarity.
    """
    if top_k <= 0:
        return []

    loaded_index: dict[str, dict[str, dict[str, float]] | dict[str, float] | str] | None = None
    try:
        loaded_index = load_vector_index(index_dir=index_dir)
    except (FileNotFoundError, ValueError):
        loaded_index = None

    try:
        if loaded_index is not None:
            idf_map = loaded_index["idf_map"]
            if not isinstance(idf_map, dict):
                raise ValueError("invalid vector index: idf_map")
            query_vector = build_query_vector(query, tfidf_dir=tfidf_dir, idf_map=idf_map)
        else:
            query_vector = build_query_vector(query, tfidf_dir=tfidf_dir)
    except ValueError as exc:
        print(f"vector-search: {exc}", file=sys.stderr)
        return []

    candidates: list[tuple[str, float]] = []
    if loaded_index is not None:
        doc_vectors = loaded_index["doc_vectors"]
        doc_norms = loaded_index["doc_norms"]
        if not isinstance(doc_vectors, dict) or not isinstance(doc_norms, dict):
            print("vector-search: invalid vector index payload", file=sys.stderr)
            return []

        query_norm = _norm_sparse(query_vector)
        for doc_id, doc_vector in doc_vectors.items():
            if not isinstance(doc_id, str) or not isinstance(doc_vector, dict):
                continue
            doc_norm = float(doc_norms.get(doc_id, 0.0))
            score = _cosine_similarity_with_doc_norm(query_vector, query_norm, doc_vector, doc_norm)
            if score > 0.0:
                candidates.append((doc_id, score))
    else:
        for tfidf_file in _iter_tfidf_files(tfidf_dir):
            doc_id = _doc_id_from_tfidf_file(tfidf_file)
            doc_vector = load_doc_vector(doc_id, tfidf_dir=tfidf_dir)
            score = cosine_similarity_sparse(doc_vector, query_vector)
            if score > 0.0:
                candidates.append((doc_id, score))

    candidates.sort(key=lambda item: (-item[1], item[0]))
    return candidates[:top_k]
