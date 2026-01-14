# FastAPI 비동기 처리와 LCEL 학습 가이드

이 가이드는 FastAPI의 비동기 처리와 LangChain의 LCEL(LangChain Expression Language)을 학습하기 위한 포괄적인 예제와 설명을 제공합니다.

## 목차

1. [개요](#개요)
2. [설치 및 실행](#설치-및-실행)
3. [비동기 처리 패턴](#비동기-처리-패턴)
4. [LCEL 패턴](#lcel-패턴)
5. [FastAPI 엔드포인트](#fastapi-엔드포인트)
6. [실전 예제](#실전-예제)
7. [성능 비교](#성능-비교)

---

## 개요

### 왜 비동기인가?

비동기 프로그래밍은 I/O 바운드 작업(API 호출, 데이터베이스 쿼리, 파일 읽기 등)에서 뛰어난 성능을 발휘합니다.

**동기 처리 (순차적):**
```
Task 1 (1초) → Task 2 (1초) → Task 3 (1초) = 총 3초
```

**비동기 처리 (병렬):**
```
Task 1 (1초)
Task 2 (1초)  ← 동시 실행
Task 3 (1초)
= 총 1초
```

### LCEL이란?

LCEL(LangChain Expression Language)은 LangChain의 선언적 문법으로, 복잡한 LLM 파이프라인을 간결하게 표현할 수 있습니다.

**전통적 방식:**
```python
prompt = PromptTemplate.from_template("Answer: {query}")
llm = ChatOpenAI()
parser = StrOutputParser()

result = parser.parse(llm.invoke(prompt.format(query="Hello")))
```

**LCEL 방식:**
```python
chain = prompt | llm | StrOutputParser()
result = await chain.ainvoke({"query": "Hello"})
```

---

## 설치 및 실행

### 의존성 설치

```bash
poetry install
```

추가된 주요 패키지:
- `langchain-core`: LCEL 핵심 기능
- `langsmith`: LangChain 추적 및 디버깅

### 환경 변수 설정

`.env` 파일에 OpenAI API 키가 설정되어 있는지 확인:

```env
OPENAI_API_KEY=your_api_key_here
```

### 실행 방법

#### 1. FastAPI 서버 실행

```bash
poetry run start
```

서버 실행 후 다음 URL에서 API 문서 확인:
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

#### 2. 독립 실행 스크립트

**비동기 패턴 예제:**
```bash
poetry run async-patterns
```

**LCEL 패턴 예제:**
```bash
poetry run lcel-patterns
```

---

## 비동기 처리 패턴

### Pattern 1: 기본 async/await

```python
async def fetch_data(id: int):
    await asyncio.sleep(1)  # I/O 시뮬레이션
    return {"id": id, "data": f"Result {id}"}

# 순차 실행
result1 = await fetch_data(1)
result2 = await fetch_data(2)
# 총 2초 소요
```

**핵심 개념:**
- `async def`: 비동기 함수 정의
- `await`: 비동기 작업 완료 대기, 다른 작업에 제어권 양도

### Pattern 2: asyncio.gather를 사용한 병렬 실행

```python
# 병렬 실행
results = await asyncio.gather(
    fetch_data(1),
    fetch_data(2),
    fetch_data(3)
)
# 총 1초 소요 (병렬로 실행)
```

**핵심 개념:**
- 여러 코루틴을 동시에 실행
- 모든 작업이 완료될 때까지 대기
- 결과를 리스트로 반환

### Pattern 3: asyncio.create_task

```python
# 태스크 생성 (즉시 백그라운드에서 실행 시작)
task1 = asyncio.create_task(fetch_data(1))
task2 = asyncio.create_task(fetch_data(2))

# 다른 작업 수행 가능
do_other_work()

# 결과 대기
results = await asyncio.gather(task1, task2)
```

**핵심 개념:**
- 태스크를 먼저 생성하여 백그라운드 실행
- 결과가 필요할 때까지 다른 작업 가능

### Pattern 4: 타임아웃 처리

```python
try:
    result = await asyncio.wait_for(
        fetch_data(1),
        timeout=0.5  # 0.5초 제한
    )
except asyncio.TimeoutError:
    print("Operation timed out!")
```

**핵심 개념:**
- 작업에 시간 제한 설정
- 초과 시 TimeoutError 발생

### Pattern 5: 에러 처리

```python
# return_exceptions=True: 예외를 결과로 반환
results = await asyncio.gather(
    task1(),
    task2(),  # 실패 가능
    task3(),
    return_exceptions=True
)

for result in results:
    if isinstance(result, Exception):
        handle_error(result)
    else:
        process_result(result)
```

**핵심 개념:**
- 일부 작업이 실패해도 전체 중단되지 않음
- 예외를 개별적으로 처리 가능

### Pattern 6: 세마포어 (동시 실행 제한)

```python
semaphore = asyncio.Semaphore(2)  # 최대 2개 동시 실행

async def limited_fetch(id):
    async with semaphore:
        return await fetch_data(id)

# 5개 작업이지만 동시에 2개씩만 실행
results = await asyncio.gather(*[
    limited_fetch(i) for i in range(5)
])
```

**핵심 개념:**
- 리소스 제한 (DB 연결, API rate limit 등)
- 동시 실행 수 제어

### Pattern 7: 비동기 컨텍스트 매니저

```python
class AsyncResource:
    async def __aenter__(self):
        # 리소스 획득
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # 리소스 정리
        pass

async with AsyncResource() as resource:
    await resource.use()
# 자동으로 정리됨
```

**핵심 개념:**
- 리소스 자동 관리 (DB 연결, 파일 등)
- 예외 발생 시에도 안전한 정리 보장

### Pattern 8: 비동기 제너레이터

```python
async def data_generator(count):
    for i in range(count):
        await asyncio.sleep(0.1)
        yield {"id": i}

async for data in data_generator(10):
    process(data)
```

**핵심 개념:**
- 대용량 데이터 스트리밍
- 메모리 효율적인 처리

### Pattern 9: 동기 코드 비동기화

```python
def blocking_function():
    time.sleep(1)  # 블로킹
    return "result"

# 별도 스레드에서 실행
loop = asyncio.get_running_loop()
result = await loop.run_in_executor(None, blocking_function)
```

**핵심 개념:**
- CPU 집약적 작업 또는 레거시 동기 코드
- 스레드 풀에서 실행하여 비동기화

---

## LCEL 패턴

### Pattern 1: 기본 체인 (Prompt | LLM | Parser)

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

prompt = ChatPromptTemplate.from_template("Tell me a joke about {topic}")
llm = ChatOpenAI(model="gpt-4o-mini")
chain = prompt | llm | StrOutputParser()

result = await chain.ainvoke({"topic": "programming"})
```

**핵심 개념:**
- Pipe(`|`) 연산자로 컴포넌트 연결
- 데이터가 왼쪽에서 오른쪽으로 흐름
- 각 단계의 출력이 다음 단계의 입력

### Pattern 2: RunnablePassthrough (데이터 전달)

```python
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

chain = {
    "original": RunnablePassthrough(),
    "uppercase": RunnableLambda(lambda x: x.upper()),
    "length": RunnableLambda(lambda x: len(x))
}

result = await chain.ainvoke("hello")
# {'original': 'hello', 'uppercase': 'HELLO', 'length': 5}
```

**핵심 개념:**
- 입력을 그대로 전달하거나 변환
- 여러 형태로 데이터 가공

### Pattern 3: RunnableParallel (병렬 실행)

```python
from langchain_core.runnables import RunnableParallel

parallel_chain = RunnableParallel({
    "sentiment": sentiment_prompt | llm | StrOutputParser(),
    "summary": summary_prompt | llm | StrOutputParser(),
    "keywords": keywords_prompt | llm | StrOutputParser()
})

# 세 작업을 동시에 실행
results = await parallel_chain.ainvoke({"text": "..."})
```

**핵심 개념:**
- 여러 체인을 병렬로 실행
- 처리 시간 단축 (가장 긴 작업만큼만 소요)

### Pattern 4: RunnableLambda (커스텀 로직)

```python
def preprocess(text: str) -> dict:
    return {"text": text, "word_count": len(text.split())}

def postprocess(result: str) -> dict:
    return {"response": result, "timestamp": datetime.now()}

chain = (
    RunnableLambda(preprocess)
    | prompt
    | llm
    | StrOutputParser()
    | RunnableLambda(postprocess)
)
```

**핵심 개념:**
- 체인 중간에 임의의 Python 함수 삽입
- 전처리/후처리 로직 추가

### Pattern 5: RunnableBranch (조건부 실행)

```python
from langchain_core.runnables import RunnableBranch

branch = RunnableBranch(
    (lambda x: len(x) < 20, short_prompt | llm | StrOutputParser()),
    (lambda x: len(x) < 50, medium_prompt | llm | StrOutputParser()),
    long_prompt | llm | StrOutputParser()  # default
)
```

**핵심 개념:**
- 조건에 따라 다른 체인 실행
- if-elif-else와 유사

### Pattern 6: 스트리밍

```python
chain = prompt | llm | StrOutputParser()

async for chunk in chain.astream({"query": "..."}):
    print(chunk, end="", flush=True)
```

**핵심 개념:**
- 토큰 단위로 실시간 출력
- 사용자 경험 향상

### Pattern 7: 배치 처리

```python
chain = prompt | llm | StrOutputParser()

inputs = [{"query": q} for q in queries]
results = await chain.abatch(inputs)
```

**핵심 개념:**
- 여러 입력을 효율적으로 처리
- API 호출 최적화

### Pattern 8: 맵-리듀스 패턴

```python
# Map: 병렬로 각 항목 처리
analyses = await asyncio.gather(*[
    analyze_chain.ainvoke({"item": item})
    for item in items
])

# Reduce: 결과 합치기
summary = await reduce_chain.ainvoke({"analyses": analyses})
```

**핵심 개념:**
- 대량 데이터를 병렬로 처리
- 결과를 하나로 집계

### Pattern 9: 체인 조합

```python
# Step 1
topic = await topic_chain.ainvoke({"interest": "..."})

# Step 2 (uses output from Step 1)
question = await question_chain.ainvoke({"topic": topic})

# Step 3 (uses output from Step 2)
answer = await answer_chain.ainvoke({"question": question})
```

**핵심 개념:**
- 여러 체인을 순차적으로 연결
- 각 단계의 출력이 다음 입력

### Pattern 10: 복잡한 워크플로우

```python
# 1. 병렬로 다양한 관점 생성
perspectives = await parallel_chain.ainvoke({"topic": "..."})

# 2. 결과 통합
summary = await summary_chain.ainvoke(perspectives)

# 3. 품질 검증
validated = await validation_chain.ainvoke({"content": summary})
```

**핵심 개념:**
- 병렬 + 순차 실행 조합
- 실전 워크플로우 구현

---

## FastAPI 엔드포인트

### 사용 가능한 LCEL API

서버 실행 후 http://localhost:8001/docs 에서 다음 엔드포인트들을 테스트할 수 있습니다:

#### 1. 기본 체인
```bash
POST /lcel/basic-chain
{
  "query": "What is FastAPI?"
}
```

#### 2. 스트리밍 응답
```bash
POST /lcel/streaming-chain
{
  "query": "Explain async/await in Python"
}
```

#### 3. 병렬 실행
```bash
POST /lcel/parallel-chain
{
  "text": "Python is a great programming language"
}
```

#### 4. 다단계 체인
```bash
POST /lcel/multi-step-chain
{
  "topic": "FastAPI best practices",
  "num_points": 3
}
```

#### 5. 번역 체인
```bash
POST /lcel/translation-chain
{
  "text": "안녕하세요",
  "source_lang": "Korean",
  "target_lang": "English"
}
```

#### 6. 배치 처리
```bash
POST /lcel/batch-chain
{
  "queries": [
    "What is Python?",
    "What is FastAPI?",
    "What is LCEL?"
  ]
}
```

#### 7. 복잡한 워크플로우
```bash
POST /lcel/complex-chain
{
  "topic": "Docker containerization",
  "format": "markdown"
}
```

---

## 실전 예제

### 예제 1: 비동기 데이터베이스 쿼리

```python
from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.get("/customers")
async def get_customers(db: AsyncSession):
    # 병렬로 여러 쿼리 실행
    users, orders, stats = await asyncio.gather(
        db.execute(select(User)),
        db.execute(select(Order)),
        db.execute(select(func.count(User.id)))
    )

    return {
        "users": users.scalars().all(),
        "orders": orders.scalars().all(),
        "total_users": stats.scalar()
    }
```

### 예제 2: LLM + 데이터베이스 조합

```python
@router.post("/intelligent-search")
async def intelligent_search(query: str, db: AsyncSession):
    llm = ChatOpenAI()

    # 1. LLM으로 쿼리 의도 파악
    intent_chain = (
        ChatPromptTemplate.from_template(
            "Extract search intent from: {query}"
        )
        | llm
        | JsonOutputParser()
    )

    intent = await intent_chain.ainvoke({"query": query})

    # 2. 의도 기반 DB 쿼리
    results = await db.execute(
        select(Product).where(Product.category == intent["category"])
    )

    # 3. 결과 요약
    summary_chain = (
        ChatPromptTemplate.from_template(
            "Summarize these products: {products}"
        )
        | llm
        | StrOutputParser()
    )

    summary = await summary_chain.ainvoke({
        "products": [p.name for p in results.scalars()]
    })

    return {
        "intent": intent,
        "products": results.scalars().all(),
        "summary": summary
    }
```

### 예제 3: 스트리밍 + 비동기

```python
from fastapi.responses import StreamingResponse

@router.post("/stream-analysis")
async def stream_analysis(text: str):
    chain = prompt | llm | StrOutputParser()

    async def generate():
        async for chunk in chain.astream({"text": text}):
            # Server-Sent Events 형식
            yield f"data: {chunk}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )
```

---

## 성능 비교

### 순차 vs 병렬 실행

**순차 실행 (5초):**
```python
result1 = await api_call_1()  # 1초
result2 = await api_call_2()  # 2초
result3 = await api_call_3()  # 2초
# 총: 5초
```

**병렬 실행 (2초):**
```python
results = await asyncio.gather(
    api_call_1(),  # 1초
    api_call_2(),  # 2초
    api_call_3()   # 2초
)
# 총: 2초 (가장 긴 작업)
```

### 실제 측정 예시

독립 실행 스크립트에서 확인 가능:

```bash
# 비동기 패턴 성능 측정
poetry run async-patterns

# 예상 출력:
# Sequential execution: 3.00s
# Parallel execution: 1.00s
# Speedup: 3x
```

---

## 학습 팁

### 1. 순서대로 학습

1. **기본 async/await** (src/examples/async_patterns.py)
   - Pattern 1-3 집중

2. **비동기 심화** (src/examples/async_patterns.py)
   - Pattern 4-9 학습

3. **기본 LCEL** (src/examples/lcel_patterns.py)
   - Pattern 1-4 집중

4. **LCEL 심화** (src/examples/lcel_patterns.py)
   - Pattern 5-10 학습

5. **FastAPI 통합** (src/routers/lcel_examples.py)
   - 실제 API로 테스트

### 2. 실습 방법

각 패턴을 다음과 같이 실습:

1. **코드 읽기**: 주석과 설명 이해
2. **독립 실행**: `poetry run async-patterns` 또는 `poetry run lcel-patterns`
3. **수정 실험**: 파라미터 변경해보기
4. **API 테스트**: Swagger UI에서 직접 호출
5. **성능 측정**: 실행 시간 비교

### 3. 디버깅 팁

**로깅 추가:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 체인 실행 과정 확인
chain = prompt | llm | StrOutputParser()
result = await chain.ainvoke({"query": "..."})
```

**LangSmith 활용:**
```env
# .env에 추가
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_key
LANGCHAIN_PROJECT=your_project
```

### 4. 일반적인 실수

**❌ 잘못된 예:**
```python
# await 없이 코루틴 호출
result = chain.ainvoke({"query": "..."})  # 코루틴 객체 반환

# 순차적으로 실행해야 하는데 병렬로 실행
result1 = asyncio.create_task(step1())
result2 = asyncio.create_task(step2(result1))  # result1이 아직 완료 안됨!
```

**✅ 올바른 예:**
```python
# await으로 결과 대기
result = await chain.ainvoke({"query": "..."})

# 의존성 있는 작업은 순차 실행
result1 = await step1()
result2 = await step2(result1)
```

---

## 추가 자료

### 공식 문서
- [FastAPI 비동기 가이드](https://fastapi.tiangolo.com/async/)
- [Python asyncio 공식 문서](https://docs.python.org/3/library/asyncio.html)
- [LangChain LCEL 문서](https://python.langchain.com/docs/expression_language/)

### 관련 파일
- `src/routers/lcel_examples.py`: FastAPI LCEL 엔드포인트
- `src/examples/async_patterns.py`: 비동기 패턴 예제
- `src/examples/lcel_patterns.py`: LCEL 패턴 예제

### 실습 프로젝트 아이디어

1. **챗봇 시스템**
   - 비동기로 여러 사용자 동시 처리
   - LCEL로 대화 체인 구성

2. **문서 분석 파이프라인**
   - 병렬로 여러 문서 처리
   - 맵-리듀스로 결과 집계

3. **실시간 번역 서비스**
   - 스트리밍으로 즉시 번역
   - 배치 처리로 여러 문장 한번에

---

## 문제 해결

### Q: "RuntimeError: asyncio.run() cannot be called from a running event loop"

**A:** Jupyter나 이미 실행 중인 이벤트 루프에서 발생합니다.

```python
# 대신 이렇게 사용:
import nest_asyncio
nest_asyncio.apply()

asyncio.run(my_function())
```

### Q: "This model's maximum context length is 16385 tokens"

**A:** 입력이 너무 깁니다. 텍스트를 분할하거나 요약하세요.

```python
# 텍스트 분할
chunks = [text[i:i+1000] for i in range(0, len(text), 1000)]
results = await chain.abatch([{"text": c} for c in chunks])
```

### Q: 성능이 기대만큼 안 나옵니다

**A:** 체크리스트:
- [ ] I/O 바운드 작업인가? (CPU 집약적이면 멀티프로세싱 사용)
- [ ] 병렬 실행 가능한가? (의존성 확인)
- [ ] API rate limit 걸리지 않았나?
- [ ] 세마포어로 동시 실행 제한했나?

---

## 요약

### 비동기 처리 핵심 3가지

1. **async/await**: 비동기 함수 정의 및 대기
2. **asyncio.gather**: 병렬 실행
3. **asyncio.create_task**: 백그라운드 실행

### LCEL 핵심 3가지

1. **Pipe(|)**: 컴포넌트 연결
2. **RunnableParallel**: 병렬 실행
3. **ainvoke/astream/abatch**: 비동기 실행 메서드

### FastAPI 통합

```python
@router.post("/endpoint")
async def endpoint(request: Request):
    # 비동기 + LCEL 조합
    chain = prompt | llm | StrOutputParser()
    result = await chain.ainvoke({"input": request.data})
    return result
```

---

이제 `poetry run start`로 서버를 실행하고 http://localhost:8001/docs 에서 직접 테스트해보세요!
