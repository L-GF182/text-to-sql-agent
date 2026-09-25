import os
import gradio as gr

#首次启动自动初始化向量库
if not os.path.exists("./chroma_db"):
    print("🔄 首次启动，正在初始化向量库（需要下载嵌入模型，约400MB）...")
    from schema_rag import init_vector_store
    init_vector_store()
    print("✅ 向量库初始化完成")

#导入已有功能
from langgraph_agent import chat_with_memory          # 多轮对话（带记忆）
# from sql_agent_with_retry import run_agent_with_retry  # 单轮查询（带缓存），备用


#聊天回调
def chat_fn(message, history):
    """
    默认走多轮对话（chat_with_memory），带上下文记忆。
    如果想体验单轮查询（带 Redis 缓存），把下面 return 换成 run_agent_with_retry(message) 即可。
    """
    try:
        return chat_with_memory(message, thread_id="gradio_demo")
        # return run_agent_with_retry(message)  # ← 单轮查询模式，取消注释即可
    except Exception as e:
        return f"抱歉，出错了：{str(e)}"


#构建 Gradio 界面
# ========== 构建 Gradio 界面 ==========
demo = gr.ChatInterface(
    fn=chat_fn,
    title="🤖 智能数据分析 Agent",
    description=(
        "基于 **LangChain + 通义千问**，用自然语言查询数据库。\n\n"
        "支持功能：RAG 检索增强 / SQL 安全护栏 / 自愈重试 / Redis 缓存 / 多轮对话记忆"
    ),
    examples=[
        "有多少首歌曲？",
        "有哪些艺术家？",
        "第一个艺术家的专辑有哪些？",
        "有多少张专辑？",
        "删除所有歌曲",
    ],
)


#启动
if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
    )