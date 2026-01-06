from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError as PydanticValidationError
import logging
from pathlib import Path

from backend.config import settings
from backend.models import init_db
from backend.exceptions import BaseAPIException
from backend.schemas.response import ErrorResponse, ErrorDetail
from backend.limiter import limiter

# 配置日志
settings.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(settings.LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("正在启动 CheckIn API 服务...")

    # 初始化数据库
    logger.info("正在初始化数据库...")
    init_db()
    logger.info("数据库初始化完成")

    # 确保必要的目录存在
    settings.SESSION_DIR.mkdir(parents=True, exist_ok=True)
    (settings.BASE_DIR / "data").mkdir(parents=True, exist_ok=True)

    # 启动调度器
    logger.info("正在启动调度器...")
    from backend.services.scheduler_service import start_scheduler
    start_scheduler()

    logger.info(f"CheckIn API 服务已启动，版本: {settings.VERSION}")

    yield

    # 关闭时执行
    logger.info("正在关闭 CheckIn API 服务...")
    from backend.services.scheduler_service import stop_scheduler
    stop_scheduler()
    logger.info("CheckIn API 服务已关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="接龙自动打卡系统 API",
    lifespan=lifespan,
)

# 绑定速率限制器到应用
app.state.limiter = limiter

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,  # 使用属性方法获取列表
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理器
@app.exception_handler(BaseAPIException)
async def api_exception_handler(request: Request, exc: BaseAPIException):
    """处理自定义 API 异常"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=ErrorDetail(
                code=exc.error_code,
                message=exc.message
            )
        ).model_dump()
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理请求验证错误"""
    errors = exc.errors()
    # 取第一个错误作为主要错误消息
    first_error = errors[0] if errors else {}
    field = ".".join(str(loc) for loc in first_error.get("loc", []))
    message = first_error.get("msg", "验证错误")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error=ErrorDetail(
                code="VALIDATION_ERROR",
                message=message,
                field=field or None
            )
        ).model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """处理未捕获的异常"""
    logger.error(f"未处理的异常: {type(exc).__name__}: {str(exc)}", exc_info=True)

    # 不向客户端暴露内部错误详情
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error=ErrorDetail(
                code="INTERNAL_ERROR",
                message="服务器内部错误，请稍后重试"
            )
        ).model_dump()
    )


# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "service": settings.PROJECT_NAME,
    }


# 根路径
@app.get("/")
async def root():
    """API 根路径"""
    return {
        "message": "欢迎使用接龙自动打卡系统 API",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health",
    }


# 注册路由
from backend.api import auth, users, check_in, admin, tasks, templates
app.include_router(auth.router, prefix=f"{settings.API_PREFIX}/auth", tags=["认证"])
app.include_router(users.router, prefix=f"{settings.API_PREFIX}/users", tags=["用户"])
app.include_router(tasks.router, prefix=f"{settings.API_PREFIX}/tasks", tags=["打卡任务"])
app.include_router(check_in.router, prefix=f"{settings.API_PREFIX}/check_in", tags=["打卡"])
app.include_router(admin.router, prefix=f"{settings.API_PREFIX}/admin", tags=["管理员"])
app.include_router(templates.router, prefix=f"{settings.API_PREFIX}/templates", tags=["任务模板"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
