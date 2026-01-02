import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding='utf-8',
        case_sensitive=True,
        extra='ignore'
    )

    # 项目根目录
    BASE_DIR: Path = BASE_DIR

    # 项目基础配置
    PROJECT_NAME: str = "CheckIn API"
    VERSION: str = "2.0.0"
    API_PREFIX: str = "/api"

    # 数据库配置
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/data/checkin.db"

    # CORS 配置（从环境变量读取，用逗号分隔）
    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        """将CORS_ORIGINS字符串转换为列表"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    # 日志配置
    LOG_FILE: Path = BASE_DIR / "logs" / "backend.log"
    LOG_LEVEL: str = "INFO"

    # 会话文件配置
    SESSION_DIR: Path = BASE_DIR / "sessions"
    SESSION_CLEANUP_HOURS: int = 24

    # 邮件配置（从 .env 读取）
    SMTP_SERVER: str = ""
    SMTP_PORT: int = 465
    SMTP_SENDER_EMAIL: str = ""
    SMTP_SENDER_PASSWORD: str = ""
    SMTP_USE_SSL: bool = True

    # 前端 URL 配置（用于邮件中的链接）
    FRONTEND_URL: str = "http://localhost:3000"

    # 定时任务配置（可通过环境变量配置）
    TOKEN_CHECK_INTERVAL_MINUTES: int = 30  # Token 检查间隔（分钟）
    SESSION_CLEANUP_INTERVAL_HOURS: int = 24  # 会话清理间隔（小时）

    # Selenium / Chrome 配置（从 .env 读取）
    CHROME_BINARY_PATH: str = ""
    CHROMEDRIVER_PATH: str = ""


settings = Settings()
