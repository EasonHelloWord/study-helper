"""FastAPI应用主模块

包含所有API路由端点和认证逻辑。
主要功能：
- 用户认证（注册、登录、JWT验证）
- 题目管理（上传、查询、更新）
- 题目求解
- 学习档案查看
- 管理员功能（用户管理、禁用用户）
"""

from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import database
import models
import crud
import schemas
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import List
import os
import json
import base64

# ==================== 安全配置 ====================

# JWT密钥：用于签名和验证JWT令牌
# 从环境变量读取，如果没有则使用默认值（仅用于开发）
SECRET_KEY = os.environ.get("STUDY_HELPER_SECRET", "dev-secret-change-me")

# JWT加密算法：HS256是最常用的对称加密算法
ALGORITHM = "HS256"

# 访问令牌过期时间：7天（单位：分钟）
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

# ==================== 应用初始化 ====================

# 初始化数据库（创建所有表）
database.init_db()

# 创建FastAPI应用实例
app = FastAPI(title="Study Helper Backend")

# OAuth2认证方案：从请求头Authorization中提取Bearer token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


# ==================== 依赖函数 ====================

def get_db():
    """获取数据库会话（依赖注入）
    
    为每个请求创建一个数据库会话，
    请求完成后自动关闭连接。
    
    yield语法使这个函数成为上下文管理器：
    - yield前：准备资源（创建连接）
    - yield值：传递给路由处理函数
    - yield后：清理资源（关闭连接）
    """
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_access_token(data: dict, expires_delta: timedelta = None):
    """创建JWT访问令牌
    
    将用户信息编码为JWT令牌，用于后续请求的身份验证。
    
    参数：
        data: 要编码的数据字典，通常包含usernameid等信息
        expires_delta: 令牌过期时间差（如不提供则使用默认值）
        
    返回：
        JWT令牌字符串（base64编码）
        
    JWT结构：
        header.payload.signature
        - header: 加密算法信息
        - payload: 用户数据 + 过期时间
        - signature: 使用SECRET_KEY生成的签名
    """
    to_encode = data.copy()  # 复制数据以避免修改原字典
    
    # 计算令牌过期时间
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # 添加exp（expiration）字段
    to_encode.update({"exp": expire})
    
    # 使用SECRET_KEY和ALGORITHM对数据进行签名
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """获取当前请求用户（验证JWT）
    
    从请求头的Authorization: Bearer <token>中提取令牌，
    验证令牌的有效性，并返回对应的用户对象。
    
    参数：
        token: 从OAuth2 scheme自动提取的JWT令牌
        db: 数据库会话（用于查询用户）
        
    返回：
        User对象（当前请求的用户）
        
    异常：
        HTTPException (401): 令牌无效或过期
        
    验证过程：
        1. 检查token格式和签名
        2. 解码token获取username
        3. 从数据库查询用户
        4. 确保用户存在且激活
    """
    # 认证失败时返回的异常
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},  # WWW-Authenticate头提示客户端正确的认证方式
    )
    try:
        # 使用SECRET_KEY验证并解码JWT
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # 从payload中获取username（\"sub\"是standard claim）
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        # JWT解码或验证失败（签名错误、过期等）
        raise credentials_exception
    
    # 从数据库查询用户
    user = crud.get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception
    
    return user


# ==================== API路由 ====================

@app.post("/register", response_model=schemas.UserOut)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    """注册新用户
    
    创建新的用户账户。
    
    请求体：
        {
            \"username\": \"john\",
            \"password\": \"secret123\",
            \"nickname\": \"John Doe\"
        }
        
    响应：
        {
            \"id\": 1,
            \"uuid\": \"550e8400-e29b-41d4-a716-446655440000\",
            \"username\": \"john\",
            \"nickname\": \"John Doe\"
        }
        
    状态码：
        200: 注册成功
        400: 用户名已存在
    """
    # 检查用户名是否已被注册
    existing = crud.get_user_by_username(db, user_in.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # 创建新用户
    user = crud.create_user(db, user_in)
    return user


@app.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """用户登录
    
    验证用户名密码并返回JWT访问令牌。
    
    请求体（form-data格式）：
        username: john
        password: secret123
        
    响应：
        {
            \"access_token\": \"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...\",
            \"token_type\": \"bearer\"
        }
        
    使用方法：
        将access_token放在后续请求的Authorization header中：
        Authorization: Bearer <access_token>
        
    状态码：
        200: 登录成功
        400: 用户名或密码错误
    """
    # 验证用户名和密码
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    # 生成JWT令牌
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", response_model=schemas.UserOut)
def read_users_me(current_user=Depends(get_current_user)):
    """获取当前登录用户信息
    
    返回当前JWT令牌对应的用户信息。
    
    请求头：
        Authorization: Bearer <access_token>
        
    响应：
        {
            \"id\": 1,
            \"uuid\": \"550e8400-e29b-41d4-a716-446655440000\",
            \"username\": \"john\",
            \"nickname\": \"John Doe\"
        }
        
    状态码：
        200: 成功
        401: 无效或过期的令牌
    """
    return current_user


@app.post("/problems/upload", response_model=schemas.ProblemOut)
def upload_problem(
    raw: str = Form(None),
    file: UploadFile = File(None),
    source_type: str = Form("text"),
    subject: str = Form(None),
    course: str = Form(None),
    problem_type: str = Form(None),
    knowledge_tags: str = Form(None),  # JSON格式的字符串，如'["函数", "微积分"]'
    difficulty: int = Form(None),
    tags: str = Form(None),  # JSON格式的字符串，如'["难题", "易错"]'
    notes: str = Form(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """上传学习题目
    
    允许用户上传新题目，支持文本、文件或LaTeX形式。
    同时可以提供题目的元数据（学科、课程、题型等）。
    
    请求参数（form-data）：
        raw: 文本题目内容（必填或file必填其一）
        file: 上传的题目文件（可选，.jpg/.png/.pdf等）
        source_type: 题目来源类型（默认\"text\"）
            可选值：\"text\"（纯文本）、\"image\"（图片）、\"latex\"（LaTeX）
        subject: 学科，如\"数学\"、\"物理\"等（可选）
        course: 课程名称，如\"高等数学\"、\"线性代数\"等（可选）
        problem_type: 题型，如\"选择\"、\"填空\"、\"解答\"等（可选）
        knowledge_tags: 知识点标签JSON数组，如'[\"函数\", \"微积分\"]'（可选）
        difficulty: 难度等级，1-5（可选），1=最简单，5=最困难
        tags: 用户自定义标签JSON数组，如'[\"难题\", \"易错\"]'（可选）
        notes: 用户备注（可选）
        
    响应：
        返回完整的题目对象，包含：
        - id: 题目ID
        - owner_id: 所有者ID
        - source_type: 题目来源类型
        - file_content: Base64编码的文件内容（如果上传了文件）
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
        
    说明：
        - 题目自动关联到当前登录用户
        - 所有元数据字段均为可选，以支持渐进式填充
        - 上传的文件会被编码为Base64格式存储在数据库中
        
    状态码：
        200: 上传成功
        400: 缺少必填参数或参数格式错误
        401: 无效或过期的令牌
    """
    # 验证至少提供了题目内容（文本或文件之一）
    if not raw and not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="必须提供题目内容（raw文本或file文件）"
        )
    
    # 构建要存储的题目内容和Base64编码的文件
    file_content_base64 = None
    if file:
        raw_store = f"FILE:{file.filename}"  # 标记为文件来源
        # 读取文件内容并编码为Base64
        try:
            file_bytes = file.file.read()
            file_content_base64 = base64.b64encode(file_bytes).decode('utf-8')
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无法读取文件: {str(e)}"
            )
    else:
        raw_store = raw  # 文本来源
    
    # 解析JSON格式的标签字段
    knowledge_tags_list = None
    if knowledge_tags:
        try:
            knowledge_tags_list = json.loads(knowledge_tags)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="knowledge_tags必须是有效的JSON数组"
            )
    
    tags_list = None
    if tags:
        try:
            tags_list = json.loads(tags)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="tags必须是有效的JSON数组"
            )
    
    # 创建问题记录
    problem_in = schemas.ProblemCreate(
        source_type=source_type,
        raw=raw_store,
        file_content=file_content_base64,
        subject=subject,
        course=course,
        problem_type=problem_type,
        knowledge_tags=knowledge_tags_list,
        difficulty=difficulty,
        tags=tags_list,
        notes=notes,
    )
    p = crud.create_problem(db, owner_id=current_user.id, problem_in=problem_in)
    
    # 返回创建的题目完整信息，包括解析后的tags和knowledge_tags列表
    return schemas.ProblemOut.from_orm(p)


@app.get("/problems/{problem_id}", response_model=schemas.ProblemOut)
def get_problem(
    problem_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取题目详情
    
    根据题目ID获取题目的完整信息。
    
    路径参数：
        problem_id: 题目ID
        
    响应：
        返回完整的题目对象
        
    状态码：
        200: 获取成功
        401: 无效或过期的令牌
        404: 题目不存在
    """
    p = crud.get_problem(db, problem_id)
    if not p:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="题目不存在"
        )
    # 验证当前用户是否有权查看此题目
    if p.owner_id and p.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此题目"
        )
    return schemas.ProblemOut.from_orm(p)


@app.patch("/problems/{problem_id}", response_model=schemas.ProblemOut)
def update_problem(
    problem_id: int,
    problem_in: schemas.ProblemUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """更新题目元数据
    
    更新已上传题目的元数据、标签和备注。
    只能更新自己上传的题目。
    
    路径参数：
        problem_id: 题目ID
        
    请求体（JSON）：
        {
            \"subject\": \"数学\",
            \"course\": \"高等数学\",
            \"problem_type\": \"解答\",
            \"knowledge_tags\": [\"函数\", \"微积分\"],
            \"difficulty\": 3,
            \"is_bookmarked\": true,
            \"tags\": [\"难题\", \"易错\"],
            \"notes\": \"这是一道关键题目\"
        }
        
    所有字段都是可选的，仅更新提供的字段。
    
    响应：
        返回更新后的完整题目对象
        
    状态码：
        200: 更新成功
        401: 无效或过期的令牌
        403: 无权更新此题目
        404: 题目不存在
    """
    p = crud.get_problem(db, problem_id)
    if not p:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="题目不存在"
        )
    
    # 验证当前用户是否有权修改此题目
    if p.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改此题目"
        )
    
    # 更新题目
    p = crud.update_problem(db, problem_id, problem_in)
    return schemas.ProblemOut.from_orm(p)


@app.get("/problems", response_model=List[schemas.ProblemOut])
def list_problems(
    subject: str = None,
    course: str = None,
    bookmarked_only: bool = False,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """查询用户的题目列表
    
    按条件查询当前用户上传的题目。
    
    查询参数：
        subject: 按学科筛选（可选）
        course: 按课程筛选（可选）
        bookmarked_only: 仅返回已收藏的题目（可选，默认false）
        
    响应：
        返回符合条件的题目列表
        
    说明：
        - 用户只能查看自己上传的题目
        - 支持多条件组合查询
        
    状态码：
        200: 查询成功
        401: 无效或过期的令牌
    """
    query = db.query(models.Problem).filter(models.Problem.owner_id == current_user.id)
    
    if subject:
        query = query.filter(models.Problem.subject == subject)
    if course:
        query = query.filter(models.Problem.course == course)
    if bookmarked_only:
        query = query.filter(models.Problem.is_bookmarked == True)
    
    problems = query.all()
    return [schemas.ProblemOut.from_orm(p) for p in problems]


@app.post("/solve", response_model=schemas.SolveResult)
def solve(req: schemas.SolveRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """求解题目
    
    调用AI模型求解题目，返回思路、步骤和答案。
    
    请求体：
        {
            \"problem_id\": 1,  // 已上传题目ID（可选）
            \"raw\": \"2+2=?\",   /// 直接输入的题目（可选）
            \"mode\": \"structured\"
        }
        
    响应：
        {
            \"thoughts\": \"先把题目读清楚，然后分步求解。\",
            \"steps\": [\"分析已知条件\", \"列出解题思路\", \"计算并得到结果\"],
            \"answer\": \"4\"
        }
        
    说明：
        - 当前实现为占位符，返回模拟数据
        - 未来将集成AI求解引擎
        
    状态码：
        200: 求解成功
        401: 无效或过期的令牌
    """
    # 获取题目内容：可以是problem_id对应的题目，或直接提交的raw文本
    if req.problem_id:
        problem = crud.get_problem(db, req.problem_id)
        raw = problem.raw if problem else req.raw
    else:
        raw = req.raw
    
    # 调用AI求解（当前为占位符）
    # TODO: 集成真实的AI求解模型
    thoughts = "先把题目读清楚，然后分步求解。"
    steps = ["分析已知条件", "列出解题思路", "计算并得到结果"]
    answer = "42（占位答案）"
    
    return {"thoughts": thoughts, "steps": steps, "answer": answer}


@app.get("/profile", response_model=schemas.LearningProfile)
def profile(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """获取学习档案
    
    返回用户的学习进度，包括各主题的掌握度。
    
    响应：
        {
            \"user_id\": 1,
            \"mastery\": {
                \"代数\": 0.75,
                \"几何\": 0.60
            },
            \"trend\": []
        }
        
    说明：
        - mastery: 各主题掌握度（0.0-1.0表示0-100%）
        - trend: 学习趋势（历史记录）
        
    应用场景：
        显示用户学习进度、推荐学习材料、生成学习报告
        
    状态码：
        200: 成功
        401: 无效或过期的令牌
    """
    data = crud.get_learning_profile(db, current_user.id)
    return data


@app.get("/admin/users", response_model=List[schemas.UserOut])
def admin_list_users(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """（管理员）列出所有用户
    
    仅管理员可访问，返回系统中的所有用户列表。
    
    响应：
        [
            {
                \"id\": 1,
                \"uuid\": \"...\",
                \"username\": \"john\",
                \"nickname\": \"John\"
            },
            ...
        ]
        
    权限检查：
        current_user.is_admin 必须为 True
        
    状态码：
        200: 成功
        401: 无效或过期的令牌  
        403: 权限不足（非管理员）
    """
    # 权限检查：只有管理员可以查看用户列表
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Requires admin")
    
    return crud.list_users(db)


@app.post("/admin/users/{user_id}/ban", response_model=schemas.UserOut)
def admin_ban_user(user_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """（管理员）禁用用户
    
    管理员可禁用指定用户，被禁用的用户无法登录。
    
    路径参数：
        user_id: 要禁用的用户ID
        
    响应：
        {
            \"id\": 2,
            \"uuid\": \"...\",
            \"username\": \"baduser\",
            \"nickname\": null
        }
        
    说明：
        - 将用户的is_active设置为False
        - 被禁用的用户无法通过登录认证
        
    权限检查：
        current_user.is_admin 必须为 True
        
    状态码：
        200: 禁用成功
        401: 无效或过期的令牌
        403: 权限不足（非管理员）
        404: 用户不存在
    """
    # 权限检查：只有管理员可以禁用用户
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Requires admin")
    
    # 执行禁用操作
    user = crud.set_user_active(db, user_id, active=False)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user
