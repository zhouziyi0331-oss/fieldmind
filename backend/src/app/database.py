"""旧模块路径兼容层。

历史代码使用 ``app.database``，当前数据库实现位于 ``app.core.database``。
"""

from app.core.database import Base, SessionLocal, engine, get_db

__all__ = ["Base", "SessionLocal", "engine", "get_db"]
