"""
测试新的异常处理系统
"""
import sys
sys.path.insert(0, '..')

from backend.exceptions import (
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    ResourceNotFoundError,
    BusinessLogicError,
)
from backend.schemas.response import ErrorResponse, ErrorDetail

def test_exceptions():
    """测试自定义异常"""
    print("=" * 60)
    print("测试自定义异常类")
    print("=" * 60)

    # 测试 ValidationError
    try:
        raise ValidationError("用户名长度必须在2-50之间")
    except ValidationError as e:
        print(f"✅ ValidationError: {e.message} (状态码: {e.status_code}, 代码: {e.error_code})")

    # 测试 AuthenticationError
    try:
        raise AuthenticationError("Token已过期")
    except AuthenticationError as e:
        print(f"✅ AuthenticationError: {e.message} (状态码: {e.status_code}, 代码: {e.error_code})")

    # 测试 AuthorizationError
    try:
        raise AuthorizationError("需要管理员权限")
    except AuthorizationError as e:
        print(f"✅ AuthorizationError: {e.message} (状态码: {e.status_code}, 代码: {e.error_code})")

    # 测试 ResourceNotFoundError
    try:
        raise ResourceNotFoundError("用户不存在")
    except ResourceNotFoundError as e:
        print(f"✅ ResourceNotFoundError: {e.message} (状态码: {e.status_code}, 代码: {e.error_code})")

    # 测试 BusinessLogicError
    try:
        raise BusinessLogicError("打卡任务已禁用")
    except BusinessLogicError as e:
        print(f"✅ BusinessLogicError: {e.message} (状态码: {e.status_code}, 代码: {e.error_code})")


def test_response_schemas():
    """测试响应 Schema"""
    print("\n" + "=" * 60)
    print("测试响应 Schema")
    print("=" * 60)

    # 测试 ErrorResponse
    error_response = ErrorResponse(
        error=ErrorDetail(
            code="VALIDATION_ERROR",
            message="邮箱格式不正确",
            field="email"
        )
    )

    response_dict = error_response.model_dump()
    print(f"✅ ErrorResponse 序列化成功:")
    print(f"   {response_dict}")

    assert response_dict["success"] == False
    assert response_dict["error"]["code"] == "VALIDATION_ERROR"
    assert response_dict["error"]["message"] == "邮箱格式不正确"
    assert response_dict["error"]["field"] == "email"
    print("✅ 所有断言通过")


def check_old_exception_patterns():
    """检查旧的异常处理模式"""
    print("\n" + "=" * 60)
    print("检查需要更新的旧异常代码")
    print("=" * 60)

    import os
    import re

    patterns = {
        "HTTPException with detail": r'raise HTTPException.*detail=f?".*{',
        "except Exception": r'except Exception as',
    }

    results = {}
    for pattern_name, pattern in patterns.items():
        results[pattern_name] = []

        for root, dirs, files in os.walk('../backend/api'):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        matches = re.findall(pattern, content, re.MULTILINE)
                        if matches:
                            results[pattern_name].append((filepath, len(matches)))

    for pattern_name, files in results.items():
        print(f"\n{pattern_name}:")
        if files:
            print(f"  ⚠️  发现 {sum(count for _, count in files)} 处使用")
            for filepath, count in files:
                print(f"     - {filepath}: {count} 处")
        else:
            print(f"  ✅ 未发现使用")


if __name__ == "__main__":
    test_exceptions()
    test_response_schemas()
    check_old_exception_patterns()

    print("\n" + "=" * 60)
    print("✅ 所有测试通过！新的异常处理系统工作正常")
    print("=" * 60)
