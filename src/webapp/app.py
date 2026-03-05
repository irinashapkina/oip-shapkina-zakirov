from pathlib import Path

from flask import Flask, render_template_string, request

from crawler.cli import _read_url_index
from crawler.vector_search import load_vector_index, search_in_loaded_index

DEFAULT_VECTOR_INDEX_DIR = Path("output/vector_index")
DEFAULT_CORPUS_INDEX_PATH = Path("output/index.txt")
DEFAULT_TOP_K = 10

PAGE_TEMPLATE = """
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Vector Search</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 24px; }
    form { margin-bottom: 16px; }
    input[type=text] { width: 420px; max-width: 90vw; padding: 8px; }
    button { padding: 8px 12px; }
    table { border-collapse: collapse; width: 100%; margin-top: 12px; }
    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
    th { background: #f5f5f5; }
    .message { margin: 12px 0; color: #444; }
    .error { margin: 12px 0; color: #b00020; }
  </style>
</head>
<body>
  <h1>Vector Search</h1>
  <form action="/search" method="get">
    <input type="text" name="q" value="{{ query }}" placeholder="Введите запрос">
    <button type="submit">Search</button>
  </form>

  {% if message %}
    <div class="message">{{ message }}</div>
  {% endif %}

  {% if error %}
    <div class="error">{{ error }}</div>
  {% endif %}

  {% if results %}
    <table>
      <thead>
        <tr>
          <th>doc_id</th>
          <th>score</th>
          <th>url</th>
        </tr>
      </thead>
      <tbody>
        {% for row in results %}
          <tr>
            <td>{{ row.doc_id }}</td>
            <td>{{ row.score }}</td>
            <td><a href="{{ row.url }}" target="_blank" rel="noopener noreferrer">{{ row.url }}</a></td>
          </tr>
        {% endfor %}
      </tbody>
    </table>
  {% endif %}
</body>
</html>
"""


def create_app(
    *,
    vector_index_dir: Path = DEFAULT_VECTOR_INDEX_DIR,
    corpus_index_path: Path = DEFAULT_CORPUS_INDEX_PATH,
    top_k: int = DEFAULT_TOP_K,
) -> Flask:
    app = Flask(__name__)
    app.config["VECTOR_INDEX_DIR"] = vector_index_dir
    app.config["CORPUS_INDEX_PATH"] = corpus_index_path
    app.config["TOP_K"] = top_k

    @app.get("/")
    def index():
        return render_template_string(PAGE_TEMPLATE, query="", results=[], message="", error="")

    @app.get("/search")
    def search():
        query = (request.args.get("q") or "").strip()
        if not query:
            return render_template_string(
                PAGE_TEMPLATE,
                query="",
                results=[],
                message="Введите запрос",
                error="",
            )

        try:
            vector_index = load_vector_index(index_dir=app.config["VECTOR_INDEX_DIR"])
        except FileNotFoundError:
            return render_template_string(
                PAGE_TEMPLATE,
                query=query,
                results=[],
                message="",
                error=(
                    "Векторный индекс не найден. "
                    "Сначала запустите: PYTHONPATH=src python -m crawler vector-index --tfidf output/tfidf "
                    f"--out {app.config['VECTOR_INDEX_DIR']}"
                ),
            )
        except ValueError as exc:
            return render_template_string(
                PAGE_TEMPLATE,
                query=query,
                results=[],
                message="",
                error=f"Ошибка формата индекса: {exc}",
            )

        try:
            url_map = _read_url_index(app.config["CORPUS_INDEX_PATH"])
        except ValueError as exc:
            return render_template_string(
                PAGE_TEMPLATE,
                query=query,
                results=[],
                message="",
                error=f"Ошибка чтения index.txt: {exc}",
            )

        try:
            ranked = search_in_loaded_index(
                query=query,
                top_k=app.config["TOP_K"],
                vector_index=vector_index,
            )
        except ValueError as exc:
            return render_template_string(
                PAGE_TEMPLATE,
                query=query,
                results=[],
                message="",
                error=str(exc),
            )

        results = [
            {
                "doc_id": doc_id,
                "score": f"{score:.6f}",
                "url": url_map.get(doc_id, ""),
            }
            for doc_id, score in ranked
        ]
        message = "Ничего не найдено" if not results else ""
        return render_template_string(
            PAGE_TEMPLATE,
            query=query,
            results=results,
            message=message,
            error="",
        )

    return app


app = create_app()
