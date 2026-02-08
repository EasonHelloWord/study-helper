"""SQLAlchemy ORM数据模型

定义数据库表结构和表之间的关系。
所有模型都继承自Base，在初始化数据库时会创建对应的表。
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from database import Base
import datetime


class User(Base):
    """用户模型
    
    存储用户账户信息和认证相关数据。
    
    字段说明：
    - id: 主键，自增整数
    - uuid: 用户的唯一标识符，唯一且索引化
    - username: 登录用户名，唯一且索引化
    - hashed_password: PBKDF2-SHA256哈希后的密码
    - nickname: 用户昵称（可选）
    - is_active: 账户是否激活（默认激活）
    - is_admin: 是否为管理员（默认否）
    - created_at: 账户创建时间（自动设置为当前UTC时间）
    """
    __tablename__ = "users"
    
    # 主键字段
    id = Column(Integer, primary_key=True, index=True)
    
    # 唯一标识符：UUID格式，最多64字符
    uuid = Column(String(64), unique=True, index=True, nullable=False)
    
    # 用户名：最多128字符，用于登录
    username = Column(String(128), unique=True, index=True, nullable=False)
    
    # 密码哈希值：最多256字符（PBKDF2运行HMAC-SHA256生成的哈希）
    hashed_password = Column(String(256), nullable=False)
    
    # 用户昵称：最多128字符，可选
    nickname = Column(String(128), nullable=True)
    
    # 账户激活标志：是否可以登录和使用系统
    is_active = Column(Boolean, default=True)
    
    # 管理员标志：是否拥有管理员权限
    is_admin = Column(Boolean, default=False)
    
    # 账户创建时间：自动记录为当前UTC时间
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Problem(Base):
    """问题/题目模型
    
    存储用户上传的学习题目。
    
    字段说明：
    - id: 主键，自增整数
    - owner_id: 题目上传者的用户ID（外键）
    - source_type: 题目来源类型（如\"text\"、\"image\"等）
    - raw: 原始题目内容（通常是用户输入的文本或上传文件名）
    - file_content: Base64编码的文件内容（当上传图片/PDF等时存储）
    - parsed: 解析后的题目内容（经过AI处理）
    - subject: 学科（如\"数学\"、\"物理\"等）
    - course: 课程名称
    - problem_type: 题型（如\"选择\"、\"填空\"、\"解答\"等）
    - knowledge_tags: 知识点标签（JSON格式，如\"[\\\"函数\\\", \\\"微积分\\\"]\"）
    - difficulty: 难度估计（1-5，1=最简单）
    - is_bookmarked: 是否收藏
    - tags: 用户自定义标签（JSON格式）
    - notes: 用户备注
    - created_at: 题目上传时间
    - updated_at: 题目最后更新时间
    
    关系：
    - owner: 关联到User模型，表示题目的拥有者
    """
    __tablename__ = "problems"
    
    # 主键字段
    id = Column(Integer, primary_key=True, index=True)
    
    # 题目所有者用户ID，可为空允许系统题目
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # 题目来源类型：\"text\"表示文本，\"image\"表示图片，\"latex\"表示LaTeX等
    source_type = Column(String(32), default="text")
    
    # 原始题目内容：保存用户输入或上传的原始数据
    raw = Column(Text, nullable=True)
    
    # 文件内容：Base64编码的文件内容，仅当source_type为image/pdf等时才有值
    file_content = Column(Text, nullable=True)
    
    # 解析后的题目内容：AI处理后的结构化题目
    parsed = Column(Text, nullable=True)
    
    # 学科：如\"数学\"、\"物理\"、\"化学\"等，用于分类
    subject = Column(String(64), nullable=True, index=True)
    
    # 课程名称：如\"高等数学\"、\"线性代数\"等
    course = Column(String(128), nullable=True)
    
    # 题型：如\"选择\"、\"填空\"、\"解答\"、\"证明\"等
    problem_type = Column(String(64), nullable=True)
    
    # 知识点标签：JSON格式字符串，如\"[\\\"函数\\\", \\\"微积分\\\"]\"
    knowledge_tags = Column(Text, nullable=True)
    
    # 难度估计：1-5表示简单到困难，可选
    difficulty = Column(Integer, nullable=True)
    
    # 是否收藏：用于\"我的题库\"筛选
    is_bookmarked = Column(Boolean, default=False)
    
    # 用户自定义标签：JSON格式字符串
    tags = Column(Text, nullable=True)
    
    # 用户备注：记录用户对这道题的笔记
    notes = Column(Text, nullable=True)
    
    # 题目创建时间：自动记录为当前UTC时间
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # 题目最后更新时间：自动更新
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # 与User建立关系：一个用户可以有多个题目
    owner = relationship("User")


class Attempt(Base):
    """尝试/答题记录模型
    
    记录用户尝试解答题目的历史。
    
    字段说明：
    - id: 主键，自增整数
    - user_id: 答题用户的ID（外键）
    - problem_id: 题目ID（外键）
    - correct: 答题是否正确（可为True/False/None）
    - score: 获得的分数（0-100或其他评分）
    - submitted_at: 提交时间
    
    关系：
    - user: 关联到User模型，表示答题者
    - problem: 关联到Problem模型，表示被答题的问题
    """
    __tablename__ = "attempts"
    
    # 主键字段
    id = Column(Integer, primary_key=True, index=True)
    
    # 答题用户ID（外键，不能为空）
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # 题目ID（外键，不能为空）
    problem_id = Column(Integer, ForeignKey("problems.id"))
    
    # 答题是否正确：True(正确)/False(错误)/None(未评分)
    correct = Column(Boolean, nullable=True)
    
    # 答题成绩：可为百分比、绩点等
    score = Column(Float, nullable=True)
    
    # 答题提交时间：自动记录为当前UTC时间
    submitted_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # 与User建立关系：一个用户可以有多次答题记录
    user = relationship("User")
    
    # 与Problem建立关系：一道题可以被多个用户答过
    problem = relationship("Problem")


class TopicMastery(Base):
    """主题掌握度模型
    
    记录用户对各个学习主题的掌握程度。
    用于生成学习进度和个性化建议。
    
    字段说明：
    - id: 主键，自增整数
    - user_id: 用户ID（外键）
    - topic: 学习主题名称（如\"代数\"、\"几何\"等）
    - mastery: 掌握度分数（0.0-1.0，表示0%-100%）
    
    关系：
    - user: 关联到User模型，表示学生
    """
    __tablename__ = "topic_mastery"
    
    # 主键字段
    id = Column(Integer, primary_key=True, index=True)
    
    # 用户ID（外键，表示是哪个学生的掌握度）
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # 学习主题：需要索引以支持快速查询
    # 例如：\"函数\"、\"导数\"、\"线性代数\"等
    topic = Column(String(128), index=True)
    
    # 掌握度分数：范围0.0-1.0，0表示完全不懂，1表示完全掌握
    # 可通过用户答题情况动态计算更新
    mastery = Column(Float, default=0.0)
    
    # 与User建立关系：一个用户可以对应多个主题的掌握度记录
    user = relationship("User")
