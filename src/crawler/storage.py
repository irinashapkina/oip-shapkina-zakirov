from pathlib import Path


def make_filename(n: int) -> str:
    """
    Формирует имя файла страницы по порядковому номеру.

    Args:
        n: Номер страницы (1, 2, …).

    Returns:
        Имя вида "0001.html", "0002.html" и т.д. (4 цифры, ведущие нули).
    """
    return f"{n:04d}.html"


def save_page(out_dir: Path, n: int, html: str) -> Path:
    """
    Сохраняет HTML-текст в файл в заданном каталоге.

    Имя файла — make_filename(n). Каталог создаётся при необходимости.
    Кодировка: UTF-8.

    Args:
        out_dir: Каталог для сохранения.
        n: Номер страницы (определяет имя файла).
        html: Содержимое страницы.

    Returns:
        Путь к сохранённому файлу.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / make_filename(n)
    path.write_text(html, encoding="utf-8")
    return path


def append_index(index_path: Path, n: int, url: str) -> None:
    """
    Добавляет одну строку в индексный файл.

    Формат строки: "0001.html<TAB>url". Кодировка файла: UTF-8.
    Родительский каталог index_path создаётся при необходимости.

    Args:
        index_path: Путь к индексному файлу.
        n: Номер страницы.
        url: URL страницы.
    """
    index_path.parent.mkdir(parents=True, exist_ok=True)
    line = f"{make_filename(n)}\t{url}\n"
    with index_path.open("a", encoding="utf-8") as f:
        f.write(line)
