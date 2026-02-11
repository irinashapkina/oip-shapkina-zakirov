import sys
import zipfile
from pathlib import Path


def package(pages_dir: Path, index_path: Path, out_zip: Path) -> int:
    """
    Собирает submission.zip: внутри папка pages/ со всеми HTML и файл index.txt.

    Требует существования pages_dir (каталог) и index_path (файл).
    При отсутствии — сообщение в stderr и возврат 1.

    Returns:
        0 — успех, 1 — ошибка (нет данных или запись не удалась).
    """
    if not pages_dir.exists():
        print(f"package: pages directory not found: {pages_dir}", file=sys.stderr)
        return 1
    if not pages_dir.is_dir():
        print(f"package: pages path is not a directory: {pages_dir}", file=sys.stderr)
        return 1

    if not index_path.exists():
        print(f"package: index file not found: {index_path}", file=sys.stderr)
        return 1
    if not index_path.is_file():
        print(f"package: index path is not a file: {index_path}", file=sys.stderr)
        return 1

    try:
        out_zip.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in sorted(pages_dir.iterdir()):
                if f.is_file():
                    zf.write(f, arcname=f"pages/{f.name}")
            zf.write(index_path, arcname="index.txt")
    except OSError as e:
        print(f"package: failed to write zip: {e}", file=sys.stderr)
        return 1

    return 0
