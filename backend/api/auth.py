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

router = APIRouter()


@router.post("/request_qrcode", response_model=dict, summary="请求 QQ 扫码二维码")
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
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="注册过于频繁，请 10 分钟后再试"
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
    - success: 扫描成功（包含 user_id 和 authorization）
    - error: 发生错误
    """
    try:
        result = AuthService.get_qrcode_status(session_id, db)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询扫码状态失败: {str(e)}"
        )


@router.post("/verify_token", response_model=dict, summary="验证 Token 有效性")
async def verify_token(
    request: TokenVerifyRequest,
    db: Session = Depends(get_db)
):
    """
    验证 Token 有效性

    - **authorization**: Token（可带或不带 "Bearer " 前缀）

    返回 Token 是否有效以及相关信息
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
async def alias_login(
    request: AliasLoginRequest,
    db: Session = Depends(get_db)
):
    """
    别名+密码登录（仅限已设置密码的用户）

    - **alias**: 用户别名
    - **password**: 密码

    返回登录结果，成功时包含 user_id 和 authorization

    注意：
    - 用户必须已设置密码才能使用此方式登录
    - Token 必须仍然有效（未过期）
    - 如果 Token 已过期，请使用扫码登录重新获取
    """
    try:
        result = AuthService.alias_login(request.alias, request.password, db)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"别名登录失败: {str(e)}"
        )
