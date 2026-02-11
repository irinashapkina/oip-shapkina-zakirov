**ФИО:** Шапкина Ирина Викторовна и Закиров Рузиль Рамзилевич
**Группа:** 11 209

## Описание

Проект скачивает HTML-страницы по списку URL: до 100 страниц, сохраняет с разметкой, в файлы `0001.html`, `0002.html`, … в кодировке UTF-8. Формирует файл `index.txt` в формате «номер_файла TAB url».

## Result Preview

Пример содержимого `index.txt`:

```
0001	https://ru.wikipedia.org/wiki/Python
0002	https://habr.com/ru/articles/123456/
0003	https://docs.python.org/3/tutorial/
0004	https://pypi.org/project/aiohttp/
0005	https://example.com/page
```

## Project Structure

| Папка / файл | Назначение |
|--------------|------------|
| `src/crawler/` | Исходный код краулера |
| `data/` | Входные данные (список URL) |
| `examples/` | Примеры выходных файлов и данных |
| `requirements.txt` | Зависимости Python |

## Quick Start

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск скачивания
python -m crawler run --input data/urls.txt --out output/pages --index output/index.txt --limit 100 --concurrency 10

# Проверка результата
python -m crawler validate --pages output/pages --index output/index.txt --min-pages 100
```

Подробная установка и запуск — в [DEPLOYMENT.md](DEPLOYMENT.md).
