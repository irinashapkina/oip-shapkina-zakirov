import logging
from pathlib import Path

from .download import download_html
from .storage import append_index, save_page

# Таймаут и ретраи для download_html
DEFAULT_TIMEOUT = 30.0
DEFAULT_RETRIES = 2


def _read_urls(input_path: Path) -> list[str]:
    """Читает URL из файла, пропускает пустые."""
    text = input_path.read_text(encoding="utf-8")
    return [line.strip() for line in text.splitlines() if line.strip()]


def run(
    input_path: Path,
    out_dir: Path,
    index_path: Path,
    limit: int,
    timeout: float = DEFAULT_TIMEOUT,
    retries: int = DEFAULT_RETRIES,
) -> int:
    """
    Читает URL из input_path, скачивает до limit страниц
    по очереди, сохраняет в out_dir и дописывает индекс в index_path.

    При ошибке загрузки URL логирует и пропускает. Если успешных скачиваний
    набралось меньше limit из‑за нехватки URL — возвращает ненулевой код.

    Returns:
        0 при успехе (набрано limit успешных), иначе 1.
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logger = logging.getLogger(__name__)
    urls = _read_urls(input_path)

    # Каждый run начинаем с пустого индекса
    if index_path.exists():
        index_path.write_text("", encoding="utf-8")

    success_count = 0
    next_n = 1

    for url in urls:
        if success_count >= limit:
            break
        try:
            html = download_html(url, timeout=timeout, retries=retries)
            save_page(out_dir, next_n, html)
            append_index(index_path, next_n, url)
            success_count += 1
            next_n += 1
        except Exception as e:
            logger.warning("Skip URL %s: %s", url, e)
            continue

    if success_count < limit:
        logger.error(
            "Not enough URLs: got %d successful downloads, need %d (URLs exhausted).",
            success_count,
            limit,
        )
        return 1
    return 0
