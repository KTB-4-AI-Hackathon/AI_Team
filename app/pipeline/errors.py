from app.schemas import ERROR_CODE

class ApiError(Exception):
    def __init__(self, status_code: int, code: ERROR_CODE, message: str, retryable: bool):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.retryable = retryable