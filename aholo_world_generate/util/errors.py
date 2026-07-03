class AholoError(Exception):
    """Base error for Aholo plugin operations."""


class AholoApiError(AholoError):
    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        biz_code: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.biz_code = biz_code

    def __str__(self) -> str:
        parts = [super().__str__()]
        if self.biz_code:
            parts.append(f"bizCode={self.biz_code}")
        if self.status_code is not None:
            parts.append(f"http={self.status_code}")
        return " | ".join(parts)


class AholoUploadError(AholoError):
    pass


class AholoTimeoutError(AholoError):
    pass
