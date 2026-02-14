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

    tmp_path = out_zip.with_suffix(out_zip.suffix + ".tmp")

    try:
        out_zip.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in sorted(pages_dir.rglob("*")):
                if f.is_file():
                    arcname = f"pages/{f.relative_to(pages_dir)}"
                    zf.write(f, arcname=arcname)
            zf.write(index_path, arcname="index.txt")

        if tmp_path.stat().st_size == 0:
            raise ValueError("Resulting zip file is empty")

        tmp_path.replace(out_zip)
        return 0

    except Exception as e:
        print(f"package: {e}", file=sys.stderr)
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
        if out_zip.exists() and out_zip.stat().st_size == 0:
            try:
                out_zip.unlink()
            except OSError:
                pass
        return 1
