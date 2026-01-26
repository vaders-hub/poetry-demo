"""
Redis 클라이언트 관리 유틸리티

Redis 연결을 싱글톤 패턴으로 관리하여 여러 라우터에서 재사용
"""

import os

import redis.asyncio as redis

# Redis 클라이언트 (전역 싱글톤)
_redis_client: redis.Redis | None = None


async def get_redis_client() -> redis.Redis:
    """
    Redis 클라이언트 가져오기 (싱글톤 패턴)

    환경변수 REDIS_URL에서 Redis 연결 정보를 읽어 클라이언트를 생성합니다.
    이미 생성된 클라이언트가 있으면 재사용합니다.

    Returns:
        redis.Redis: Redis 비동기 클라이언트

    Environment Variables:
        REDIS_URL: Redis 연결 URL (기본값: "redis://localhost:6379/0")

    Examples:
        >>> client = await get_redis_client()
        >>> await client.set("key", "value")
        >>> await client.get("key")
        b'value'
    """
    global _redis_client

    if _redis_client is None:
        # .env에서 REDIS_URL 읽기, 없으면 기본값 사용
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        # redis.asyncio.from_url은 await 없이 호출 (클라이언트 객체 반환)
        _redis_client = redis.from_url(redis_url, decode_responses=False)

    return _redis_client


async def close_redis_client():
    """
    Redis 클라이언트 종료

    전역 Redis 클라이언트 연결을 종료하고 None으로 초기화합니다.
    주로 애플리케이션 종료 시 호출됩니다.

    Examples:
        >>> await close_redis_client()
    """
    global _redis_client

    if _redis_client:
        await _redis_client.close()
        _redis_client = None


async def ping_redis() -> bool:
    """
    Redis 연결 상태 확인

    Redis 서버에 ping을 보내 연결 상태를 확인합니다.

    Returns:
        bool: 연결 성공 시 True, 실패 시 False

    Examples:
        >>> is_connected = await ping_redis()
        >>> print(f"Redis connected: {is_connected}")
        Redis connected: True
    """
    try:
        client = await get_redis_client()
        await client.ping()
        return True
    except Exception:
        return False
