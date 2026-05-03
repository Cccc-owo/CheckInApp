"""
自定义异常类

提供统一的异常处理机制，避免直接抛出通用Exception
"""


class BaseAPIException(Exception):
    """API 异常基类"""

    def __init__(self, message: str, status_code: int = 500, error_code: str = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        super().__init__(self.message)


class ValidationError(BaseAPIException):
    """验证错误 - 400"""

    def __init__(self, message: str, error_code: str = "VALIDATION_ERROR"):
        super().__init__(message, status_code=400, error_code=error_code)


class AuthenticationError(BaseAPIException):
    """认证错误 - 401"""

    def __init__(self, message: str = "未授权", error_code: str = "AUTHENTICATION_ERROR"):
        super().__init__(message, status_code=401, error_code=error_code)


class AuthorizationError(BaseAPIException):
    """授权错误 - 403"""

    def __init__(self, message: str = "无权限访问", error_code: str = "AUTHORIZATION_ERROR"):
        super().__init__(message, status_code=403, error_code=error_code)


class ResourceNotFoundError(BaseAPIException):
    """资源未找到 - 404"""

    def __init__(self, message: str = "资源未找到", error_code: str = "NOT_FOUND"):
        super().__init__(message, status_code=404, error_code=error_code)


class ResourceConflictError(BaseAPIException):
    """资源冲突 - 409"""

    def __init__(self, message: str = "资源冲突", error_code: str = "CONFLICT"):
        super().__init__(message, status_code=409, error_code=error_code)


class BusinessLogicError(BaseAPIException):
    """业务逻辑错误 - 默认422，但可自定义状态码（如429）"""

    def __init__(self, message: str, error_code: str = "BUSINESS_ERROR", status_code: int = 422):
        super().__init__(message, status_code=status_code, error_code=error_code)


class InternalServerError(BaseAPIException):
    """服务器内部错误 - 500"""

    def __init__(self, message: str = "服务器内部错误", error_code: str = "INTERNAL_ERROR"):
        super().__init__(message, status_code=500, error_code=error_code)
