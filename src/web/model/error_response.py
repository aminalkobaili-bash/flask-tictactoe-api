from typing import Optional


class ErrorResponse:
    def __init__(self, error: str, details: Optional[str] = None):
        self.error = error
        self.details = details

    def to_json(self) -> dict:
        result = {"error": self.error}
        if self.details:
            result["details"] = self.details
        return result
