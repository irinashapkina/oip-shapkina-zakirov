import argparse
import sys
from pathlib import Path

from .run import run as run_crawler


def _cmd_run(args: argparse.Namespace) -> int:
    """Подкоманда run: запуск краулера по URL из файла с сохранением в out_dir и индексом."""
    return run_crawler(
        input_path=Path(args.input),
        out_dir=Path(args.out),
        index_path=Path(args.index),
        limit=args.limit,
    )


def _cmd_validate(_args: argparse.Namespace) -> int:
    """Подкоманда validate: проверка данных (заглушка)."""
    print("Not implemented")
    return 0


def _cmd_package(_args: argparse.Namespace) -> int:
    """Подкоманда package: формирование результата (заглушка)."""
    print("Not implemented")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    """Собирает парсер с подкомандами run, validate, package."""
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
    subparsers.add_parser("validate", help="проверить конфигурацию/данные")
    subparsers.add_parser("package", help="упаковать результат")

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
    }
    handler = handlers[args.command]
    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
