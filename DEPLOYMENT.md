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

После того как страницы сохранены в `output/pages`, можно получить списки токенов и лемм:

**macOS/Linux:**
```bash
PYTHONPATH=src python -m crawler analyze --pages output/pages --tokens output/tokens.txt --lemmas output/lemmas.txt
```

**Windows PowerShell:**
```powershell
$env:PYTHONPATH="src"; python -m crawler analyze --pages output/pages --tokens output/tokens.txt --lemmas output/lemmas.txt
```

Форматы выходных файлов:
- `tokens.txt` — по одному токену в строке.
- `lemmas.txt` — `лемма` + список токенов этой леммы через пробел.
