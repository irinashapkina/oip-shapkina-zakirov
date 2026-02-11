import argparse
import sys


def _cmd_run(_args: argparse.Namespace) -> int:
    """Подкоманда run: запуск краулера (заглушка)."""
    print("Not implemented")
    return 0


def _cmd_validate(_args: argparse.Namespace) -> int:
    """Подкоманда validate: проверка данных (пока заглушка)."""
    print("Not implemented")
    return 0


def _cmd_package(_args: argparse.Namespace) -> int:
    """Подкоманда package: формирование результата (пока заглушка)."""
    print("Not implemented")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    """Собирает парсер с подкомандами run, validate, package."""
    parser = argparse.ArgumentParser(
        prog="crawler",
        description="CLI для краулера.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help="доступные команды")

    subparsers.add_parser("run", help="запустить краулер")
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
