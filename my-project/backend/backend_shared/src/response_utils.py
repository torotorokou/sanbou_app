from fastapi.responses import JSONResponse


def api_response(
    *,
    status_code: int,
    status_str: str,
    code: str,
    detail: str,
    result: dict | None = None,
    hint: str | None = None,
):
    """APIレスポンス共通関数（hint追加版）"""
    content = {
        "status": status_str,
        "code": code,
        "detail": detail,
    }
    if result is not None:
        content["result"] = result
    if hint is not None:
        content["hint"] = hint
    return JSONResponse(status_code=status_code, content=content)
