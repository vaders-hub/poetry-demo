# Tests

이 디렉토리는 poetry-demo 프로젝트의 테스트 코드를 포함합니다.

## 테스트 구조

```
tests/
├── conftest.py              # pytest 설정 및 fixture 정의
├── test_customer_crud.py    # Customer CRUD 유닛 테스트
├── test_customer_routes.py  # Customer API 라우트 통합 테스트
└── test_llm_routes.py       # LLM API 라우트 통합 테스트
```

## 테스트 실행

### 전체 테스트 실행
```bash
pytest
```

### 특정 테스트 파일 실행
```bash
pytest tests/test_customer_crud.py
pytest tests/test_customer_routes.py
pytest tests/test_llm_routes.py
```

### 특정 테스트 클래스 실행
```bash
pytest tests/test_customer_crud.py::TestCustomerCRUD
```

### 특정 테스트 함수 실행
```bash
pytest tests/test_customer_crud.py::TestCustomerCRUD::test_create_customer_success
```

### 상세 출력으로 실행
```bash
pytest -v
```

### 실패 시 즉시 중단
```bash
pytest -x
```

### 코드 커버리지 확인 (pytest-cov 설치 필요)
```bash
pytest --cov=src --cov-report=html
```

## 테스트 데이터베이스

테스트는 in-memory SQLite 데이터베이스를 사용하여 실제 Oracle 데이터베이스에 영향을 주지 않습니다.

## Fixture 설명

### conftest.py의 주요 fixture:

- **test_engine**: 테스트용 SQLite 엔진 생성
- **test_session**: 테스트용 데이터베이스 세션
- **client**: FastAPI 테스트 클라이언트
- **mock_openai_client**: OpenAI API 호출 모킹
- **mock_langchain_chain**: LangChain 체인 모킹
- **sample_customer_data**: 샘플 고객 데이터

## 테스트 커버리지

### Customer CRUD (test_customer_crud.py)
- ✅ 고객 생성 (성공/실패 케이스)
- ✅ 고객 조회 (전체/개별)
- ✅ 고객 수정
- ✅ 고객 삭제
- ✅ 완전한 CRUD 워크플로우

### Customer Routes (test_customer_routes.py)
- ✅ POST /customer/add
- ✅ GET /customer/list
- ✅ GET /customer/{customer_id}
- ✅ PUT /customer/modify
- ✅ DELETE /customer/delete
- ✅ 유효성 검증 및 에러 처리

### LLM Routes (test_llm_routes.py)
- ✅ GET /llm/sync/chat
- ✅ GET /llm/async/chat
- ✅ GET /llm/async/chat-stream
- ✅ GET /llm/async/generate-text
- ✅ GET /llm/complete
- ✅ OpenAI API 모킹 및 에러 처리

## 주의사항

1. 테스트 실행 전 필요한 의존성 설치:
   ```bash
   pip install pytest pytest-asyncio httpx pytest-mock
   ```

2. 환경 변수는 테스트에서 자동으로 모킹되므로 `.env` 파일이 없어도 실행 가능합니다.

3. LLM 테스트는 실제 OpenAI API를 호출하지 않고 모킹된 응답을 사용합니다.
