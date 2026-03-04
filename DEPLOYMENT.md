# Руководство по развёртыванию

## Требования

- **Python 3.12** (или совместимая версия 3.12+)
- Доступ в интернет для скачивания страниц и установки зависимостей
- `aspell` с русским (`ru`) словарём для лемматизации

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

Пакет лежит в `src/`, поэтому для запуска модуля нужен **PYTHONPATH=src**

## Запуск скачивания

Из корня проекта.

**macOS/Linux:**
```bash
PYTHONPATH=src python -m crawler run --input data/urls.txt --out output/pages --index output/index.txt --limit 100
```

**Windows PowerShell:**
```powershell
$env:PYTHONPATH="src"; python -m crawler run --input data/urls.txt --out output/pages --index output/index.txt --limit 100
```

- Список URL должен лежать в `data/urls.txt` (один URL на строку).

## Проверка результата

**macOS/Linux:**
```bash
PYTHONPATH=src python -m crawler validate --pages output/pages --index output/index.txt --min-pages 100
```

**Windows PowerShell:**
```powershell
$env:PYTHONPATH="src"; python -m crawler validate --pages output/pages --index output/index.txt --min-pages 100
```

## Где хранится результат

После успешного `run`:

- **HTML-файлы:** `output/pages/` — файлы `0001.html`, `0002.html`, …
- **Индекс:** `output/index.txt` — строки вида `номер<TAB>url`, в кодировке UTF-8.

Каталог `output/` создаётся автоматически при первом запуске.

## Сборка архива

**macOS/Linux:**
```bash
PYTHONPATH=src python -m crawler package --pages output/pages --index output/index.txt --out output/submission.zip
```

**Windows PowerShell:**
```powershell
$env:PYTHONPATH="src"; python -m crawler package --pages output/pages --index output/index.txt --out output/submission.zip
```

Архив `output/submission.zip` будет содержать каталог `pages/` с HTML и файл `index.txt` в корне архива.

## Токенизация и лемматизация

После того как страницы сохранены в `output/pages`, можно получить токены и леммы
отдельно для каждой страницы:

**macOS/Linux:**
```bash
PYTHONPATH=src python -m crawler analyze --pages output/pages --tokens output/tokens --lemmas output/lemmas
```

**Windows PowerShell:**
```powershell
$env:PYTHONPATH="src"; python -m crawler analyze --pages output/pages --tokens output/tokens --lemmas output/lemmas
```

Форматы выходных файлов:
- в `output/tokens/` создаются файлы `0001_tokens.txt`, `0002_tokens.txt`, ...
  (по одному токену в строке для соответствующей страницы);
- в `output/lemmas/` создаются файлы `0001_lemmas.txt`, `0002_lemmas.txt`, ...
  (формат строк: `лемма` + список токенов этой леммы через пробел).

## Построение инвертированного индекса (по леммам)

После получения `output/lemmas/*.txt` можно построить инвертированный индекс по леммам:

**macOS/Linux:**
```bash
PYTHONPATH=src python -m crawler build-index --lemmas output/lemmas --out output/inverted_index.txt
```

**Windows PowerShell:**
```powershell
$env:PYTHONPATH="src"; python -m crawler build-index --lemmas output/lemmas --out output/inverted_index.txt
```

Формат строк в `inverted_index.txt`: `лемма<TAB>документ1 документ2 ... документN`.

## Булев поиск по индексу

Поддерживаются операторы `AND`, `OR`, `NOT` и скобки.

Пример с передачей запроса в аргументе:

**macOS/Linux:**
```bash
PYTHONPATH=src python -m crawler search --index output/inverted_index.txt --query "((психология AND стресс) OR (мотивация AND тревожность)) AND NOT выгорание"
```

**Windows PowerShell:**
```powershell
$env:PYTHONPATH="src"; python -m crawler search --index output/inverted_index.txt --query "((психология AND стресс) OR (мотивация AND тревожность)) AND NOT выгорание"
```

Если `--query` не передан, команда запросит строку интерактивно.

## Расчёт TF/IDF/TF-IDF (задание 4)

После того как выполнены задания 1–3 (скачивание, токенизация/лемматизация, построение инвертированного индекса), можно запустить расчёт TF/IDF/TF-IDF по всему корпусу.

Команда автоматически использует стандартную структуру репозитория:

- входные токены: `output/tokens/0001_tokens.txt`, `0002_tokens.txt`, …
- входные леммы: `output/lemmas/0001_lemmas.txt`, `0002_lemmas.txt`, …
- выходные TF-IDF файлы: `output/tfidf/`.

**macOS/Linux:**
```bash
PYTHONPATH=src python -m crawler tfidf
```

**Windows PowerShell:**
```powershell
$env:PYTHONPATH="src"; python -m crawler tfidf
```

Результат:

- Каталог `output/tfidf/` создаётся автоматически.
- Для каждого документа `<id>` (например, `0001`) будут созданы файлы:
  - `tfidf_terms_<id>.txt` — TF-IDF по терминам
  - `tfidf_lemmas_<id>.txt` — TF-IDF по леммам

Формат строк в этих файлах:

```text
<термин_или_лемма> <idf> <tf-idf>
```

Значения `idf` и `tf-idf` выводятся с фиксированной точностью до 6 знаков после запятой.
