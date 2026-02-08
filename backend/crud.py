"""数据库CRUD操作模块

包含所有与数据库交互的操作函数，包括：
- 用户管理：创建、查询、认证、激活/禁用
- 题目管理：创建、查询
- 学习档案：查询掌握度
"""

from sqlalchemy.orm import Session
import models
import schemas
from passlib.context import CryptContext
from uuid import uuid4
import json

# 密码加密/验证上下文
# schemes=["pbkdf2_sha256"]: 使用PBKDF2-SHA256算法进行密码加密
# 相比bcrypt：不需要native后端，无72字节限制，跨平台稳定
# deprecated="auto": 自动处理旧密码升级
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """对密码进行加密
    
    使用PBKDF2-SHA256算法将明文密码转换为安全的哈希值。
    PBKDF2会自动生成salt，同一密码每次生成的哈希值都不同。
    相比bcrypt，PBKDF2更稳定且无72字节限制。
    
    参数：
        password: 明文密码
        
    返回：
        密码的PBKDF2-SHA256哈希值（编码后约为70-100字符）
    """
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """验证密码
    
    将输入的明文密码与存储的哈希值进行比对。
    这个比较过程是恒时间的，防止时间攻击。
    
    参数：
        plain: 用户输入的明文密码
        hashed: 数据库中存储的密码哈希值
        
    返回：
        True 如果密码匹配，False 否则
    """
    return pwd_context.verify(plain, hashed)


def create_user(db: Session, user_in: schemas.UserCreate):
    """创建新用户
    
    创建用户账户，自动生成UUID并对密码进行加密。
    
    参数：
        db: 数据库会话
        user_in: 用户创建数据（包含username、password、nickname）
        
    返回：
        创建后的User模型对象（已保存到数据库）
        
    异常：
        可能抛出IntegrityError如果username已存在
    """
    user = models.User(
        uuid=str(uuid4()),  # 生成UUID作为用户全局唯一标识
        username=user_in.username,
        hashed_password=get_password_hash(user_in.password),  # 密码加密后存储
        nickname=user_in.nickname,
    )
    db.add(user)  # 将对象添加到会话
    db.commit()  # 提交事务到数据库
    db.refresh(user)  # 刷新对象以获取数据库生成的ID等字段
    return user


def get_user_by_username(db: Session, username: str):
    """按用户名查询用户
    
    根据用户名从数据库中查询用户，用于登录验证。
    
    参数：
        db: 数据库会话
        username: 要查询的用户名
        
    返回：
        User对象如果找到，None 如果用户不存在
    """
    return db.query(models.User).filter(models.User.username == username).first()


def authenticate_user(db: Session, username: str, password: str):
    """认证用户
    
    验证用户名和密码是否匹配，用于登录。
    
    参数：
        db: 数据库会话
        username: 用户名
        password: 明文密码
        
    返回：
        User对象如果身份验证成功，None 如果失败
        
    流程：
        1. 查询用户名是否存在
        2. 验证密码是否正确
        3. 返回用户对象或None
    """
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def list_users(db: Session, skip: int = 0, limit: int = 100):
    """列出所有用户（支持分页）
    
    用于管理员查看所有用户列表。
    
    参数：
        db: 数据库会话
        skip: 跳过前N条记录（默认0）
        limit: 返回最多N条记录（默认100）
        
    返回：
        User对象列表
    """
    return db.query(models.User).offset(skip).limit(limit).all()


def set_user_active(db: Session, user_id: int, active: bool):
    """设置用户激活状态
    
    管理员用此函数激活或禁用用户账户。
    禁用的用户无法登录。
    
    参数：
        db: 数据库会话
        user_id: 用户ID
        active: True激活，False禁用
        
    返回：
        更新后的User对象，或None如果用户不存在
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return None
    user.is_active = active  # 更新激活状态
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_problem(db: Session, owner_id: int, problem_in: schemas.ProblemCreate):
    """创建新题目
    
    用户上传新的学习题目。
    
    参数：
        db: 数据库会话
        owner_id: 题目所有者的用户ID
        problem_in: 题目信息（包含source_type、raw及元数据）
        
    返回：
        创建后的Problem模型对象（已保存到数据库）
    """
    # 将列表转换为JSON字符串
    knowledge_tags_json = json.dumps(problem_in.knowledge_tags) if problem_in.knowledge_tags else None
    tags_json = json.dumps(problem_in.tags) if problem_in.tags else None
    
    p = models.Problem(
        owner_id=owner_id,
        source_type=problem_in.source_type,  # 题目来源类型
        raw=problem_in.raw,  # 原始题目内容
        file_content=problem_in.file_content,  # Base64编码的文件内容
        subject=problem_in.subject,  # 学科
        course=problem_in.course,  # 课程名称
        problem_type=problem_in.problem_type,  # 题型
        knowledge_tags=knowledge_tags_json,  # 知识点标签（JSON格式）
        difficulty=problem_in.difficulty,  # 难度估计
        tags=tags_json,  # 用户标签（JSON格式）
        notes=problem_in.notes,  # 用户备注
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def get_problem(db: Session, problem_id: int):
    """根据ID查询题目
    
    获取特定题目的详细信息。
    
    参数：
        db: 数据库会话
        problem_id: 题目ID
        
    返回：
        Problem对象如果找到，None 如果题目不存在
    """
    return db.query(models.Problem).filter(models.Problem.id == problem_id).first()


def update_problem(db: Session, problem_id: int, problem_in: schemas.ProblemUpdate):
    """更新题目元数据
    
    更新已上传题目的元数据、标签和备注。
    
    参数：
        db: 数据库会话
        problem_id: 题目ID
        problem_in: 要更新的题目元数据
        
    返回：
        更新后的Problem对象，如果题目不存在则返回None
    """
    p = db.query(models.Problem).filter(models.Problem.id == problem_id).first()
    if not p:
        return None
    
    # 更新各字段（如果提供）
    if problem_in.subject is not None:
        p.subject = problem_in.subject
    if problem_in.course is not None:
        p.course = problem_in.course
    if problem_in.problem_type is not None:
        p.problem_type = problem_in.problem_type
    if problem_in.knowledge_tags is not None:
        p.knowledge_tags = json.dumps(problem_in.knowledge_tags)
    if problem_in.difficulty is not None:
        p.difficulty = problem_in.difficulty
    if problem_in.is_bookmarked is not None:
        p.is_bookmarked = problem_in.is_bookmarked
    if problem_in.tags is not None:
        p.tags = json.dumps(problem_in.tags)
    if problem_in.notes is not None:
        p.notes = problem_in.notes
    
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def get_learning_profile(db: Session, user_id: int):
    """获取用户的学习档案
    
    返回用户对各个主题的掌握度统计。
    用于展示学习进度和推荐学习材料。
    
    参数：
        db: 数据库会话
        user_id: 用户ID
        
    返回：
        字典包含：
        - user_id: 用户ID
        - mastery: 各主题掌握度的字典
          键：主题名称
          值：掌握度（0.0-1.0）
        - trend: 学习趋势（历史记录列表，当前为空占位）
        
    使用场景：
        查询所有该用户学习过的主题及掌握度
        用于生成学习报告和个性化建议
    """
    # 查询该用户的所有主题掌握度记录
    rows = db.query(models.TopicMastery).filter(models.TopicMastery.user_id == user_id).all()
    
    # 构建掌握度字典：{主题名: 掌握度分数}
    mastery = {r.topic: r.mastery for r in rows}
    
    # 返回学习档案（趋势数据为占位符，可在后续扩展）
    return {"user_id": user_id, "mastery": mastery, "trend": []}
