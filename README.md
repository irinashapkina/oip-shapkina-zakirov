**ФИО:** Шапкина Ирина Викторовна и Закиров Рузиль Рамзилевич

**Группа:** 11-209

## Описание

Проект скачивает HTML-страницы по списку URL: до 100 страниц, сохраняет с разметкой, в файлы `0001.html`, `0002.html`, … в кодировке UTF-8. Формирует файл `index.txt` в формате «номер_файла TAB url».

## Result Preview

Пример содержимого `index.txt`:

```
0001.html	https://ru.wikipedia.org/wiki/Python
0002.html	https://habr.com/ru/articles/123456/
0003.html	https://docs.python.org/3/tutorial/
0004.html	https://pypi.org/project/aiohttp/
0005.html	https://example.com/page
```

## Project Structure

| Папка / файл | Назначение |
|--------------|------------|
| `src/crawler/` | Исходный код краулера |
| `data/` | Входные данные (список URL) |
| `examples/` | Примеры выходных файлов и данных |
| `requirements.txt` | Зависимости Python |

Подробная установка и запуск — в [DEPLOYMENT.md](DEPLOYMENT.md).
