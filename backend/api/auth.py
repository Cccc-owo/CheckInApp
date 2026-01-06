from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session

from backend.models import get_db
from backend.schemas.auth import (
    QRCodeRequest,
    QRCodeResponse,
    QRCodeStatusResponse,
    TokenVerifyRequest,
    TokenVerifyResponse,
    AliasLoginRequest,
    AliasLoginResponse,
)
from backend.services.auth_service import AuthService
from backend.exceptions import BusinessLogicError
from backend.limiter import limiter

router = APIRouter()


@router.post("/request_qrcode", response_model=dict, summary="请求 QQ 扫码二维码")
@limiter.limit("10/minute")  # 每分钟最多10次请求
async def request_qrcode(
    request_obj: QRCodeRequest,
    req: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    请求 QQ 扫码二维码

    - **alias**: 用户别名

    返回会话 ID，用于后续查询扫码状态
    """
    from backend.services.registration_manager import registration_manager
    import secrets

    # 检查注册限流 Cookie
    reg_cookie = req.cookies.get("reg_limit")

    if reg_cookie:
        if not registration_manager.check_registration_cookie(reg_cookie):
            raise BusinessLogicError(
                message="注册过于频繁，请 10 分钟后再试",
                error_code="RATE_LIMIT_EXCEEDED",
                status_code=429
            )
    else:
        # 生成新的 Cookie
        reg_cookie = secrets.token_urlsafe(16)

    # 获取客户端 IP
    client_ip = req.client.host if req.client else "unknown"

    # 如果有代理，尝试从 X-Forwarded-For 获取真实 IP
    forwarded_for = req.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()

    try:
        result = AuthService.request_qrcode(request_obj.alias, client_ip, db)

        # 设置限流 Cookie（10 分钟）
        response.set_cookie(
            key="reg_limit",
            value=reg_cookie,
            max_age=600,  # 10 分钟
            httponly=True,
            samesite="lax"
        )

        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建扫码会话失败: {str(e)}"
        )


@router.get("/qrcode_status/{session_id}", response_model=dict, summary="检查二维码扫描状态")
async def get_qrcode_status(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    检查二维码扫描状态

    - **session_id**: 会话 ID

    状态说明:
    - pending: 正在初始化
    - waiting_scan: 等待扫描（包含二维码图片 Base64）
    - success: 扫描成功（包含 JWT token 和 user 信息）
    - error: 发生错误

    认证架构说明:
    - 扫码成功后返回 JWT token（用于网站登录，21天有效期）
    - 同时更新数据库中的 authorization token（用于打卡业务）
    - 两种 token 分别管理，互不影响
    """
    try:
        result = AuthService.get_qrcode_status(session_id, db)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询扫码状态失败: {str(e)}"
        )


@router.delete("/qrcode_session/{session_id}", response_model=dict, summary="取消二维码登录会话")
async def cancel_qrcode_session(
    session_id: str
):
    """
    取消二维码登录会话

    - **session_id**: 会话 ID

    用于用户关闭二维码对话框时,终止后台的 Selenium 进程
    """
    try:
        result = AuthService.cancel_qrcode_session(session_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"取消会话失败: {str(e)}"
        )


@router.post("/verify_token", response_model=dict, summary="验证 JWT Token 有效性")
async def verify_token(
    request: TokenVerifyRequest,
    db: Session = Depends(get_db)
):
    """
    验证 JWT Token 有效性（网站登录认证）

    - **authorization**: JWT Token（可带或不带 "Bearer " 前缀）

    返回 Token 是否有效以及用户信息

    注意：
    - 此接口验证的是 JWT token（用于网站登录，21天有效期）
    - 不验证打卡业务的 authorization token（存储在数据库中）
    - JWT token 过期需要重新登录，但打卡 token 过期不影响网站使用
    """
    try:
        result = AuthService.verify_token(request.authorization, db)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"验证 Token 失败: {str(e)}"
        )


@router.post("/alias_login", response_model=dict, summary="别名+密码登录")
@limiter.limit("5/minute")  # 每分钟最多5次登录尝试
async def alias_login(
    request: AliasLoginRequest,
    req: Request,
    db: Session = Depends(get_db)
):
    """
    别名+密码登录（仅限已设置密码的用户）

    - **alias**: 用户别名
    - **password**: 密码

    返回登录结果，成功时包含 JWT token 和 user 信息

    认证架构说明:
    - 登录成功后返回 JWT token（用于网站登录，21天有效期）
    - 如果数据库中的打卡 authorization token 过期，会返回警告信息
    - 打卡 token 过期不影响网站登录，但无法自动打卡，建议扫码更新

    注意：
    - 用户必须已设置密码才能使用此方式登录
    - 即使打卡 token 已过期，仍然可以使用密码登录网站
    - 如需更新打卡 token，请使用扫码登录
    """
    try:
        result = AuthService.alias_login(request.alias, request.password, db)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"别名登录失败: {str(e)}"
        )
