import re
import shutil
import subprocess
import sys
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path

TOKEN_RE = re.compile(r"[А-Яа-яЁё]+(?:-[А-Яа-яЁё]+)?")

RU_STOPWORDS = {
    "а",
    "без",
    "более",
    "больше",
    "будет",
    "будто",
    "бы",
    "был",
    "была",
    "были",
    "было",
    "быть",
    "в",
    "вам",
    "вас",
    "весь",
    "во",
    "вот",
    "все",
    "всего",
    "всех",
    "вы",
    "где",
    "да",
    "даже",
    "для",
    "до",
    "его",
    "ее",
    "ей",
    "ею",
    "если",
    "есть",
    "еще",
    "же",
    "за",
    "здесь",
    "и",
    "из",
    "или",
    "им",
    "их",
    "к",
    "как",
    "ко",
    "когда",
    "кто",
    "ли",
    "либо",
    "между",
    "меня",
    "мне",
    "много",
    "может",
    "мой",
    "моя",
    "мы",
    "на",
    "над",
    "наш",
    "не",
    "него",
    "нее",
    "ней",
    "нет",
    "ни",
    "них",
    "но",
    "ну",
    "о",
    "об",
    "однако",
    "он",
    "она",
    "они",
    "оно",
    "от",
    "очень",
    "по",
    "под",
    "при",
    "с",
    "со",
    "так",
    "также",
    "такой",
    "там",
    "те",
    "тем",
    "то",
    "того",
    "тоже",
    "той",
    "только",
    "том",
    "ты",
    "у",
    "уже",
    "хотя",
    "чего",
    "чей",
    "чем",
    "что",
    "чтобы",
    "это",
    "эта",
    "эти",
    "этот",
    "я",
    "из-за",
    "из-под",
    "безо",
    "будто",
    "вдоль",
    "взамен",
    "вместо",
    "вне",
    "внутри",
    "вовремя",
    "вокруг",
    "вопреки",
    "вроде",
    "вследствие",
    "благодаря",
    "дабы",
    "доколе",
    "ежели",
    "зато",
    "зачем",
    "ибо",
    "иначе",
    "исключая",
    "коли",
    "кроме",
    "лишь",
    "меж",
    "мимо",
    "наподобие",
    "напротив",
    "насчет",
    "насчёт",
    "невзирая",
    "несмотря",
    "обо",
    "около",
    "относительно",
    "перед",
    "передо",
    "пока",
    "покуда",
    "помимо",
    "после",
    "поскольку",
    "посредством",
    "потому",
    "поэтому",
    "при",
    "причем",
    "причём",
    "против",
    "пусть",
    "пускай",
    "раз",
    "разве",
    "сверх",
    "сквозь",
    "словно",
    "согласно",
    "среди",
    "также",
    "тогда",
    "только",
    "хоть",
    "хотя",
    "через",
    "чрез",
}

STOPWORDS = RU_STOPWORDS


class _ArticleExtractor(HTMLParser):
    """Вытаскивает текст статьи; при отсутствии блока статьи — весь видимый текст."""

    _SKIP_TAGS = {"script", "style", "noscript", "svg"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self._capture_depth = 0
        self._article_chunks: list[str] = []
        self._fallback_chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self._SKIP_TAGS:
            # Пропускаем содержимое технических тегов (скрипты/стили/иконки).
            self._skip_depth += 1
            return

        if self._skip_depth > 0:
            return

        if self._capture_depth > 0:
            # Если уже внутри нужного блока, считаем вложенность, чтобы корректно выйти.
            self._capture_depth += 1
            return

        attr_map = dict(attrs)
        classes = set((attr_map.get("class") or "").split())
        if "field-name-body" in classes:
            # Основной контент статьи на сайте sibac.
            self._capture_depth = 1

    def handle_endtag(self, tag: str) -> None:
        if tag in self._SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1
            return

        if self._skip_depth > 0:
            return

        if self._capture_depth > 0:
            self._capture_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth > 0:
            return
        if data and not data.isspace():
            # Всегда копим fallback-текст, чтобы не потерять данные при нестандартной верстке.
            self._fallback_chunks.append(data)
            if self._capture_depth > 0:
                self._article_chunks.append(data)

    def get_text(self) -> str:
        if self._article_chunks:
            return " ".join(self._article_chunks)
        return " ".join(self._fallback_chunks)


def _extract_text(html: str) -> str:
    # Небольшой встроенный HTML-парсер без внешних зависимостей.
    parser = _ArticleExtractor()
    parser.feed(html)
    parser.close()
    return parser.get_text()


def _is_russian_token(token: str) -> bool:
    return bool(re.fullmatch(r"[А-Яа-яЁё]+(?:-[А-Яа-яЁё]+)?", token))


def _collect_unique_tokens(texts: list[str]) -> list[str]:
    tokens: set[str] = set()
    for text in texts:
        for raw in TOKEN_RE.findall(text.lower()):
            token = raw.strip("-")
            if not token or len(token) <= 2:
                continue
            if not _is_russian_token(token):
                continue
            if token in STOPWORDS:
                continue
            # set автоматически убирает дубликаты между документами.
            tokens.add(token)
    return sorted(tokens)


def _is_cyrillic(token: str) -> bool:
    return bool(re.search(r"[А-Яа-яЁё]", token))


def _parse_aspell_response(token: str, response_lines: list[str]) -> str:
    if not response_lines:
        return token
    if response_lines[0].startswith("*"):
        # "*" означает, что токен уже в нормальной форме словаря.
        return token
    if response_lines[0].startswith("+ "):
        # "+ lemma" — найден базовый вариант; используем его как лемму.
        lemma = response_lines[0][2:].strip().lower()
        if TOKEN_RE.fullmatch(lemma):
            return lemma
    # Для неоднозначных ответов (&/#/?) оставляем исходный токен, чтобы не вносить шум.
    return token


def _aspell_lemmas(tokens: list[str], dictionary: str) -> dict[str, str]:
    if not tokens:
        return {}

    proc = subprocess.run(
        ["aspell", "-d", dictionary, "-a"],
        input="\n".join(tokens) + "\n",
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "aspell failed")

    lines = proc.stdout.splitlines()
    if lines and lines[0].startswith("@(#)"):
        lines = lines[1:]

    # В pipe-режиме aspell отделяет ответы пустыми строками: собираем группы по токенам.
    groups: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if line == "":
            groups.append(current)
            current = []
            continue
        if line[0] in {"*", "+", "&", "#", "-", "?"}:
            current.append(line.strip())
    if current:
        groups.append(current)
    if len(groups) < len(tokens):
        # Защита от редких расхождений в выводе aspell.
        groups.extend([[] for _ in range(len(tokens) - len(groups))])

    result: dict[str, str] = {}
    for token, responses in zip(tokens, groups):
        result[token] = _parse_aspell_response(token, responses)
    return result


def _group_by_lemmas(tokens: list[str]) -> dict[str, list[str]]:
    if shutil.which("aspell") is None:
        raise RuntimeError("aspell is required to build lemma groups")

    ru_tokens = [token for token in tokens if _is_cyrillic(token)]
    hyphen_tokens = [token for token in tokens if "-" in token]

    # Составные слова через дефис не всегда корректно лемматизируются aspell:
    # оставляем их "как есть", чтобы не получить случайные леммы.
    ru_tokens = [token for token in ru_tokens if "-" not in token]

    token_to_lemma: dict[str, str] = {}
    token_to_lemma.update(_aspell_lemmas(ru_tokens, "ru"))
    token_to_lemma.update({token: token for token in hyphen_tokens})

    grouped: dict[str, set[str]] = defaultdict(set)
    for token in tokens:
        lemma = token_to_lemma.get(token, token)
        grouped[lemma].add(token)

    # Возвращаем стабильный порядок для воспроизводимого diff и проверок.
    return {lemma: sorted(grouped[lemma]) for lemma in sorted(grouped)}


def _write_tokens(path: Path, tokens: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Формат задания: один токен в строке.
    content = "".join(f"{token}\n" for token in tokens)
    path.write_text(content, encoding="utf-8")


def _write_lemma_groups(path: Path, lemma_groups: dict[str, list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    for lemma in sorted(lemma_groups):
        tokens = lemma_groups[lemma]
        # Формат задания: "<лемма> <токен1> ... <токенN>".
        lines.append(" ".join([lemma, *tokens]))
    content = "\n".join(lines)
    if content:
        content += "\n"
    path.write_text(content, encoding="utf-8")


def analyze(pages_dir: Path, tokens_dir: Path, lemmas_dir: Path) -> int:
    """
    Читает HTML-файлы из pages_dir и для каждого файла строит:
    - отдельный список уникальных токенов без служебных слов и мусора;
    - отдельную группировку токенов по леммам.
    """
    if not pages_dir.exists():
        print(f"analyze: pages directory not found: {pages_dir}", file=sys.stderr)
        return 1
    if not pages_dir.is_dir():
        print(f"analyze: pages path is not a directory: {pages_dir}", file=sys.stderr)
        return 1
    if tokens_dir.exists() and not tokens_dir.is_dir():
        print(f"analyze: tokens path is not a directory: {tokens_dir}", file=sys.stderr)
        return 1
    if lemmas_dir.exists() and not lemmas_dir.is_dir():
        print(f"analyze: lemmas path is not a directory: {lemmas_dir}", file=sys.stderr)
        return 1

    html_files = sorted(path for path in pages_dir.glob("*.html") if path.is_file())
    if not html_files:
        print(f"analyze: no html files in {pages_dir}", file=sys.stderr)
        return 1

    tokens_dir.mkdir(parents=True, exist_ok=True)
    lemmas_dir.mkdir(parents=True, exist_ok=True)

    # Этапы для каждой страницы: извлечение текста -> токены -> леммы -> запись артефактов.
    for html_path in html_files:
        text = _extract_text(html_path.read_text(encoding="utf-8"))
        tokens = _collect_unique_tokens([text])
        lemma_groups = _group_by_lemmas(tokens)

        tokens_path = tokens_dir / f"{html_path.stem}_tokens.txt"
        lemmas_path = lemmas_dir / f"{html_path.stem}_lemmas.txt"
        _write_tokens(tokens_path, tokens)
        _write_lemma_groups(lemmas_path, lemma_groups)

    return 0
