import argparse
import sys
from pathlib import Path

from .run import run as run_crawler
from .validate import validate as validate_crawler
from .package import package as package_crawler
from .text_processing import analyze as analyze_text
from .boolean_search import build_index as build_inverted_index
from .boolean_search import search as search_inverted_index
from .tfidf import build_tfidf_for_corpus as build_tfidf_corpus
from .vector_search import build_vector_index as build_vector_search_index
from .vector_search import load_vector_index as load_vector_search_index
from .vector_search import search_in_loaded_index as search_in_vector_index


def _cmd_run(args: argparse.Namespace) -> int:
    """Подкоманда run: запуск краулера по URL из файла с сохранением в out_dir и индексом."""
    return run_crawler(
        input_path=Path(args.input),
        out_dir=Path(args.out),
        index_path=Path(args.index),
        limit=args.limit,
    )


def _cmd_validate(args: argparse.Namespace) -> int:
    """Подкоманда validate: проверка индекса и каталога страниц."""
    return validate_crawler(
        pages_dir=Path(args.pages),
        index_path=Path(args.index),
        min_pages=args.min_pages,
    )


def _cmd_package(args: argparse.Namespace) -> int:
    """Подкоманда package: упаковка pages и index в submission.zip."""
    return package_crawler(
        pages_dir=Path(args.pages),
        index_path=Path(args.index),
        out_zip=Path(args.out),
    )


def _cmd_analyze(args: argparse.Namespace) -> int:
    """Подкоманда analyze: токенизация и группировка токенов по леммам."""
    return analyze_text(
        pages_dir=Path(args.pages),
        tokens_dir=Path(args.tokens),
        lemmas_dir=Path(args.lemmas),
    )


def _cmd_build_index(args: argparse.Namespace) -> int:
    """Подкоманда build-index: построение инвертированного индекса по леммам."""
    return build_inverted_index(
        lemmas_dir=Path(args.lemmas),
        out_path=Path(args.out),
    )


def _cmd_search(args: argparse.Namespace) -> int:
    """Подкоманда search: булев поиск (AND/OR/NOT, скобки) по индексу."""
    return search_inverted_index(
        index_path=Path(args.index),
        query=args.query,
    )


def _cmd_tfidf(args: argparse.Namespace) -> int:
    """Подкоманда tfidf: расчёт TF/IDF/TF-IDF по корпусу и генерация per-document файлов."""
    tokens_dir = Path(args.tokens)
    lemmas_dir = Path(args.lemmas)
    out_dir = Path(args.out)

    print(f"tfidf: tokens_dir = {tokens_dir}")
    print(f"tfidf: lemmas_dir = {lemmas_dir}")
    print(f"tfidf: out_dir    = {out_dir}")

    return build_tfidf_corpus(
        tokens_dir=tokens_dir,
        lemmas_dir=lemmas_dir,
        out_dir=out_dir,
    )


def _cmd_build_vector_index(args: argparse.Namespace) -> int:
    """Подкоманда build-vector-index: построение и сохранение векторного индекса по TF-IDF."""
    tfidf_dir = Path(args.tfidf)
    out_dir = Path(args.out)

    print(f"build-vector-index: tfidf_dir = {tfidf_dir}")
    print(f"build-vector-index: out_dir   = {out_dir}")
    try:
        payload = build_vector_search_index(tfidf_dir=tfidf_dir, index_dir=out_dir)
    except ValueError as e:
        print(f"build-vector-index: {e}", file=sys.stderr)
        return 1

    doc_vectors = payload.get("doc_vectors", {})
    idf_map = payload.get("idf_map", {})
    print(f"build-vector-index: indexed documents = {len(doc_vectors) if isinstance(doc_vectors, dict) else 0}")
    print(f"build-vector-index: vocabulary size = {len(idf_map) if isinstance(idf_map, dict) else 0}")
    print(f"build-vector-index: index file = {out_dir / 'vector_index.json'}")
    return 0


def _read_url_index(index_path: Path) -> dict[str, str]:
    """
    Читает index.txt формата: filename<TAB>url и возвращает doc_id -> url.
    Поддерживает ключи и с .html, и без него.
    """
    if not index_path.exists() or not index_path.is_file():
        raise ValueError(f"index file not found: {index_path}")

    url_map: dict[str, str] = {}
    for line_no, raw_line in enumerate(index_path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        if "\t" not in line:
            raise ValueError(f"invalid index format at line {line_no}: expected 'filename<TAB>url'")
        filename, url = line.split("\t", 1)
        filename = filename.strip()
        url = url.strip()
        if not filename:
            raise ValueError(f"invalid index format at line {line_no}: empty filename")
        doc_id = filename
        if doc_id.endswith(".html"):
            bare_id = doc_id[: -len(".html")]
        else:
            bare_id = doc_id
            doc_id = f"{doc_id}.html"
        url_map[doc_id] = url
        url_map[bare_id] = url
    return url_map


def _cmd_vector_index(args: argparse.Namespace) -> int:
    """Подкоманда vector-index: построение и сохранение векторного индекса по TF-IDF."""
    tfidf_dir = Path(args.tfidf)
    out_dir = Path(args.out)

    print(f"vector-index: tfidf_dir = {tfidf_dir}")
    print(f"vector-index: out_dir   = {out_dir}")
    try:
        payload = build_vector_search_index(tfidf_dir=tfidf_dir, index_dir=out_dir)
    except ValueError as e:
        print(f"vector-index: {e}", file=sys.stderr)
        return 1

    doc_vectors = payload.get("doc_vectors", {})
    idf_map = payload.get("idf_map", {})
    print(f"vector-index: indexed documents = {len(doc_vectors) if isinstance(doc_vectors, dict) else 0}")
    print(f"vector-index: vocabulary size = {len(idf_map) if isinstance(idf_map, dict) else 0}")
    print(f"vector-index: index file = {out_dir / 'vector_index.json'}")
    return 0


def _cmd_vector_search(args: argparse.Namespace) -> int:
    """Подкоманда vector-search: поиск по сохранённому векторному индексу."""
    index_dir = Path(args.vector_index)
    corpus_index_path = Path(args.index)
    query = args.query
    top_k = args.top

    try:
        vector_index = load_vector_search_index(index_dir=index_dir)
    except FileNotFoundError:
        print(
            f"vector-search: vector index not found in {index_dir}; run `vector-index` first",
            file=sys.stderr,
        )
        return 1
    except ValueError as e:
        print(f"vector-search: {e}", file=sys.stderr)
        return 1

    try:
        results = search_in_vector_index(query=query, top_k=top_k, vector_index=vector_index)
    except ValueError as e:
        print(f"vector-search: {e}", file=sys.stderr)
        return 1

    try:
        url_map = _read_url_index(corpus_index_path)
    except ValueError as e:
        print(f"vector-search: {e}", file=sys.stderr)
        return 1

    for doc_id, score in results:
        url = url_map.get(doc_id, "")
        print(f"{doc_id} {score:.6f} {url}")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    """Собирает парсер с подкомандами run, validate, package, analyze, build-index, search, tfidf, build-vector-index, vector-index, vector-search."""
    parser = argparse.ArgumentParser(
        prog="crawler",
        description="CLI для краулера.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help="доступные команды")

    run_parser = subparsers.add_parser("run", help="запустить краулер")
    run_parser.add_argument("--input", required=True, help="файл с URL (по одному на строку)")
    run_parser.add_argument("--out", required=True, help="каталог для сохранения страниц (0001.html, …)")
    run_parser.add_argument("--index", required=True, help="файл индекса (filename<TAB>url)")
    run_parser.add_argument("--limit", type=int, default=100, help="нужное число успешных скачиваний (по умолчанию: 100)")
    validate_parser = subparsers.add_parser("validate", help="проверить индекс и страницы")
    validate_parser.add_argument("--pages", required=True, help="каталог со страницами (0001.html, …)")
    validate_parser.add_argument("--index", required=True, help="файл индекса (filename<TAB>url)")
    validate_parser.add_argument("--min-pages", type=int, default=100, help="минимальное число файлов в каталоге (по умолчанию: 100)")
    package_parser = subparsers.add_parser("package", help="упаковать страницы и индекс в ZIP")
    package_parser.add_argument("--pages", required=True, help="каталог со страницами (0001.html, …)")
    package_parser.add_argument("--index", required=True, help="файл индекса (filename<TAB>url)")
    package_parser.add_argument("--out", required=True, help="путь к создаваемому ZIP (submission.zip)")
    analyze_parser = subparsers.add_parser("analyze", help="получить токены и леммы из сохраненных HTML")
    analyze_parser.add_argument("--pages", required=True, help="каталог со страницами (0001.html, …)")
    analyze_parser.add_argument(
        "--tokens",
        required=True,
        help="каталог для токенов по страницам (файлы вида 0001_tokens.txt)",
    )
    analyze_parser.add_argument(
        "--lemmas",
        required=True,
        help="каталог для лемм по страницам (файлы вида 0001_lemmas.txt)",
    )
    build_index_parser = subparsers.add_parser("build-index", help="построить инвертированный индекс по леммам")
    build_index_parser.add_argument(
        "--lemmas",
        required=True,
        help="каталог лемм по страницам (файлы вида 0001_lemmas.txt)",
    )
    build_index_parser.add_argument(
        "--out",
        required=True,
        help="выходной TXT с инвертированным индексом (лемма -> документы)",
    )
    search_parser = subparsers.add_parser("search", help="выполнить булев поиск по инвертированному индексу")
    search_parser.add_argument("--index", required=True, help="файл инвертированного индекса")
    search_parser.add_argument(
        "--query",
        required=False,
        help="строка булева запроса; если не передан, будет интерактивный ввод",
    )

    tfidf_parser = subparsers.add_parser(
        "tfidf",
        help="подсчитать TF/IDF/TF-IDF по корпусу и сохранить per-document файлы",
    )
    tfidf_parser.add_argument(
        "--tokens",
        default="output/tokens",
        help="каталог токенов по страницам (файлы вида 0001_tokens.txt, по умолчанию: output/tokens)",
    )
    tfidf_parser.add_argument(
        "--lemmas",
        default="output/lemmas",
        help="каталог лемм по страницам (файлы вида 0001_lemmas.txt, по умолчанию: output/lemmas)",
    )
    tfidf_parser.add_argument(
        "--out",
        default="output/tfidf",
        help="каталог для TF-IDF файлов (tfidf_terms_<id>.txt, tfidf_lemmas_<id>.txt, по умолчанию: output/tfidf)",
    )

    vector_index_parser = subparsers.add_parser(
        "build-vector-index",
        help="построить и сохранить векторный индекс по готовым TF-IDF файлам",
    )
    vector_index_parser.add_argument(
        "--tfidf",
        default="output/tfidf",
        help="каталог с TF-IDF файлами (tfidf_lemmas_<id>.txt, по умолчанию: output/tfidf)",
    )
    vector_index_parser.add_argument(
        "--out",
        default="output/vector_index",
        help="каталог для сохранения векторного индекса (по умолчанию: output/vector_index)",
    )

    vector_index_alias_parser = subparsers.add_parser(
        "vector-index",
        help="построить и сохранить векторный индекс по готовым TF-IDF файлам",
    )
    vector_index_alias_parser.add_argument(
        "--tfidf",
        default="output/tfidf",
        help="каталог с TF-IDF файлами (tfidf_lemmas_<id>.txt, по умолчанию: output/tfidf)",
    )
    vector_index_alias_parser.add_argument(
        "--out",
        default="output/vector_index",
        help="каталог для сохранения векторного индекса (по умолчанию: output/vector_index)",
    )

    vector_search_parser = subparsers.add_parser(
        "vector-search",
        help="выполнить косинусный поиск по сохранённому векторному индексу",
    )
    vector_search_parser.add_argument(
        "query",
        help="текстовый поисковый запрос",
    )
    vector_search_parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="размер top-K выдачи (по умолчанию: 10)",
    )
    vector_search_parser.add_argument(
        "--vector-index",
        default="output/vector_index",
        help="каталог с векторным индексом (по умолчанию: output/vector_index)",
    )
    vector_search_parser.add_argument(
        "--index",
        default="output/index.txt",
        help="путь к index.txt (filename<TAB>url, по умолчанию: output/index.txt)",
    )

    return parser


def main() -> int:
    """
    Точка входа CLI: парсит аргументы, вызывает обработчик подкоманды
    и возвращает код выхода.
    """
    parser = _build_parser()
    args = parser.parse_args()

    handlers = {
        "run": _cmd_run,
        "validate": _cmd_validate,
        "package": _cmd_package,
        "analyze": _cmd_analyze,
        "build-index": _cmd_build_index,
        "search": _cmd_search,
        "tfidf": _cmd_tfidf,
        "build-vector-index": _cmd_build_vector_index,
        "vector-index": _cmd_vector_index,
        "vector-search": _cmd_vector_search,
    }
    handler = handlers[args.command]
    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
