import os
from pathlib import Path

from .app import DEFAULT_CORPUS_INDEX_PATH
from .app import DEFAULT_VECTOR_INDEX_DIR
from .app import create_app


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def main() -> None:
    vector_index_dir = Path(os.getenv("VECTOR_INDEX_DIR", str(DEFAULT_VECTOR_INDEX_DIR)))
    corpus_index_path = Path(os.getenv("INDEX_PATH", str(DEFAULT_CORPUS_INDEX_PATH)))
    port = _int_env("PORT", 8000)

    app = create_app(
        vector_index_dir=vector_index_dir,
        corpus_index_path=corpus_index_path,
    )
    app.run(host="127.0.0.1", port=port, debug=False)


if __name__ == "__main__":
    main()
