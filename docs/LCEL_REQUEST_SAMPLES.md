# LCEL 예제 Request Body 샘플

이 문서는 http://localhost:8001/docs 의 Swagger UI에서 각 LCEL 엔드포인트를 테스트할 때 사용할 수 있는 샘플 Request body를 제공합니다.

## 목차

1. [기본 LCEL 예제 (1-10)](#기본-lcel-예제)
2. [Pydantic 구조화 출력 예제 (11-18)](#pydantic-구조화-출력-예제)

---

## 기본 LCEL 예제

### 1. Basic Chain - `/lcel/basic-chain`

**설명**: 가장 기본적인 LCEL 체인

```json
{
  "query": "What is FastAPI and why is it popular?"
}
```

**다른 샘플**:
```json
{
  "query": "Explain the difference between async and sync programming"
}
```

---

### 2. Streaming Chain - `/lcel/streaming-chain`

**설명**: 실시간 스트리밍 응답

```json
{
  "query": "Write a detailed explanation of how Python's asyncio works"
}
```

**다른 샘플**:
```json
{
  "query": "Tell me a story about a robot learning to code"
}
```

---

### 3. Passthrough Chain - `/lcel/passthrough-chain`

**설명**: RunnablePassthrough를 사용한 데이터 전달

```json
{
  "query": "hello world"
}
```

**다른 샘플**:
```json
{
  "query": "python programming"
}
```

---

### 4. Multi-step Chain - `/lcel/multi-step-chain`

**설명**: 다단계 체인 (포인트 생성 → 설명)

```json
{
  "topic": "FastAPI best practices",
  "num_points": 3
}
```

**다른 샘플**:
```json
{
  "topic": "Python async/await patterns",
  "num_points": 5
}
```

```json
{
  "topic": "LangChain LCEL advantages",
  "num_points": 4
}
```

---

### 5. Parallel Chain - `/lcel/parallel-chain`

**설명**: 병렬 실행 (감정 분석 + 요약 + 키워드)

```json
{
  "text": "Python is a versatile programming language widely used in web development, data science, and artificial intelligence. Its simple syntax makes it beginner-friendly while remaining powerful for experienced developers."
}
```

**다른 샘플**:
```json
{
  "text": "FastAPI is a modern, fast web framework for building APIs with Python 3.7+ based on standard Python type hints. It provides automatic interactive API documentation and excellent performance."
}
```

---

### 6. Translation Chain - `/lcel/translation-chain`

**설명**: 번역 체인 (전처리 + 번역 + 후처리)

```json
{
  "text": "안녕하세요. 저는 파이썬 개발자입니다.",
  "source_lang": "Korean",
  "target_lang": "English"
}
```

**다른 샘플**:
```json
{
  "text": "FastAPI는 매우 빠르고 현대적인 웹 프레임워크입니다.",
  "source_lang": "Korean",
  "target_lang": "English"
}
```

```json
{
  "text": "Hello, I am a Python developer specializing in async programming.",
  "source_lang": "English",
  "target_lang": "Korean"
}
```

---

### 7. Conditional Chain - `/lcel/conditional-chain`

**설명**: 입력 길이에 따라 다른 프롬프트 사용

**짧은 입력** (간단한 답변):
```json
{
  "query": "What is Python?"
}
```

**긴 입력** (상세한 답변):
```json
{
  "query": "What is Python and how does it compare to other programming languages in terms of performance, syntax, and use cases?"
}
```

---

### 8. Batch Chain - `/lcel/batch-chain`

**설명**: 여러 질의를 병렬로 처리

```json
{
  "queries": [
    "What is Python?",
    "What is FastAPI?",
    "What is LCEL?"
  ]
}
```

**다른 샘플**:
```json
{
  "queries": [
    "Explain async/await",
    "What is a coroutine?",
    "What is asyncio?",
    "What is an event loop?",
    "What is a future?"
  ]
}
```

---

### 9. Retry Chain - `/lcel/retry-chain`

**설명**: 재시도 로직이 있는 체인

```json
{
  "query": "What are the benefits of using LCEL in LangChain?"
}
```

**다른 샘플**:
```json
{
  "query": "How does async programming improve performance?"
}
```

---

### 10. Complex Chain - `/lcel/complex-chain`

**설명**: 다단계 복잡한 워크플로우 (분석 → 생성 → 포맷 → 검증)

**Markdown 형식**:
```json
{
  "topic": "Docker containerization best practices",
  "format": "markdown"
}
```

**JSON 형식**:
```json
{
  "topic": "Python async programming patterns",
  "format": "json"
}
```

**Plain 형식**:
```json
{
  "topic": "FastAPI performance optimization",
  "format": "plain"
}
```

---

## Pydantic 구조화 출력 예제

### 11. Pydantic Person - `/lcel/pydantic-person`

**설명**: 텍스트에서 사람 정보 추출

```json
{
  "text": "John Smith is a 35 year old software engineer at Google. His email is john.smith@gmail.com"
}
```

**다른 샘플**:
```json
{
  "text": "Meet Sarah Johnson, a 28-year-old data scientist working at Microsoft"
}
```

```json
{
  "text": "키가 크지만 눈이 작은 사람"
}
```

---

### 12. Pydantic Movie Review - `/lcel/pydantic-movie-review`

**설명**: 영화 설명으로 구조화된 리뷰 생성

```json
{
  "movie_description": "A sci-fi thriller about AI taking over the world. The movie features stunning visual effects and a thought-provoking storyline about humanity's relationship with technology."
}
```

**다른 샘플**:
```json
{
  "movie_description": "A heartwarming comedy about a family road trip that goes hilariously wrong. Features great performances from the ensemble cast."
}
```

```json
{
  "movie_description": "An action-packed superhero movie with incredible fight scenes and a complex villain. The movie explores themes of power and responsibility."
}
```

---

### 13. Pydantic Structured Product - `/lcel/pydantic-structured-product`

**설명**: 제품 분석 (OpenAI structured output 사용)

```json
{
  "product_description": "iPhone 15 Pro - Latest flagship smartphone with A17 Pro chip, titanium design, and advanced camera system. Features USB-C port and Action button."
}
```

**다른 샘플**:
```json
{
  "product_description": "Tesla Model 3 - Electric sedan with autopilot capabilities, long range battery, and minimalist interior design. Affordable entry to Tesla lineup."
}
```

```json
{
  "product_description": "MacBook Pro M3 - Professional laptop with powerful M3 chip, stunning Liquid Retina XDR display, and all-day battery life. Perfect for developers and creators."
}
```

---

### 14. Pydantic Parallel - `/lcel/pydantic-parallel`

**설명**: 병렬로 여러 Pydantic 모델 생성

```json
{
  "product_description": "iPhone 15 Pro designed by Apple's chief designer Jony Ive successor. Features titanium frame and advanced camera system with 48MP main sensor."
}
```

**다른 샘플**:
```json
{
  "product_description": "Tesla Cybertruck developed under Elon Musk's leadership. Revolutionary electric pickup with stainless steel exoskeleton and bulletproof glass."
}
```

---

### 15. Pydantic List - `/lcel/pydantic-list`

**설명**: 여러 사람 정보를 리스트로 추출

```json
{
  "team_description": "Our development team consists of John Smith (35, lead developer), Sarah Johnson (28, frontend specialist), and Mike Chen (32, DevOps engineer). All members have 5+ years of experience."
}
```

**다른 샘플**:
```json
{
  "team_description": "The startup was founded by three entrepreneurs: Emily Davis (29, CEO), Robert Brown (31, CTO), and Lisa Wang (27, CFO). They all met at Stanford University."
}
```

```json
{
  "team_description": "우리 팀은 김철수 (팀장, 40세), 이영희 (시니어 개발자, 35세), 박민수 (주니어 개발자, 25세)로 구성되어 있습니다."
}
```

---

### 16. Pydantic with Postprocessing - `/lcel/pydantic-with-postprocessing`

**설명**: 코드 분석 + 후처리 (리스크 레벨, 개발 시간 추정)

```json
{
  "code_description": "A REST API for user authentication with JWT tokens, password hashing, and rate limiting. Should handle 1000 requests per second."
}
```

**다른 샘플**:
```json
{
  "code_description": "A microservice for processing payments with Stripe integration, handling webhooks, and storing transaction logs in PostgreSQL."
}
```

```json
{
  "code_description": "A real-time chat application using WebSockets, with message persistence, user presence tracking, and typing indicators."
}
```

---

### 17. Pydantic Batch - `/lcel/pydantic-batch`

**설명**: 여러 텍스트에서 사람 정보 배치 추출

```json
{
  "texts": [
    "John Smith is a 35 year old software engineer",
    "Sarah is a 28-year-old data scientist at Microsoft",
    "Mike Chen, 32, works as a DevOps engineer"
  ]
}
```

**다른 샘플**:
```json
{
  "texts": [
    "Emily Davis, 29-year-old CEO of TechStart Inc.",
    "Robert Brown is the CTO, age 31",
    "Lisa Wang serves as CFO at 27 years old",
    "David Park, 33, is the VP of Engineering"
  ]
}
```

---

### 18. Pydantic Conditional - `/lcel/pydantic-conditional`

**설명**: 조건에 따라 다른 Pydantic 모델 사용

**간단한 분석**:
```json
{
  "text": "Python is a popular programming language for web development and data science.",
  "detailed": false
}
```

**상세한 분석**:
```json
{
  "text": "Python is a popular programming language for web development and data science.",
  "detailed": true
}
```

**다른 샘플** (상세 분석):
```json
{
  "text": "FastAPI is a modern web framework that provides excellent performance and automatic API documentation. It uses Python type hints for validation.",
  "detailed": true
}
```

---

## 추가 팁

### Swagger UI 사용 방법

1. 브라우저에서 http://localhost:8001/docs 접속
2. 원하는 엔드포인트 클릭
3. "Try it out" 버튼 클릭
4. 위의 샘플 JSON을 Request body에 붙여넣기
5. "Execute" 버튼 클릭
6. 응답 확인

### 응답 예시

대부분의 엔드포인트는 다음과 같은 형식으로 응답합니다:

```json
{
  "result": "...",
  "execution_time_ms": 1234.56,
  "explanation": "..."
}
```

Pydantic 엔드포인트는 구조화된 데이터를 반환합니다:

```json
{
  "name": "John Smith",
  "age": 35,
  "occupation": "software engineer",
  "email": "john.smith@gmail.com"
}
```

### 성능 비교

병렬 처리 엔드포인트들은 실행 시간이 훨씬 빠릅니다:

- **순차 처리**: 각 작업이 완료된 후 다음 작업 시작
- **병렬 처리**: 모든 작업이 동시에 실행 (가장 긴 작업만큼만 소요)

예를 들어, 3개의 1초짜리 작업:
- 순차: 3초
- 병렬: 1초

### 문제 해결

**에러가 발생하면**:

1. OpenAI API 키가 `.env`에 설정되어 있는지 확인
2. 서버가 실행 중인지 확인 (`poetry run start`)
3. Request body의 JSON 형식이 올바른지 확인
4. 필수 필드가 모두 포함되어 있는지 확인

**타임아웃이 발생하면**:

- LLM 응답이 느릴 수 있습니다 (특히 복잡한 요청)
- 입력을 더 간단하게 만들어보세요
- 재시도해보세요

---

## 학습 순서 추천

1. **Basic Chain** → LCEL의 기본 개념 이해
2. **Passthrough Chain** → 데이터 전달 방식 학습
3. **Parallel Chain** → 병렬 실행의 효율성 체험
4. **Batch Chain** → 여러 입력 처리 방법
5. **Pydantic Person** → 구조화된 출력 기초
6. **Pydantic Structured Product** → OpenAI structured output
7. **Pydantic Parallel** → 구조화 출력 병렬 실행
8. **Complex Chain** → 실전 워크플로우

각 예제를 실행해보고 `execution_time_ms`를 비교하면서 비동기와 병렬 처리의 이점을 체감해보세요!
