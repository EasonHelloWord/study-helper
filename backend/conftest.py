"""pytest测试框架配置文件

配置测试环境和共享fixtures。
fixtures是pytest的依赖注入机制，为测试提供必要的资源。
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
import tempfile
import os
from unittest.mock import patch

import database
import models
from main import app, get_db


def mock_password_hash(password: str) -> str:
    """模拟密码哈希函数
    
    用于测试环境中代替真实的PBKDF2-SHA256，避免性能和兼容性问题。
    在真实环境中，应使用实际的PBKDF2-SHA256哈希（通过passlib）。
    
    参数：
        password: 明文密码
        
    返回：
        模拟的哈希值：\"hashed_<password>_hashed\"
    """
    return f"hashed_{password}_hashed"


def mock_verify_password(plain: str, hashed: str) -> bool:
    """模拟密码验证函数
    
    用于测试环境中代替真实的bcrypt验证。
    
    参数：
        plain: 用户输入的明文密码
        hashed: 存储的密码哈希值
        
    返回：
        True 如果密码匹配，False 否则
    """
    return f"hashed_{plain}_hashed" == hashed


@pytest.fixture(scope="function")
def db():
    """数据库会话fixture
    
    为每个测试创建独立的临时SQLite数据库，
    测试完成后自动清理。
    
    Fixture作用域：
    - function: 每个测试函数运行一次（创建和销毁）
    - session: 整个测试会话只运行一次
    
    好处：
    - 测试隔离：测试之间互不影响
    - 自动清理：无需手动清理数据库
    - 可重复：每个测试都从干净的数据库开始
    
    Yield：
        SQLAlchemy Session对象
    """
    # 创建唯一的临时数据库文件
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)
    
    # 配置临时数据库连接URL
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    
    # 创建测试用的会话工厂
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # 创建所有表结构
    models.Base.metadata.create_all(bind=engine)
    
    # 覆盖FastAPI应用的get_db依赖，使用测试数据库
    def override_get_db():
        """返回测试数据库会话而不是生产数据库"""
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    # 应用依赖覆盖
    app.dependency_overrides[get_db] = override_get_db
    
    # 创建数据库会话
    db_session = TestingSessionLocal()
    
    # 使用mock函数替换bcrypt（测试性能优化）
    with patch('backend.crud.get_password_hash', side_effect=mock_password_hash), \
         patch('backend.crud.verify_password', side_effect=mock_verify_password):
        yield db_session
    
    # 清理：关闭会话
    db_session.close()
    
    # 清理：删除所有表
    models.Base.metadata.drop_all(bind=engine)
    
    # 清理：关闭数据库连接
    engine.dispose()
    
    # 清理：删除临时数据库文件
    try:
        os.unlink(db_path)
    except OSError:
        pass
    
    # 清理：恢复依赖覆盖
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client(db):
    """FastAPI 测试客户端fixture
    
    为每个测试提供FastAPI应用的测试客户端。
    
    功能：
    - 发送HTTP请求到应用
    - 验证响应状态码和内容
    - 模拟实际的HTTP交互
    
    区别于真实HTTP客户端：
    - 运行速度快（无网络开销）
    - 直接调用应用函数（可调试）
    - 自动处理多个请求的会话
    
    返回：
        TestClient实例
    """
    # 创建测试客户端
    with patch('backend.crud.get_password_hash', side_effect=mock_password_hash), \
         patch('backend.crud.verify_password', side_effect=mock_verify_password):
        return TestClient(app)
