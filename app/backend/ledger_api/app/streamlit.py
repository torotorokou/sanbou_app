# Minimal stub for streamlit to allow FastAPI server to import modules that reference streamlit
# This avoids installing heavy streamlit in the API container.

from typing import Any, Iterable, List

# simple dict-like session state
session_state: dict[str, Any] = {}


def write(*args: Any, **kwargs: Any) -> None:
    pass


def dataframe(*args: Any, **kwargs: Any) -> None:
    pass


def success(*args: Any, **kwargs: Any) -> None:
    pass


def warning(*args: Any, **kwargs: Any) -> None:
    pass


def error(*args: Any, **kwargs: Any) -> None:
    pass


def button(label: str, *args: Any, **kwargs: Any) -> bool:
    return False


class _Col:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def columns(spec: Iterable[Any]) -> List[_Col]:
    # Return the same number of dummy columns as requested
    try:
        n = len(list(spec))
    except Exception:
        n = 1
    return [_Col() for _ in range(max(1, n))]


def rerun() -> None:
    pass


def stop() -> None:
    pass
