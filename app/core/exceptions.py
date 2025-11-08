class AppException(Exception):
    """Base application exception"""
    
    def __init__(self, detail: str, status_code: int = 500, error_code: str = "INTERNAL_ERROR"):
        self.detail = detail
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(detail)

class ValidationError(AppException):
    """Validation error"""
    
    def __init__(self, detail: str):
        super().__init__(detail, 400, "VALIDATION_ERROR")

class NotFoundError(AppException):
    """Resource not found error"""
    
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(detail, 404, "NOT_FOUND")

class UnauthorizedError(AppException):
    """Unauthorized access error"""
    
    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(detail, 401, "UNAUTHORIZED")

class ForbiddenError(AppException):
    """Forbidden access error"""
    
    def __init__(self, detail: str = "Forbidden"):
        super().__init__(detail, 403, "FORBIDDEN")

class ConflictError(AppException):
    """Resource conflict error"""
    
    def __init__(self, detail: str = "Resource conflict"):
        super().__init__(detail, 409, "CONFLICT")

class RateLimitError(AppException):
    """Rate limit exceeded error"""
    
    def __init__(self, detail: str = "Rate limit exceeded"):
        super().__init__(detail, 429, "RATE_LIMIT_EXCEEDED")

class AIServiceError(AppException):
    """AI service error"""
    
    def __init__(self, detail: str = "AI service unavailable"):
        super().__init__(detail, 503, "AI_SERVICE_ERROR")

class IntegrationError(AppException):
    """External integration error"""
    
    def __init__(self, detail: str = "Integration service error"):
        super().__init__(detail, 502, "INTEGRATION_ERROR")
