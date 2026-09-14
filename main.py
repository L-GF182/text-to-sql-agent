from langgraph_agent import chat_with_memory
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sql_agent_with_retry import run_agent_with_retry # 导入之前创建的 agent

app = FastAPI(title="Text-to-SQL Agent API")

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str

@app.post("/query", response_model=QueryResponse)
async def query_database(request: QueryRequest):
    try:
        #使用带缓存和重试的调用
        answer =run_agent_with_retry(request.question)
        return QueryResponse(answer=answer)
    except Exception as e:
        import traceback
        print("\n❌ [详细错误堆栈]:")
        traceback.print_exc()  # 这行会打印出真正的报错原因
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Text-to-SQL Agent is running!"}

# ---------- 多轮对话接口 ----------
class ChatRequest(BaseModel):
    question: str
    session_id: str = "default"

class ChatResponse(BaseModel):
    answer: str
    session_id: str

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        answer = chat_with_memory(request.question, request.session_id)
        return ChatResponse(answer=answer, session_id=request.session_id)
    except Exception as e:
        import traceback
        print("\n❌ [chat 详细错误堆栈]:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))