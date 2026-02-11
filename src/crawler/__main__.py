"""
Точка входа при запуске пакета как модуля: python -m crawler ...
Делегирует выполнение в cli.main().
"""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
