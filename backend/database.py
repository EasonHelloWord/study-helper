"""数据库配置和初始化模块

该模块负责：
- SQLAlchemy数据库引擎创建
- 数据库会话工厂配置
- ORM基类声明
- 数据库表初始化
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# 获取当前文件所在的目录路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# SQLite数据库文件路径
DB_PATH = os.path.join(BASE_DIR, "db.sqlite3")

# SQLAlchemy数据库连接URL
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

# 创建数据库引擎
# check_same_thread=False 允许在不同线程中使用SQLite连接（开发环境）
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 创建数据库会话工厂
# autocommit=False: 自动提交关闭，需要手动commit
# autoflush=False: 自动刷新关闭，需要手动flush
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建ORM基类，所有模型都应该继承自这个Base
Base = declarative_base()


def init_db():
    """初始化数据库
    
    根据所有已定义的模型创建对应的数据库表。
    必须在导入所有模型后调用此函数。
    """
    # 导入models模块以确保所有模型在create_all前注册到Base
    import models  # noqa: F401

    # 根据Base中的所有模型元数据创建数据库表
    Base.metadata.create_all(bind=engine)
