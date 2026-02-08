# Study Helper 后端

简单的 FastAPI 后端骨架，包含：

- 注册/登录（JWT）
- 用户资料
- 题目上传占位接口（文件/文本）
- 解题占位接口（将来接入大模型）
- 学习画像占位数据
- 管理端：列用户、封禁

运行（建议在虚拟环境中）：

```bash
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```

数据库使用 SQLite：`backend/db.sqlite3`，models 会在首次运行时创建。

说明：目前解析/解题为占位实现，建议在 `main.solve` 中接入 AI 模型服务（本地或远端 API）。
