import os
import logging
from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_classic.agents import AgentExecutor, create_openai_tools_agent
import sqlparse
from schema_rag import retrieve_relevant_schemas

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化 LLM 和数据库
llm = ChatOpenAI(
    temperature=0.1,
    model="qwen3-max-2026-01-23",
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    openai_api_base=os.getenv("OPENAI_BASE_URL"),
)
db = SQLDatabase.from_uri("sqlite:///Chinook.db")


# SQL 安全校验函数
def validate_sql(sql: str) -> bool:
    """仅允许 SELECT 查询"""
    if not sql or not sql.strip():
        return False
    parsed = sqlparse.parse(sql)
    if not parsed:
        return False
    return parsed[0].get_type().upper() == "SELECT"


# 集成 RAG：构建聚焦的 Prompt
def build_rag_prompt(question: str) -> str:
    """根据用户问题，通过 RAG 检索相关表，构建聚焦的 Prompt"""
    relevant_tables = retrieve_relevant_schemas(question, top_k=5)
    print(f"🔍 检索到的表: {[t['table_name'] for t in relevant_tables]}")

    schema_context = "\n\n".join([
        f"表名: {t['table_name']}\n结构信息:\n{t['schema_info']}"
        for t in relevant_tables
    ])

    prompt = f"""
你是一个SQLite专家。请只使用以下提供的相关表结构来回答用户的问题。
如果问题无法基于这些表回答，请说明。

【相关表结构】
{schema_context}

【用户问题】
{question}

请生成SQL并返回查询结果。
"""
    return prompt


# 自定义安全工具
@tool
def safe_sql_query(query: str) -> str:
    """执行 SQL 查询，仅允许 SELECT 语句"""
    if not validate_sql(query):
        return "错误：非法的 SQL 操作，仅允许 SELECT 查询。"
    try:
        result = db.run(query)
        return result
    except Exception as e:
        return f"SQL 执行错误：{str(e)}"


# 构建 Toolkit 并替换默认的 sql_db_query 工具
toolkit = SQLDatabaseToolkit(db=db, llm=llm)
tools = toolkit.get_tools()

for i, t in enumerate(tools):
    if t.name == "sql_db_query":
        tools[i] = safe_sql_query
        break

# 定义 Prompt
prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "你是一个 SQLite 专家。请根据用户的问题，使用提供的工具查询数据库，"
        "然后返回最终答案。你只能执行 SELECT 查询，不得修改数据库。"
        "如果问题无法基于数据库回答，请说明。"
    ),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# 创建 Agent
agent = create_openai_tools_agent(llm, tools, prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=5,
)