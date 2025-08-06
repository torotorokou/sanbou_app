from fastapi.responses import JSONResponse


class BaseApiResponse:
    def __init__(
        self,
        *,
        code: str,
        detail: str,
        result: dict | None = None,
        hint: str | None = None,
        status_code: int = 200,
    ):
        self.code = code
        self.detail = detail
        self.result = result
        self.hint = hint
        self.status_code = status_code

    def to_json_response(self, status_str: str) -> JSONResponse:
        content = {
            "status": status_str,
            "code": self.code,
            "detail": self.detail,
        }
        if self.result is not None:
            content["result"] = self.result
        if self.hint is not None:
            content["hint"] = self.hint
        return JSONResponse(status_code=self.status_code, content=content)


class SuccessApiResponse(BaseApiResponse):
    def __init__(
        self,
        *,
        code: str,
        detail: str,
        result: dict | None = None,
        hint: str | None = None,
        status_code: int = 200,
    ):
        super().__init__(
            code=code, detail=detail, result=result, hint=hint, status_code=status_code
        )

    def to_json_response(self) -> JSONResponse:
        return super().to_json_response("success")


class ErrorApiResponse(BaseApiResponse):
    def __init__(
        self,
        *,
        code: str,
        detail: str,
        result: dict | None = None,
        hint: str | None = None,
        status_code: int = 422,
    ):
        super().__init__(
            code=code, detail=detail, result=result, hint=hint, status_code=status_code
        )

    def to_json_response(self) -> JSONResponse:
        return super().to_json_response("error")


# 旧関数も互換用に残しておく
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
