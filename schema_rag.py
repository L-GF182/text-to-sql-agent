import os
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.utilities import SQLDatabase
from langchain_core.documents import Document

# 初始化数据库连接
db = SQLDatabase.from_uri("sqlite:///Chinook.db")

# 使用中文嵌入模型（第一次运行时会自动下载，约400MB）
embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-zh-v1.5")

# 向量库持久化目录
PERSIST_DIR = "./chroma_db"

def build_schema_documents():
    """提取数据库所有表的结构，生成文档"""
    table_names = db.get_usable_table_names()
    docs = []
    for name in table_names:
        table_info = db.get_table_info([name])
        doc = Document(
            page_content=table_info,
            metadata={"table_name": name}
        )
        docs.append(doc)
    return docs

def init_vector_store():
    """初始化向量库（首次运行必须执行一次）"""
    docs = build_schema_documents()
    vector_store = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=PERSIST_DIR
    )
    print(f"✅ 向量库初始化完成，共处理 {len(docs)} 张表。")
    return vector_store

# 模块级缓存，只加载一次
_vector_store_cache = None

def load_vector_store():
    """加载已有向量库（模块级缓存，只加载一次）"""
    global _vector_store_cache
    if _vector_store_cache is None:
        _vector_store_cache = Chroma(
            persist_directory=PERSIST_DIR,
            embedding_function=embeddings
        )
    return _vector_store_cache

def retrieve_relevant_schemas(question: str, top_k: int = 5):
    """根据用户问题检索最相关的表结构"""
    vector_store = load_vector_store()
    results = vector_store.similarity_search(question, k=top_k)
    schemas = []
    for doc in results:
        schemas.append({
            "table_name": doc.metadata["table_name"],
            "schema_info": doc.page_content
        })
    return schemas