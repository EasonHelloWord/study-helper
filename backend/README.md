# Study Helper Backend

一个基于 FastAPI 的在线学习辅助平台后端，支持题目上传、知识点管理和学习进度追踪。

## 功能特性

- 🔐 **JWT 身份认证**：安全的用户登录和授权
- 📤 **多格式题目上传**：支持文本、图片、LaTeX 格式，Base64 编码存储
- 🏷️ **智能元数据管理**：科目、课程、难度、知识点标签等
- 🔍 **灵活查询筛选**：按科目、课程、标签、收藏状态快速检索
- 📊 **学习进度追踪**：记录做题情况和知识点掌握度
- 👤 **用户管理**：个人资料管理、管理员后台

## 快速开始

### 环境要求

- Python 3.9+
- SQLite（已内置）

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动服务

```bash
python main.py
```

服务默认运行在 `http://localhost:8000`

访问 API 文档：http://localhost:8000/docs

## API 使用示例

### 1. 用户注册

```bash
curl -X POST "http://localhost:8000/api/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "secure_password123",
    "email": "john@example.com"
  }'
```

**响应：**
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "is_active": true,
  "is_admin": false
}
```

### 2. 用户登录

```bash
curl -X POST "http://localhost:8000/api/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=john_doe&password=secure_password123"
```

**响应：**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 3. 上传题目（带文件）

```bash
curl -X POST "http://localhost:8000/api/problems" \
  -H "Authorization: Bearer {access_token}" \
  -F "title=微积分基础题" \
  -F "description=求 f(x) = x^2 的导数" \
  -F "subject=数学" \
  -F "course=微积分" \
  -F "problem_type=计算题" \
  -F "knowledge_tags=[\"导数\",\"微积分\"]" \
  -F "difficulty=中等" \
  -F "file=@problem_image.png"
```

**响应：**
```json
{
  "id": 1,
  "title": "微积分基础题",
  "description": "求 f(x) = x^2 的导数",
  "subject": "数学",
  "course": "微积分",
  "problem_type": "计算题",
  "knowledge_tags": ["导数", "微积分"],
  "difficulty": "中等",
  "source_type": "file",
  "owner_id": 1,
  "created_at": "2024-01-15T10:30:45.123456",
  "updated_at": "2024-01-15T10:30:45.123456",
  "is_bookmarked": false,
  "tags": [],
  "notes": ""
}
```

### 4. 查询题目（带筛选）

```bash
curl -X GET "http://localhost:8000/api/problems?subject=数学&course=微积分&difficulty=中等" \
  -H "Authorization: Bearer {access_token}"
```

**响应：**
```json
[
  {
    "id": 1,
    "title": "微积分基础题",
    "description": "求 f(x) = x^2 的导数",
    "subject": "数学",
    "course": "微积分",
    "problem_type": "计算题",
    "knowledge_tags": ["导数", "微积分"],
    "difficulty": "中等",
    "source_type": "file",
    "owner_id": 1,
    "created_at": "2024-01-15T10:30:45.123456",
    "updated_at": "2024-01-15T10:30:45.123456",
    "is_bookmarked": false,
    "tags": [],
    "notes": ""
  }
]
```

### 5. 获取单个题目（包含文件内容）

```bash
curl -X GET "http://localhost:8000/api/problems/1" \
  -H "Authorization: Bearer {access_token}"
```

**响应：** 包含 `file_content` 字段（Base64 编码的文件数据）

### 6. 更新题目元数据

```bash
curl -X PUT "http://localhost:8000/api/problems/1" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "微积分进阶题",
    "difficulty": "困难",
    "is_bookmarked": true,
    "notes": "需要复习链式法则"
  }'
```

### 7. 记录做题结果

```bash
curl -X POST "http://localhost:8000/api/problems/1/solve" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "is_correct": true,
    "time_spent_seconds": 180
  }'
```

### 8. 获取学习进度

```bash
curl -X GET "http://localhost:8000/api/user/profile" \
  -H "Authorization: Bearer {access_token}"
```

## 项目结构

```
backend/
├── main.py              # FastAPI 应用主文件，包含所有 API 端点
├── models.py            # SQLAlchemy ORM 数据模型
├── schemas.py           # Pydantic 数据验证模式
├── crud.py              # 数据库 CRUD 操作
├── database.py          # 数据库连接和配置
├── db.sqlite3           # SQLite 数据库文件
├── requirements.txt     # 生产环境依赖
├── dev-requirements.txt # 开发环境依赖
└── README.md            # 本文件
```

## 数据库架构

### Users 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 用户 ID（主键） |
| username | String | 用户名（唯一） |
| email | String | 邮箱（唯一） |
| hashed_password | String | 密码哈希值（PBKDF2-SHA256） |
| is_active | Boolean | 是否激活 |
| is_admin | Boolean | 是否管理员 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

### Problems 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 题目 ID（主键） |
| title | String | 题目标题 |
| description | String | 题目描述 |
| subject | String | 科目（数学、物理、化学等） |
| course | String | 课程名称 |
| problem_type | String | 题目类型（选择题、计算题、证明题等） |
| knowledge_tags | JSON | 知识点标签列表 |
| difficulty | String | 难度等级（简单、中等、困难） |
| source_type | String | 来源类型（text、image、latex） |
| file_content | Text | Base64 编码的文件内容 |
| owner_id | Integer | 上传者用户 ID（外键） |
| is_bookmarked | Boolean | 是否收藏 |
| tags | JSON | 自定义标签列表 |
| notes | String | 个人笔记 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

### Attempts 表（做题记录）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 记录 ID（主键） |
| problem_id | Integer | 题目 ID（外键） |
| user_id | Integer | 用户 ID（外键） |
| is_correct | Boolean | 是否正确 |
| time_spent_seconds | Integer | 耗时（秒） |
| attempted_at | DateTime | 做题时间 |

### TopicMastery 表（知识点掌握度）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 记录 ID（主键） |
| user_id | Integer | 用户 ID（外键） |
| topic | String | 知识点名称 |
| mastery_level | Float | 掌握度（0-100） |
| last_updated | DateTime | 最后更新时间 |

## 身份认证流程

1. **注册**：用户提供用户名、邮箱、密码
2. **密码处理**：使用 PBKDF2-SHA256 哈希存储密码（不存储明文）
3. **登录**：验证用户名和密码，返回 JWT token
4. **Token 信息**：
   - 算法：HS256
   - 有效期：7 天
5. **API 请求**：在 Authorization 头中传入 Bearer token
6. **验证**：服务器解析 JWT 获取用户信息

**示例请求头：**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqb2huX2RvZSIsImV4cCI6MTcwNTM0ODI0NX0.xxx
```

## 文件存储机制

### 为什么选择 Base64 编码？

1. **数据库原生**：无需维护独立文件系统
2. **便于迁移**：整个数据库可作为单一文件备份
3. **便于 AI 处理**：Base64 字符串可直接传入 AI 模型
4. **无 OCR 依赖**：用户上传即存储，后续交由 AI 识别

### 文件编码流程

```
用户上传文件 → 读取二进制内容 → Base64 编码 → 存储到数据库 Text 字段
```

**Python 示例：**
```python
import base64

# 编码：文件 → Base64 字符串
file_bytes = open('problem.png', 'rb').read()
base64_str = base64.b64encode(file_bytes).decode('utf-8')
# 存储 base64_str 到数据库

# 解码：Base64 字符串 → 文件
decoded_bytes = base64.b64decode(base64_str)
open('output.png', 'wb').write(decoded_bytes)
```

### 存储大小估计

- 10KB 图片 → ~13.3KB Base64（增大约 33%）
- 100KB 图片 → ~133KB Base64

## 环境配置

### 必需环境变量

在 `.env` 文件中配置（或直接在 `main.py` 中修改）：

```env
DATABASE_URL=sqlite:///./db.sqlite3
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_DAYS=7
```

**生成安全的 SECRET_KEY：**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## 依赖包

**生产环境** (`requirements.txt`)：
- fastapi
- uvicorn
- sqlalchemy
- pydantic
- python-multipart
- pyjwt
- passlib
- bcrypt
- python-dotenv

**开发环境** (`dev-requirements.txt`)：
- 包括了生产环境的所有依赖

## 部署指南

### 开发环境

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动开发服务器
python main.py
# 或使用 Uvicorn 直接运行
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 生产环境（使用 Gunicorn）

```bash
# 安装 Gunicorn
pip install gunicorn

# 启动生产服务器
gunicorn -w 4 -b 0.0.0.0:8000 main:app
```

**Gunicorn 参数说明：**
- `-w 4`：使用 4 个工作进程
- `-b 0.0.0.0:8000`：绑定到所有网卡，端口 8000

### Docker 部署（可选）

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**构建和运行：**
```bash
docker build -t study-helper-backend .
docker run -p 8000:8000 study-helper-backend
```

## 性能优化建议

### 1. 数据库索引

在高频查询字段上添加索引：

```python
# models.py 中的 Problem 表
subject = Column(String, index=True)
course = Column(String, index=True)
owner_id = Column(Integer, ForeignKey('users.id'), index=True)
difficulty = Column(String, index=True)
```

### 2. 查询优化

- 分页查询大量题目（avoid N+1 issue）
- 使用 join 预加载关联数据

### 3. 缓存策略

- 使用 Redis 缓存热点数据（知识点统计、用户进度等）
- 题目列表使用客户端缓存

### 4. Base64 优化

- 大文件（>5MB）考虑分块上传
- 或改用 S3/对象存储，仅在数据库存储 URL 引用

## 常见问题

### Q1: 如何添加新的知识点标签？
**A:** 标签是自由格式，上传时直接指定即可。无需预定义。

### Q2: 如何导出所有题目数据？
**A:** 可以直接复制 `db.sqlite3` 文件，或通过 API 进行数据导出。

### Q3: Base64 文件内容太大怎么办？
**A:** 考虑以下方案：
- 压缩文件后再 Base64 编码
- 迁移至对象存储（S3/阿里云 OSS），存储 URL
- 按学期/年份分库

### Q4: 如何实现权限控制（不同用户看不同题目）？
**A:** 修改 `list_problems()` 中的查询条件，过滤 `owner_id`：
```python
query = query.filter(Problem.owner_id == current_user.id)
```

### Q5: 如何重置密码？
**A:** 需要实现额外的忘记密码流程（邮件验证链接等），当前版本不支持。

## 开发规范

### API 命名约定

- `GET /api/problems` - 列表查询
- `GET /api/problems/{id}` - 获取详情
- `POST /api/problems` - 创建
- `PUT /api/problems/{id}` - 更新
- `DELETE /api/problems/{id}` - 删除

### 错误处理

所有错误返回标准格式：

```json
{
  "detail": "错误消息描述"
}
```

HTTP 状态码：
- `200` - 成功
- `201` - 新建成功
- `400` - 请求参数错误
- `401` - 未授权（无效 token）
- `403` - 禁止访问（权限不足）
- `404` - 资源不存在
- `500` - 服务器错误

### 代码风格

- 使用 Type Hints（Python 3.9+）
- 遵循 PEP 8 规范
- 函数文档字符串

## 功能路线图

### v1.0 (已完成)
- ✅ 用户认证系统
- ✅ 题目上传（多格式）
- ✅ Base64 文件存储
- ✅ 题目查询和筛选
- ✅ 基础元数据管理

### v2.0 (计划中)
- 🔲 题目分类树结构
- 🔲 批量导入（Excel、CSV）
- 🔲 题目推荐算法
- 🔲 学习路径规划
- 🔲  小组协作功能

### v3.0 (未来)
- 🔲 AI 辅导助手集成
- 🔲  自动生成学习报告
- 🔲  移动 APP 支持

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交 Issue 或 PR。

---

**最后更新**: 2024 年 1 月 15 日
