import redis
import hashlib
import json
import logging
import time

logger = logging.getLogger(__name__)

#全局状态
_redis_client = None          # Redis 客户端（懒加载）
_redis_failed_until = 0       # 熔断截止时间戳（在此时间之前不再尝试连接）
FAIL_COOLDOWN = 60            # 熔断冷却时间（秒）


#内部函数
def _get_redis_client():
    """
    获取 Redis 客户端（懒加载 + 熔断机制）。
    - 熔断期内：直接返回 None，不尝试连接
    - 首次或熔断结束后：尝试连接，成功则缓存客户端，失败则进入熔断期
    """
    global _redis_client, _redis_failed_until

    # 1. 熔断期内直接返回 None
    if time.time() < _redis_failed_until:
        return None

    # 2. 已有可用连接，直接复用
    if _redis_client is not None:
        return _redis_client

    # 3. 尝试连接
    try:
        client = redis.Redis(
            host='localhost',
            port=6379,
            decode_responses=True,
            protocol=2,
            socket_connect_timeout=1,   # 连接超时 1 秒
            socket_timeout=1,           # 读写超时 1 秒
        )
        client.ping()
        _redis_client = client
        logger.info("✅ Redis 连接成功")
    except Exception as e:
        logger.warning(f"⚠️ Redis 不可用，缓存跳过（{FAIL_COOLDOWN}秒内不再重试）: {e}")
        _redis_failed_until = time.time() + FAIL_COOLDOWN
        _redis_client = None

    return _redis_client


def get_cache_key(question: str) -> str:
    """用 MD5 生成固定长度的缓存键"""
    return f"sql_agent:{hashlib.md5(question.encode()).hexdigest()}"


#对外接口
def get_cached_answer(question: str):
    """从缓存获取答案。Redis 不可用或未命中时返回 None。"""
    client = _get_redis_client()
    if client is None:
        return None

    try:
        key = get_cache_key(question)
        cached = client.get(key)
        if cached:
            return json.loads(cached)
    except Exception as e:
        logger.warning(f"⚠️ 读取缓存失败: {e}")
    return None


def set_cached_answer(question: str, answer: str, ttl: int = 3600):
    """存入缓存。Redis 不可用时静默失败。"""
    client = _get_redis_client()
    if client is None:
        return

    try:
        key = get_cache_key(question)
        client.setex(key, ttl, json.dumps(answer, ensure_ascii=False))
    except Exception as e:
        logger.warning(f"⚠️ 写入缓存失败: {e}")