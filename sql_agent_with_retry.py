import logging
from ai_data_analyst import agent_executor, build_rag_prompt
from cache_manager import get_cached_answer, set_cached_answer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_agent_with_retry(question: str, max_retries: int = 3) -> str:
    """带缓存 + RAG + 重试的 Agent 调用（对外唯一入口）"""

    # 1. 先查缓存（读取失败不影响主流程）
    try:
        cached_answer = get_cached_answer(question)
        if cached_answer:
            print(f"✅ 缓存命中: {question}")
            return cached_answer
    except Exception as e:
        print(f"⚠️ 读取缓存失败（忽略，继续调用 Agent）: {e}")

    print(f"⏳ 缓存未命中，调用 Agent: {question}")

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            # 2. 调用 Agent（使用 RAG 增强的 Prompt）
            response = agent_executor.invoke({"input": build_rag_prompt(question)})
            answer = response["output"]

            # 3. 写入缓存（失败不影响返回）
            try:
                set_cached_answer(question, answer)
            except Exception as e:
                print(f"⚠️ 写入缓存失败（忽略，直接返回答案）: {e}")

            # 4. 关键！成功必须 return
            return answer

        except Exception as e:
            logger.error(f"Attempt {attempt} failed: {e}")
            last_error = e
            continue

    # 所有重试都失败才抛异常
    raise last_error or Exception("Agent 执行失败")