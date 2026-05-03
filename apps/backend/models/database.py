from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
from backend.config import settings

# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite 特定配置
    echo=False,  # 生产环境设为 False
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()


# SQLite timezone 修复：在加载对象后，将所有 naive datetime 转换为 UTC timezone-aware
@event.listens_for(Base, "load", propagate=True)
def receive_load(target, context):
    """在从数据库加载对象后，将所有 datetime 字段转换为 timezone-aware (UTC)"""
    for attr_name in dir(target):
        # 跳过私有属性和方法
        if attr_name.startswith('_'):
            continue

        try:
            attr_value = getattr(target, attr_name)

            # 如果是 naive datetime，添加 UTC timezone
            if isinstance(attr_value, datetime) and attr_value.tzinfo is None:
                setattr(target, attr_name, attr_value.replace(tzinfo=timezone.utc))
        except (AttributeError, TypeError):
            # 某些属性可能无法访问或设置，跳过
            continue


def get_db():
    """依赖注入：获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库：创建所有表"""
    Base.metadata.create_all(bind=engine)
