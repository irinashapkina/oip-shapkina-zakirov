import sys
from pathlib import Path


def validate(pages_dir: Path, index_path: Path, min_pages: int) -> int:
    """
    Проверяет индекс и каталог страниц.

    - index_path должен существовать (файл).
    - В pages_dir должно быть не меньше min_pages файлов.
    - Каждая непустая строка index: filename<TAB>url; filename должен существовать в pages_dir.

    При первой же ошибке выводит сообщение в stderr и возвращает 1.
    Returns:
        0 — всё ок, 1 — ошибка валидации.
    """
    # Индекс существует
    if not index_path.exists():
        print(f"validate: index file not found: {index_path}", file=sys.stderr)
        return 1
    if not index_path.is_file():
        print(f"validate: index path is not a file: {index_path}", file=sys.stderr)
        return 1

    # Каталог страниц и количество файлов
    if not pages_dir.exists():
        print(f"validate: pages directory not found: {pages_dir}", file=sys.stderr)
        return 1
    if not pages_dir.is_dir():
        print(f"validate: pages path is not a directory: {pages_dir}", file=sys.stderr)
        return 1

    page_files = [f for f in pages_dir.iterdir() if f.is_file()]
    if len(page_files) < min_pages:
        print(
            f"validate: not enough pages: {len(page_files)} in {pages_dir}, required >= {min_pages}",
            file=sys.stderr,
        )
        return 1

    # Каждая строка: filename<TAB>url, файл есть в pages
    lines = index_path.read_text(encoding="utf-8").splitlines()
    for line_no, line in enumerate(lines, start=1):
        line = line.strip()
        if not line:
            continue
        if "\t" not in line:
            print(
                f"validate: index line {line_no}: expected 'filename<TAB>url', got no TAB",
                file=sys.stderr,
            )
            return 1
        parts = line.split("\t", 1)
        if len(parts) != 2:
            print(
                f"validate: index line {line_no}: expected exactly one TAB",
                file=sys.stderr,
            )
            return 1
        filename, _url = parts
        if not filename.strip():
            print(
                f"validate: index line {line_no}: empty filename",
                file=sys.stderr,
            )
            return 1
        file_path = pages_dir / filename
        if not file_path.exists() or not file_path.is_file():
            print(
                f"validate: index line {line_no}: file not found in pages: {filename}",
                file=sys.stderr,
            )
            return 1

    return 0
