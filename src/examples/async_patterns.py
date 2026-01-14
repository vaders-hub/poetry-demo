"""
FastAPI 비동기 처리 패턴 학습 예제

이 모듈은 FastAPI와 Python의 asyncio를 활용한 다양한 비동기 처리 패턴을 보여줍니다.
"""
import asyncio
import time
from typing import List, Dict, Any
from datetime import datetime


# ============================================================================
# Example 1: 기본 async/await
# ============================================================================

async def fetch_data(id: int, delay: float = 1.0) -> dict:
    """
    비동기 데이터 fetch 시뮬레이션

    await을 사용하여 다른 작업이 진행될 수 있도록 제어권 양도
    """
    print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Fetching data {id}...")
    await asyncio.sleep(delay)  # I/O 작업 시뮬레이션
    print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Data {id} fetched!")
    return {"id": id, "data": f"Result {id}"}


async def basic_async_example():
    """기본 async/await 예제"""
    print("\n=== Example 1: Basic async/await ===")
    start = time.time()

    # 순차 실행 (총 3초 소요)
    result1 = await fetch_data(1)
    result2 = await fetch_data(2)
    result3 = await fetch_data(3)

    elapsed = time.time() - start
    print(f"Sequential execution took: {elapsed:.2f}s")
    return [result1, result2, result3]


# ============================================================================
# Example 2: asyncio.gather를 사용한 병렬 실행
# ============================================================================

async def parallel_gather_example():
    """
    asyncio.gather를 사용한 병렬 실행

    여러 코루틴을 동시에 실행하고 모든 결과를 기다림
    """
    print("\n=== Example 2: Parallel execution with gather ===")
    start = time.time()

    # 병렬 실행 (총 1초 소요)
    results = await asyncio.gather(
        fetch_data(1),
        fetch_data(2),
        fetch_data(3)
    )

    elapsed = time.time() - start
    print(f"Parallel execution with gather took: {elapsed:.2f}s")
    return results


# ============================================================================
# Example 3: asyncio.create_task를 사용한 태스크 생성
# ============================================================================

async def task_creation_example():
    """
    asyncio.create_task를 사용한 태스크 생성

    태스크를 먼저 생성하여 백그라운드에서 실행 시작
    """
    print("\n=== Example 3: Task creation ===")
    start = time.time()

    # 태스크 생성 (즉시 실행 시작)
    task1 = asyncio.create_task(fetch_data(1))
    task2 = asyncio.create_task(fetch_data(2))
    task3 = asyncio.create_task(fetch_data(3))

    # 다른 작업 수행 가능
    print("Tasks created, doing other work...")
    await asyncio.sleep(0.5)

    # 모든 태스크 완료 대기
    results = await asyncio.gather(task1, task2, task3)

    elapsed = time.time() - start
    print(f"Task creation pattern took: {elapsed:.2f}s")
    return results


# ============================================================================
# Example 4: asyncio.wait와 타임아웃
# ============================================================================

async def wait_with_timeout_example():
    """
    asyncio.wait와 타임아웃 사용

    일부 작업만 완료되어도 진행하거나 타임아웃 설정
    """
    print("\n=== Example 4: Wait with timeout ===")

    tasks = [
        asyncio.create_task(fetch_data(1, delay=0.5)),
        asyncio.create_task(fetch_data(2, delay=1.5)),
        asyncio.create_task(fetch_data(3, delay=2.5)),
    ]

    # 1초 타임아웃
    done, pending = await asyncio.wait(tasks, timeout=1.0)

    print(f"Completed: {len(done)} tasks")
    print(f"Pending: {len(pending)} tasks")

    # 완료된 작업 결과
    results = [task.result() for task in done]

    # 미완료 작업 취소
    for task in pending:
        task.cancel()

    return results


# ============================================================================
# Example 5: asyncio.wait_for - 단일 작업 타임아웃
# ============================================================================

async def wait_for_example():
    """
    asyncio.wait_for - 단일 작업에 타임아웃 설정
    """
    print("\n=== Example 5: wait_for with timeout ===")

    try:
        # 0.5초 타임아웃 (작업은 1초 소요)
        result = await asyncio.wait_for(
            fetch_data(1, delay=1.0),
            timeout=0.5
        )
        return result
    except asyncio.TimeoutError:
        print("Operation timed out!")
        return {"error": "timeout"}


# ============================================================================
# Example 6: 에러 처리와 gather의 return_exceptions
# ============================================================================

async def fetch_with_error(id: int, should_fail: bool = False):
    """에러가 발생할 수 있는 fetch"""
    await asyncio.sleep(0.5)
    if should_fail:
        raise ValueError(f"Failed to fetch {id}")
    return {"id": id, "data": f"Result {id}"}


async def error_handling_example():
    """
    병렬 실행 시 에러 처리

    return_exceptions=True를 사용하여 일부 실패해도 계속 진행
    """
    print("\n=== Example 6: Error handling ===")

    # return_exceptions=True: 예외를 결과로 반환
    results = await asyncio.gather(
        fetch_with_error(1, should_fail=False),
        fetch_with_error(2, should_fail=True),
        fetch_with_error(3, should_fail=False),
        return_exceptions=True
    )

    # 결과 처리
    for i, result in enumerate(results, 1):
        if isinstance(result, Exception):
            print(f"Task {i} failed: {result}")
        else:
            print(f"Task {i} succeeded: {result}")

    return results


# ============================================================================
# Example 7: 세마포어를 사용한 동시 실행 제한
# ============================================================================

# 동시 실행 수 제한 (최대 2개)
semaphore = asyncio.Semaphore(2)


async def fetch_with_limit(id: int):
    """세마포어를 사용하여 동시 실행 수 제한"""
    async with semaphore:
        print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Starting {id} (max 2 concurrent)")
        await asyncio.sleep(1)
        print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Finished {id}")
        return {"id": id}


async def semaphore_example():
    """
    세마포어를 사용한 동시 실행 제한

    리소스 제한이 있을 때 유용 (예: DB 연결, API rate limit)
    """
    print("\n=== Example 7: Semaphore (max 2 concurrent) ===")
    start = time.time()

    # 5개 작업이지만 동시에 2개씩만 실행
    results = await asyncio.gather(
        fetch_with_limit(1),
        fetch_with_limit(2),
        fetch_with_limit(3),
        fetch_with_limit(4),
        fetch_with_limit(5),
    )

    elapsed = time.time() - start
    print(f"Semaphore pattern took: {elapsed:.2f}s (expected ~3s for 5 tasks)")
    return results


# ============================================================================
# Example 8: 비동기 컨텍스트 매니저
# ============================================================================

class AsyncResource:
    """비동기 리소스 예제 (DB 연결 등을 시뮬레이션)"""

    def __init__(self, name: str):
        self.name = name

    async def __aenter__(self):
        print(f"Opening resource: {self.name}")
        await asyncio.sleep(0.1)  # 연결 시뮬레이션
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        print(f"Closing resource: {self.name}")
        await asyncio.sleep(0.1)  # 정리 시뮬레이션

    async def fetch(self):
        print(f"Fetching from {self.name}")
        await asyncio.sleep(0.5)
        return f"Data from {self.name}"


async def async_context_manager_example():
    """
    비동기 컨텍스트 매니저 사용

    async with를 사용하여 리소스 자동 관리
    """
    print("\n=== Example 8: Async context manager ===")

    async with AsyncResource("Database") as db:
        result = await db.fetch()
        print(f"Result: {result}")

    # __aexit__이 자동 호출됨
    return result


# ============================================================================
# Example 9: 비동기 제너레이터 (async for)
# ============================================================================

async def async_data_generator(count: int):
    """
    비동기 제너레이터

    데이터를 스트리밍 방식으로 생성
    """
    for i in range(count):
        await asyncio.sleep(0.3)  # 데이터 생성 시뮬레이션
        yield {"id": i, "timestamp": datetime.now().isoformat()}


async def async_generator_example():
    """
    비동기 제너레이터 사용

    대용량 데이터를 메모리 효율적으로 처리
    """
    print("\n=== Example 9: Async generator ===")
    results = []

    async for data in async_data_generator(5):
        print(f"Received: {data}")
        results.append(data)

    return results


# ============================================================================
# Example 10: 비동기와 동기 코드 혼합
# ============================================================================

def sync_heavy_computation(n: int) -> int:
    """CPU 집약적 동기 작업"""
    print(f"Computing {n}...")
    time.sleep(0.5)  # CPU 작업 시뮬레이션
    result = sum(i * i for i in range(n))
    print(f"Computed {n}: {result}")
    return result


async def run_sync_in_executor_example():
    """
    동기 함수를 비동기로 실행

    run_in_executor를 사용하여 블로킹 함수를 별도 스레드에서 실행
    """
    print("\n=== Example 10: Running sync code in executor ===")
    loop = asyncio.get_running_loop()

    # 동기 함수를 병렬로 실행
    start = time.time()
    results = await asyncio.gather(
        loop.run_in_executor(None, sync_heavy_computation, 10000),
        loop.run_in_executor(None, sync_heavy_computation, 20000),
        loop.run_in_executor(None, sync_heavy_computation, 30000),
    )
    elapsed = time.time() - start

    print(f"Executor pattern took: {elapsed:.2f}s")
    return results


# ============================================================================
# 메인 실행 함수
# ============================================================================

async def run_all_examples():
    """모든 예제 실행"""
    print("=" * 70)
    print("FastAPI 비동기 처리 패턴 예제")
    print("=" * 70)

    examples = [
        ("Basic async/await", basic_async_example),
        ("Parallel with gather", parallel_gather_example),
        ("Task creation", task_creation_example),
        ("Wait with timeout", wait_with_timeout_example),
        ("Wait for timeout", wait_for_example),
        ("Error handling", error_handling_example),
        ("Semaphore limit", semaphore_example),
        ("Async context manager", async_context_manager_example),
        ("Async generator", async_generator_example),
        ("Sync in executor", run_sync_in_executor_example),
    ]

    results = {}

    for name, example_func in examples:
        try:
            result = await example_func()
            results[name] = {"status": "success", "result": result}
        except Exception as e:
            results[name] = {"status": "error", "error": str(e)}

        print()  # 빈 줄

    print("=" * 70)
    print("Summary")
    print("=" * 70)
    for name, result in results.items():
        status = result["status"]
        print(f"{name}: {status}")

    return results


def main():
    """동기 진입점"""
    asyncio.run(run_all_examples())


if __name__ == "__main__":
    main()
