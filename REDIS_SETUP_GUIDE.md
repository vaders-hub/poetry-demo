# Redis 설치 및 Document Analysis 테스트 가이드

## 1. Redis 서버 설치

### Windows

#### 방법 1: WSL2 사용 (권장)
```bash
# WSL2에서 Redis 설치
sudo apt update
sudo apt install redis-server

# Redis 서버 시작
sudo service redis-server start

# Redis 연결 확인
redis-cli ping
# 응답: PONG
```

#### 방법 2: Windows용 Redis (비공식)
1. [Redis for Windows](https://github.com/tporadowski/redis/releases) 다운로드
2. 설치 후 서비스 시작:
```cmd
redis-server.exe
```

### macOS
```bash
# Homebrew로 설치
brew install redis

# Redis 서버 시작
brew services start redis

# Redis 연결 확인
redis-cli ping
```

### Linux
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install redis-server

# CentOS/RHEL
sudo yum install redis

# Redis 서버 시작
sudo systemctl start redis
sudo systemctl enable redis

# Redis 연결 확인
redis-cli ping
```

---

## 2. Python 패키지 설치

```bash
# Redis 패키지 설치
poetry install
```

---

## 3. Redis 연결 설정 (선택사항)

기본값: `redis://localhost:6379/0`

커스텀 설정이 필요한 경우 `.env` 파일에 추가:

```env
REDIS_URL=redis://localhost:6379/0
# 또는 비밀번호가 있는 경우
# REDIS_URL=redis://:password@localhost:6379/0
```

---

## 4. FastAPI 서버 시작

```bash
poetry run start
```

서버가 http://localhost:8001 에서 실행됩니다.

---

## 5. Swagger UI에서 테스트

### 5.1 Redis 연결 확인

**엔드포인트**: `GET /document-analysis-redis/redis-info`

Swagger UI에서 실행하여 Redis 연결 상태 확인:

```json
{
  "redis_connected": true,
  "redis_version": "7.2.3",
  "total_keys": 0,
  "used_memory_human": "1.2M"
}
```

### 5.2 문서 업로드 (Redis 저장)

**엔드포인트**: `POST /document-analysis-redis/upload-from-docs`

**Request Body**:
```json
{
  "doc_id": "policy_2025_redis",
  "file_name": "Reprimand-sample-1.pdf"
}
```

**Response**:
```json
{
  "doc_id": "policy_2025_redis",
  "file_name": "Reprimand-sample-1.pdf",
  "num_pages": 17,
  "total_nodes": 342,
  "child_nodes": 256,
  "execution_time_ms": 3456.78,
  "message": "PDF 파일이 Redis에 성공적으로 저장되었습니다."
}
```

### 5.3 문서 요약

**엔드포인트**: `POST /document-analysis-redis/summary`

**Request Body**:
```json
{
  "doc_id": "policy_2025_redis",
  "max_length": 200
}
```

### 5.4 주요 이슈 추출

**엔드포인트**: `POST /document-analysis-redis/extract-issues`

**Request Body**:
```json
{
  "doc_id": "policy_2025_redis",
  "top_k": 8
}
```

### 5.5 자유 질의응답

**엔드포인트**: `POST /document-analysis-redis/query`

**Request Body**:
```json
{
  "doc_id": "policy_2025_redis",
  "query": "2025년 소상공인 지원 예산 총 규모는 얼마인가요?",
  "streaming": false,
  "top_k": 5
}
```

---

## 6. 메모리 저장 vs Redis 저장 비교

### 메모리 저장 (`/document-analysis`)
- **장점**: 빠른 속도, 설정 불필요
- **단점**: 서버 재시작 시 데이터 손실
- **사용 시나리오**: 개발 중 테스트, 일회성 분석

### Redis 저장 (`/document-analysis-redis`)
- **장점**: 영구 저장, 여러 서버 간 공유 가능, TTL 설정 가능
- **단점**: Redis 서버 필요, 약간의 오버헤드
- **사용 시나리오**: 프로덕션 환경, 다수 사용자, 캐싱

---

## 7. Redis 데이터 확인

### Redis CLI에서 직접 확인

```bash
# Redis CLI 접속
redis-cli

# 저장된 모든 키 확인
KEYS doc:*

# 특정 문서 정보 확인
HGETALL doc:policy_2025_redis

# 문서 개수 확인
KEYS doc:* | wc -l

# TTL 확인 (남은 시간, 초 단위)
TTL doc:policy_2025_redis
```

### 데이터 삭제

```bash
# 특정 문서 삭제
DEL doc:policy_2025_redis

# 모든 문서 삭제
KEYS doc:* | xargs redis-cli DEL
```

---

## 8. 트러블슈팅

### 문제 1: Redis 연결 실패

**에러 메시지**:
```
HTTPException: Redis 연결 실패: Error 10061 connecting to localhost:6379
```

**해결 방법**:
1. Redis 서버가 실행 중인지 확인:
   ```bash
   # Windows (WSL)
   sudo service redis-server status

   # macOS
   brew services list

   # Linux
   sudo systemctl status redis
   ```

2. Redis 서버 시작:
   ```bash
   # Windows (WSL)
   sudo service redis-server start

   # macOS
   brew services start redis

   # Linux
   sudo systemctl start redis
   ```

### 문제 2: 인덱스 역직렬화 오류

**에러 메시지**:
```
pickle.UnpicklingError: invalid load key
```

**해결 방법**:
- 문서를 삭제하고 다시 업로드:
  ```bash
  redis-cli DEL doc:your_doc_id
  ```

### 문제 3: 메모리 부족

**에러 메시지**:
```
OOM command not allowed when used memory > 'maxmemory'
```

**해결 방법**:
1. Redis 메모리 제한 확인:
   ```bash
   redis-cli CONFIG GET maxmemory
   ```

2. 메모리 제한 증가 (예: 2GB):
   ```bash
   redis-cli CONFIG SET maxmemory 2gb
   ```

---

## 9. 성능 팁

### 1. TTL 최적화
기본 TTL은 24시간(86400초)입니다. 필요에 따라 조정하세요:

`src/routers/document_analysis_redis.py:72`에서 수정:
```python
await client.expire(f"doc:{doc_id}", 3600)  # 1시간
```

### 2. 대용량 문서 처리
대용량 문서의 경우 chunk 크기를 조정하세요:

`src/routers/document_analysis_redis.py:95-108`에서 수정:
```python
# Parent 노드: 1024자로 축소
parent_splitter = SentenceSplitter(chunk_size=1024, chunk_overlap=50)

# Child 노드: 256자로 축소
child_splitter = SentenceSplitter(chunk_size=256, chunk_overlap=25)
```

### 3. Redis 메모리 정책
Redis 설정 파일(`/etc/redis/redis.conf`)에서:
```conf
# LRU 정책 사용 (오래된 키 자동 삭제)
maxmemory-policy allkeys-lru

# 최대 메모리 (예: 2GB)
maxmemory 2gb
```

---

## 10. 다음 단계

1. ✅ Redis 서버 설치 및 실행
2. ✅ `poetry install`로 패키지 설치
3. ✅ FastAPI 서버 시작
4. ✅ Swagger UI에서 `/document-analysis-redis/redis-info` 테스트
5. ✅ 문서 업로드 및 쿼리 테스트
6. 🔄 메모리 버전과 Redis 버전 성능 비교
7. 🔄 TTL, 메모리 정책 등 최적화

---

## 참고 자료

- [Redis 공식 문서](https://redis.io/documentation)
- [redis-py 문서](https://redis-py.readthedocs.io/)
- [LlamaIndex 공식 문서](https://docs.llamaindex.ai/)
- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)

---

**작성일**: 2024-01-15
**버전**: 1.0
