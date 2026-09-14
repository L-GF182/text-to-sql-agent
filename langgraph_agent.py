import os
import sqlite3
from dotenv import load_dotenv
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import HumanMessage, AIMessage
from ai_data_analyst import agent_executor, build_rag_prompt

load_dotenv()


def call_agent(state: MessagesState):
    """LangGraph 节点：调用 Agent，并把历史对话作为上下文"""
    messages = state["messages"]

    # 把历史对话拼成一个上下文文本，附加在最新问题前面
    history_text = ""
    for msg in messages[:-1]:  # 排除最新一条
        if isinstance(msg, HumanMessage):
            history_text += f"用户: {msg.content}\n"
        elif isinstance(msg, AIMessage):
            history_text += f"助手: {msg.content}\n"

    # 取最新问题
    latest_question = messages[-1].content

    # 如果有历史，拼接历史
    if history_text:
        full_input = f"【历史对话】\n{history_text}\n【当前问题】\n{latest_question}"
    else:
        full_input = latest_question

    # 调用 RAG Agent
    response = agent_executor.invoke({"input": build_rag_prompt(full_input)})
    answer = response["output"]

    return {"messages": [AIMessage(content=answer)]}


# 构建状态图
graph = StateGraph(MessagesState)
graph.add_node("agent", call_agent)
graph.add_edge(START, "agent")
graph.add_edge("agent", END)

# 使用 SQLite 持久化对话记忆
_conn = sqlite3.connect("checkpoints.db", check_same_thread=False)
memory = SqliteSaver(_conn)
app = graph.compile(checkpointer=memory)


def chat_with_memory(question: str, thread_id: str = "default") -> str:
    """
    带记忆的对话接口
    :param question: 用户问题
    :param thread_id: 会话ID（不同用户/不同会话用不同ID）
    :return: Agent 的回答
    """
    config = {"configurable": {"thread_id": thread_id}}
    result = app.invoke(
        {"messages": [HumanMessage(content=question)]},
        config=config
    )
    return result["messages"][-1].content