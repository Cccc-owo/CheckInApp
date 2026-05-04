from datetime import datetime, timezone

from sqlalchemy import DateTime, create_engine, event, inspect
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from backend.config import settings

# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite 特定配置
    echo=False,  # 生产环境设为 False
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


# SQLite timezone 修复：在加载对象后，将所有 naive datetime 转换为 UTC timezone-aware
@event.listens_for(Base, "load", propagate=True)
def receive_load(target, context):
    """在从数据库加载对象后，将所有 datetime 字段转换为 timezone-aware (UTC)"""
    mapper = inspect(target).mapper
    for attr in mapper.column_attrs:
        column = attr.columns[0]
        if not isinstance(column.type, DateTime):
            continue

        try:
            attr_value = getattr(target, attr.key)
        except (AttributeError, TypeError):
            continue

        if isinstance(attr_value, datetime) and attr_value.tzinfo is None:
            try:
                setattr(target, attr.key, attr_value.replace(tzinfo=timezone.utc))
            except (AttributeError, TypeError):
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
