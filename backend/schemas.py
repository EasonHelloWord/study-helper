"""Pydantic数据验证模型（Schema）

定义API请求和响应的数据结构。
Pydantic会自动验证数据类型，并在验证失败时返回错误。
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
import datetime
import json


class UserCreate(BaseModel):
    """用户注册请求模型
    
    用于处理用户注册API请求。
    
    字段：
    - username: 用户名（必填），用于登录
    - password: 密码（必填），至少8个字符推荐
    - nickname: 昵称（可选），用于显示
    """
    username: str
    password: str
    nickname: Optional[str] = None


class UserOut(BaseModel):
    """用户响应模型
    
    用于API返回用户信息。
    不包含密码等敏感信息。
    
    字段：
    - id: 用户数据库ID
    - uuid: 用户唯一标识符
    - username: 用户名
    - nickname: 用户昵称
    
    Config说明：
    - orm_mode: 启用可以从SQLAlchemy模型直接转换
    """
    id: int
    uuid: str
    username: str
    nickname: Optional[str] = None

    class Config:
        # 允许从SQLAlchemy ORM对象直接创建Pydantic模型
        from_attributes = True


class Token(BaseModel):
    """JWT令牌响应模型
    
    用于登录成功后返回访问令牌。
    
    字段：
    - access_token: JWT令牌字符串，用于后续API认证
    - token_type: 令牌类型，通常为\"bearer\"
    """
    access_token: str
    token_type: str = "bearer"


class ProblemCreate(BaseModel):
    """创建题目请求模型
    
    用于上传新题目。
    
    字段：
    - source_type: 题目来源类型（默认\"text\"）
      可选值：\"text\"（文本）、\"image\"（图片）、\"latex\"（LaTeX）
    - raw: 原始题目内容（必填）
      可以是文本、文件名或其他原始数据
    - file_content: Base64编码的文件内容（可选）
      当上传图片、PDF等文件时使用
    - subject: 学科（可选）
      如\"数学\"、\"物理\"、\"化学\"等
    - course: 课程名称（可选）
      如\"高等数学\"、\"线性代数\"等
    - problem_type: 题型（可选）
      如\"选择\"、\"填空\"、\"解答\"等
    - knowledge_tags: 知识点标签列表（可选）
      如[\"函数\", \"微积分\"]
    - difficulty: 难度等级（可选）
      1-5，其中1=最简单，5=最困难
    - tags: 用户自定义标签列表（可选）
    - notes: 用户备注（可选）
    """
    source_type: str = "text"
    raw: str
    file_content: Optional[str] = None
    subject: Optional[str] = None
    course: Optional[str] = None
    problem_type: Optional[str] = None
    knowledge_tags: Optional[List[str]] = None
    difficulty: Optional[int] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None


class ProblemUpdate(BaseModel):
    """更新题目元数据请求模型
    
    用于更新已上传题目的元数据和备注。
    
    字段：
    - subject: 学科（可选）
    - course: 课程名称（可选）
    - problem_type: 题型（可选）
    - knowledge_tags: 知识点标签列表（可选）
    - difficulty: 难度等级（可选）
    - is_bookmarked: 是否收藏（可选）
    - tags: 用户自定义标签列表（可选）
    - notes: 用户备注（可选）
    """
    subject: Optional[str] = None
    course: Optional[str] = None
    problem_type: Optional[str] = None
    knowledge_tags: Optional[List[str]] = None
    difficulty: Optional[int] = None
    is_bookmarked: Optional[bool] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None


class ProblemOut(BaseModel):
    """题目响应模型
    
    用于API返回题目的完整信息。
    
    字段：
    - id: 题目ID
    - owner_id: 所有者用户ID
    - source_type: 题目来源类型
    - file_content: Base64编码的文件内容
    - subject: 学科
    - course: 课程
    - problem_type: 题型
    - knowledge_tags: 知识点标签列表
    - difficulty: 难度等级
    - is_bookmarked: 是否收藏
    - tags: 用户标签列表
    - notes: 用户备注
    - created_at: 创建时间
    - updated_at: 更新时间
    
    Config说明：
    - orm_mode: 允许从SQLAlchemy模型直接转换
    """
    id: int
    owner_id: Optional[int] = None
    source_type: str
    file_content: Optional[str] = None
    subject: Optional[str] = None
    course: Optional[str] = None
    problem_type: Optional[str] = None
    knowledge_tags: Optional[List[str]] = None
    difficulty: Optional[int] = None
    is_bookmarked: bool = False
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        # 允许从SQLAlchemy ORM对象直接创建Pydantic模型
        from_attributes = True
    
    @validator('knowledge_tags', pre=True, always=True)
    def parse_knowledge_tags(cls, v):
        """将JSON字符串解析为列表"""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return None
        return v
    
    @validator('tags', pre=True, always=True)
    def parse_tags(cls, v):
        """将JSON字符串解析为列表"""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return None
        return v


class ParsedProblem(BaseModel):
    """解析后的题目响应模型
    
    用于返回AI解析后的题目信息。
    
    字段：
    - title: 题目标题（可选）
    - structured: 结构化题目数据字典
      键值对形式存储题目的各个部分
    """
    title: Optional[str] = None
    structured: Dict[str, str]


class SolveRequest(BaseModel):
    """求解题目请求模型
    
    用于发送求解请求。
    可以提交已有题目的ID或新的题目文本。
    
    字段：
    - problem_id: 已上传题目的ID（可选）
      如果提供，则使用该题目进行求解
    - raw: 原始题目文本（可选）
      如果problem_id为空，则使用此字段
    - mode: 求解模式（默认\"structured\"）
      \"structured\": 结构化求解
      \"direct\": 直接给出答案
    """
    problem_id: Optional[int] = None
    raw: Optional[str] = None
    mode: Optional[str] = "structured"


class SolveResult(BaseModel):
    """求解结果响应模型
    
    用于返回题目求解结果。
    
    字段：
    - thoughts: 求解思路（可选）
      记录求解过程中的思考步骤
    - steps: 求解步骤列表（可选）
      列举求解的各个步骤
    - answer: 最终答案（可选）
      题目的最终答案或结论
    """
    thoughts: Optional[str] = None
    steps: Optional[List[str]] = None
    answer: Optional[str] = None


class LearningProfile(BaseModel):
    """学习档案模型
    
    用于返回用户的学习进度和掌握度信息。
    
    字段：
    - user_id: 用户ID
    - mastery: 主题掌握度字典
      键：主题名称（如\"代数\"）
      值：掌握度分数（0.0-1.0）
    - trend: 学习趋势（可选）
      列表形式的历史掌握度记录
      用于绘制学习曲线
    """
    user_id: int
    mastery: Dict[str, float]
    trend: Optional[List[Dict[str, float]]] = None
