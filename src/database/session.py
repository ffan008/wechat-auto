"""
数据库会话管理
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from typing import Generator
import os
from dotenv import load_dotenv

from src.database.models import Base

load_dotenv()


class DatabaseManager:
    """数据库管理器"""

    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL", "postgresql://wechat_user:password@localhost:5432/wechat_auto")
        self.engine = None
        self.SessionLocal = None
        self._initialized = False

    def initialize(self):
        """初始化数据库连接"""
        if self._initialized:
            return

        self.engine = create_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=20,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=3600,
            echo=False,
        )

        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

        self._initialized = True

    def create_tables(self):
        """创建所有表"""
        if not self._initialized:
            self.initialize()
        Base.metadata.create_all(bind=self.engine)

    def drop_tables(self):
        """删除所有表（谨慎使用）"""
        if not self._initialized:
            self.initialize()
        Base.metadata.drop_all(bind=self.engine)

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """获取数据库会话的上下文管理器"""
        if not self._initialized:
            self.initialize()

        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_session_sync(self) -> Session:
        """获取数据库会话（非上下文管理器版本）"""
        if not self._initialized:
            self.initialize()
        return self.SessionLocal()


# 全局数据库管理器实例
db_manager = DatabaseManager()


def get_db():
    """FastAPI依赖注入函数"""
    with db_manager.get_session() as session:
        yield session
