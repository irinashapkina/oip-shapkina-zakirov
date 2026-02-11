# Руководство по развёртыванию

## Требования

- **Python 3.12** (или совместимая версия 3.12+)
- Доступ в интернет для скачивания страниц и установки зависимостей

## Установка

1. Перейти в каталог проекта:
   ```bash
   cd /путь/к/oip-shapkina-zakirov
   ```

2. Создать виртуальное окружение:
   ```bash
   python3.12 -m venv .venv
   ```

3. Активировать его:
   - macOS/Linux: `source .venv/bin/activate`
   - Windows: `.venv\Scripts\activate`

4. Установить зависимости:
   ```bash
   pip install -r requirements.txt
   ```

## Запуск скачивания

Из корня проекта:

```bash
python -m crawler run --input data/urls.txt --out output/pages --index output/index.txt --limit 100 --concurrency 10
```

- Список URL должен лежать в `data/urls.txt` (один URL на строку).

## Где хранится результат

После успешного `run`:

- **HTML-файлы:** `output/pages/` — файлы `0001.html`, `0002.html`, …
- **Индекс:** `output/index.txt` — строки вида `номер<TAB>url`, в кодировке UTF-8.

Каталог `output/` создаётся автоматически при первом запуске.

## Сборка архива

```bash
python -m crawler package --out output/submission.zip --pages output/pages --index output/index.txt
```

Архив `output/submission.zip` будет содержать каталог `pages/` с HTML и файл `index.txt` в корне архива.

Если не указать `--pages` и `--index`, по умолчанию используются `output/pages` и `output/index.txt`:

```bash
python -m crawler package --out output/submission.zip
```

Для подробного вывода при отладке добавьте к команде флаг `--verbose`.
