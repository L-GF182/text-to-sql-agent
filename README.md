# 智能数据分析 Agent（Text-to-SQL）

基于 LangChain + 通义千问的智能数据分析助手。用户通过自然语言提问，Agent 自动生成 SQL 并查询数据库返回结果，全程无需手写 SQL。

## ✨ 核心功能

- **自然语言转 SQL**：用中文提问（如“一共有多少首歌曲？”），Agent 自动生成 SQL 并返回结果。
- **RAG 检索增强**：基于 `bge-small-zh` 向量检索，动态召回最相关表结构，提升复杂查询准确率。
- **SQL 安全护栏**：自定义 `safe_sql_query` 工具，配合 `sqlparse` 解析，拦截所有非 SELECT 操作（如 DELETE、DROP）。
- **自愈重试机制**：SQL 执行出错时，Agent 根据错误反馈自动修正，最多重试 3 次。
- **Redis 缓存 + 熔断容错**：相同问题命中缓存，响应时间从 5s 降至 50ms；Redis 不可用时服务照常运行。
- **多轮对话记忆**：基于 LangGraph + SQLite 持久化，支持上下文追问（如“第一个艺术家的专辑有哪些？”）。
- **FastAPI 接口**：提供 RESTful API，自动生成 Swagger 文档，支持在线测试。

## 🛠 技术栈

- **语言**：Python 3.12
- **大模型**：通义千问（qwen3-max-2026-01-23）
- **Agent 框架**：LangChain、LangGraph
- **Web 框架**：FastAPI、Uvicorn
- **数据库**：SQLite（Chinook 示例库）
- **向量库**：Chroma
- **缓存**：Redis
- **其他**：sqlparse、HuggingFaceEmbeddings、python-dotenv

## 📁 项目结构

```text
text-to-sql-agent/
├── ai_data_analyst.py          # 核心 Agent + RAG Prompt + 安全校验
├── sql_agent_with_retry.py     # 对外唯一入口：缓存 + RAG + 重试
├── cache_manager.py            # Redis 缓存 + 熔断容错
├── schema_rag.py               # RAG 向量检索
├── langgraph_agent.py          # LangGraph 多轮对话记忆
├── main.py                     # FastAPI 接口
├── download_db.py              # 数据库下载脚本
├── Chinook.db                  # SQLite 示例数据库
├── requirements.txt            # 依赖清单
├── .env                        # 环境变量（不提交）
└── .gitignore                  # Git 忽略规则
```

## 🚀 本地运行

### 1. 克隆项目并安装依赖
```bash
git clone https://github.com/L-GF182/text-to-sql-agent.git
cd text-to-sql-agent
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt
```
### 2. 配置环境变量
在项目根目录创建 .env 文件，填入你的通义千问 API 信息：
```env
OPENAI_API_KEY=sk-你的API密钥
OPENAI_BASE_URL=https://你的专属地址/compatible-mode/v1
```
### 3. 下载数据库并初始化向量库
```bash
# 下载 Chinook 示例数据库
python download_db.py
# 初始化向量库（首次运行必须执行一次）
python -c "from schema_rag import init_vector_store; init_vector_store()"
```
### 4. 启动服务
```bash
uvicorn main:app --reload
```
服务启动后，访问 http://127.0.0.1:8000/docs 查看并测试接口。

## 📡 API 示例

### 单轮查询
```bash
curl -X POST "http://127.0.0.1:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "一共有多少首歌曲？"}'
```
### 多轮对话
```bash
# 第一轮
curl -X POST "http://127.0.0.1:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"question": "有哪些艺术家？", "session_id": "user1"}'
# 第二轮（session_id 必须相同）
curl -X POST "http://127.0.0.1:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"question": "第一个艺术家的专辑有哪些？", "session_id": "user1"}'
```
## 📄 License
MIT