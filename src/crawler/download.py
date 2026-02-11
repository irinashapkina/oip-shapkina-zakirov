from typing import Optional

import requests
from requests.exceptions import HTTPError, RequestException


def download_html(url: str, timeout: float, retries: int) -> str:
    """
    Загружает страницу по URL и возвращает её HTML-текст.
    Args:
        url: URL страницы для загрузки.
        timeout: Таймаут запроса в секундах.
        retries: Сколько раз повторять запрос при неудаче.

    Returns:
        Текст ответа (response.text).

    Raises:
        Exception: Если после всех попыток загрузка не удалась.
    """
    last_error: Optional[Exception] = None
    attempts = retries + 1

    for attempt in range(attempts):
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code >= 500:
                last_error = Exception(
                    f"HTTP {response.status_code} at {url} (attempt {attempt + 1}/{attempts})"
                )
                continue
            response.raise_for_status()
            return response.text
        except RequestException as e:
            if isinstance(e, HTTPError) and e.response is not None and e.response.status_code < 500:
                raise
            last_error = e
            continue

    msg = f"Failed to download {url} after {attempts} attempt(s)"
    if last_error is not None:
        msg += f": {last_error}"
    raise Exception(msg)
