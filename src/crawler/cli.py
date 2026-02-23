import argparse
import sys
from pathlib import Path

from .run import run as run_crawler
from .validate import validate as validate_crawler
from .package import package as package_crawler
from .text_processing import analyze as analyze_text


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
        tokens_path=Path(args.tokens),
        lemmas_path=Path(args.lemmas),
    )


def _build_parser() -> argparse.ArgumentParser:
    """Собирает парсер с подкомандами run, validate, package, analyze."""
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
    analyze_parser.add_argument("--tokens", required=True, help="выходной TXT с токенами (по одному на строку)")
    analyze_parser.add_argument(
        "--lemmas",
        required=True,
        help="выходной TXT с леммами (формат: <лемма> <токен1> ... <токенN>)",
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
    }
    handler = handlers[args.command]
    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
