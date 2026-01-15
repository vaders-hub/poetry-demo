# 조항 분석 API 사용 가이드

## 개요

조항 분석 API는 정부 정책 문서에서 **사유·근거 분석** 및 **예외 조항 검색** 기능을 제공합니다.

**Router**: `/document-clause-analysis`
**Storage**: Redis (document_analysis_redis와 동일한 저장소 사용)
**주요 기능**:
1. 조치/판단의 구체적 사유 및 근거 분석 (출처 표시)
2. 예외 조항 검색 ("다만", "단서", "예외적으로" 등)
3. 특정 조항 검색 (제1조, 부칙 등)

---

## API 엔드포인트

### 1. 문서 업로드

**Endpoint**: `POST /document-clause-analysis/upload-from-docs`

**설명**: PDF 문서를 업로드하고 Redis에 인덱스 생성

**Request Body**:
```json
{
  "file_name": "2024소상공인_지원정책.pdf",
  "doc_id": "policy_2024_v1"
}
```

**Response**:
```json
{
  "status": true,
  "message": "문서가 업로드되고 인덱스가 생성되었습니다.",
  "data": {
    "doc_id": "policy_2024_v1",
    "file_name": "2024소상공인_지원정책.pdf",
    "total_pages": 145,
    "total_chunks": 287,
    "parent_chunks": 143,
    "child_chunks": 144
  },
  "execution_time_ms": 12345.67,
  "metadata": {
    "index_type": "hierarchical",
    "parent_chunk_size": 2048,
    "child_chunk_size": 512
  }
}
```

---

### 2. 사유 및 근거 분석

**Endpoint**: `POST /document-clause-analysis/analyze-reason`

**설명**: 특정 조치/판단에 대한 구체적 사유와 근거를 분석하고 출처를 제공

**Request Body**:
```json
{
  "doc_id": "policy_2024_v1",
  "decision_or_action": "소상공인 지원금 확대",
  "top_k": 10
}
```

**Response**:
```json
{
  "status": true,
  "message": "사유 및 근거 분석이 완료되었습니다.",
  "data": {
    "doc_id": "policy_2024_v1",
    "decision_or_action": "소상공인 지원금 확대",
    "analysis": "## 1. 주요 사유\n- 코로나19로 인한 소상공인 매출 감소\n- 물가 상승으로 인한 경영난 심화\n- 임대료 부담 증가\n\n## 2. 근거 및 배경\n- 2023년 소상공인 폐업률 15% 증가 [참조 1]\n- 정부의 경제활성화 정책 [참조 2]\n\n## 3. 관련 조항\n- 소상공인 지원법 제12조 [참조 3]",
    "source_references": [
      {
        "reference_number": 1,
        "score": 0.8965,
        "text_preview": "2023년 소상공인 현황 분석 결과, 전년 대비 폐업률이 15% 증가했으며...",
        "full_text": "...",
        "metadata": {
          "page": 23,
          "chunk_index": 45,
          "node_type": "parent"
        }
      },
      {
        "reference_number": 2,
        "score": 0.8723,
        "text_preview": "정부는 경제활성화를 위해 소상공인 지원 예산을 전년 대비 30% 확대...",
        "full_text": "...",
        "metadata": {
          "page": 56,
          "parent_index": 112,
          "chunk_index": 1,
          "node_type": "child"
        }
      }
    ],
    "citations": [
      "[참조 1: 문단 45]",
      "[참조 2: 문단 112-1]"
    ],
    "total_sources_found": 10
  },
  "execution_time_ms": 3456.78,
  "metadata": {
    "analysis_type": "reason_analysis",
    "top_k_used": 10
  }
}
```

**사용 예시**:
```python
import requests

response = requests.post(
    "http://localhost:8001/document-clause-analysis/analyze-reason",
    json={
        "doc_id": "policy_2024_v1",
        "decision_or_action": "소상공인 지원금 확대",
        "top_k": 10
    }
)

data = response.json()
print(data["data"]["analysis"])
for citation in data["data"]["citations"]:
    print(citation)
```

---

### 3. 예외 조항 검색

**Endpoint**: `POST /document-clause-analysis/find-exceptions`

**설명**: 특정 상황에 대한 예외 조항, 단서 조항, 특례 규정 검색

**Request Body**:
```json
{
  "doc_id": "policy_2024_v1",
  "situation": "경영난으로 인한 폐업",
  "top_k": 10
}
```

**Response**:
```json
{
  "status": true,
  "message": "예외 조항 검색이 완료되었습니다.",
  "data": {
    "doc_id": "policy_2024_v1",
    "situation": "경영난으로 인한 폐업",
    "exception_analysis": "## 발견된 예외 조항\n\n### 1. 폐업 지원금 예외 적용\n**다만**, 다음 각 호의 경우에는 지원금을 지급하지 않는다:\n1. 허위 신고\n2. 중복 수령\n\n### 2. 임대료 지원 특례\n**이 경우** 임대료가 월 200만원을 초과하는 경우에도 특례로 지원 가능...",
    "highlighted_sources": [
      {
        "reference_number": 1,
        "score": 0.9123,
        "text_preview": "제15조(지원금 지급) ① 지원금은 폐업일로부터 3개월 이내 신청 가능. 다만, 허위 신고나 중복 수령의 경우 지급하지 않는다...",
        "full_text": "...",
        "metadata": {
          "page": 34,
          "chunk_index": 67
        },
        "found_exception_keywords": ["다만"]
      },
      {
        "reference_number": 3,
        "score": 0.8567,
        "text_preview": "임대료 지원은 월 150만원 한도. 이 경우 특례로 인정되는 경우 월 200만원까지 가능...",
        "full_text": "...",
        "metadata": {
          "page": 45,
          "chunk_index": 89
        },
        "found_exception_keywords": ["이 경우", "특례"]
      }
    ],
    "all_source_references": [...],
    "exception_clauses_found": 2
  },
  "execution_time_ms": 2345.67,
  "metadata": {
    "analysis_type": "exception_clause_search",
    "exception_keywords_searched": [
      "다만", "단서", "예외", "제외", "이 경우", "특례", "불구하고"
    ]
  }
}
```

**검색되는 예외 키워드**:
- "다만"
- "단서"
- "예외적으로" / "예외"
- "제외하고" / "제외"
- "이 경우"
- "특례"
- "불구하고"

**사용 예시**:
```python
import requests

response = requests.post(
    "http://localhost:8001/document-clause-analysis/find-exceptions",
    json={
        "doc_id": "policy_2024_v1",
        "situation": "경영난으로 인한 폐업",
        "top_k": 10
    }
)

data = response.json()
print(f"발견된 예외 조항: {data['data']['exception_clauses_found']}개")

for source in data["data"]["highlighted_sources"]:
    print(f"\n[참조 {source['reference_number']}]")
    print(f"발견된 키워드: {', '.join(source['found_exception_keywords'])}")
    print(f"내용: {source['text_preview']}")
```

---

### 4. 특정 조항 검색

**Endpoint**: `POST /document-clause-analysis/search-clause`

**설명**: 특정 조항 번호나 키워드로 조항 검색

**Request Body**:
```json
{
  "doc_id": "policy_2024_v1",
  "clause_keyword": "제1조",
  "top_k": 5
}
```

**Response**:
```json
{
  "status": true,
  "message": "조항 검색이 완료되었습니다.",
  "data": {
    "doc_id": "policy_2024_v1",
    "clause_keyword": "제1조",
    "search_results": "제1조(목적) 이 법은 소상공인의 경영 안정과 성장을 지원하기 위한 정책의 기본 사항을 규정함을 목적으로 한다...",
    "source_references": [
      {
        "reference_number": 1,
        "score": 0.9567,
        "text_preview": "제1조(목적) 이 법은 소상공인의 경영 안정과 성장을 지원하기 위한...",
        "full_text": "...",
        "metadata": {
          "page": 1,
          "chunk_index": 0
        }
      }
    ],
    "total_matches": 1
  },
  "execution_time_ms": 1234.56,
  "metadata": {
    "analysis_type": "clause_search",
    "top_k_used": 5
  }
}
```

**검색 가능한 조항 키워드 예시**:
- "제1조", "제12조" (조항 번호)
- "부칙"
- "별표", "별지"
- "시행령", "시행규칙"

---

### 5. Health Check

**Endpoint**: `GET /document-clause-analysis/health`

**설명**: API 상태 확인

**Response**:
```json
{
  "status": true,
  "message": "조항 분석 API가 정상 작동 중입니다.",
  "data": {
    "status": "healthy",
    "redis_connected": true
  }
}
```

---

## 전체 사용 흐름

### Step 1: 문서 업로드
```bash
curl -X POST "http://localhost:8001/document-clause-analysis/upload-from-docs" \
  -H "Content-Type: application/json" \
  -d '{
    "file_name": "2024소상공인_지원정책.pdf",
    "doc_id": "policy_2024_v1"
  }'
```

### Step 2-A: 사유 분석
```bash
curl -X POST "http://localhost:8001/document-clause-analysis/analyze-reason" \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "policy_2024_v1",
    "decision_or_action": "소상공인 지원금 확대",
    "top_k": 10
  }'
```

### Step 2-B: 예외 조항 검색
```bash
curl -X POST "http://localhost:8001/document-clause-analysis/find-exceptions" \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "policy_2024_v1",
    "situation": "경영난으로 인한 폐업",
    "top_k": 10
  }'
```

### Step 2-C: 특정 조항 검색
```bash
curl -X POST "http://localhost:8001/document-clause-analysis/search-clause" \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "policy_2024_v1",
    "clause_keyword": "제15조",
    "top_k": 5
  }'
```

---

## 주요 특징

### 1. 출처 추적 시스템
모든 분석 결과에 `source_references`와 `citations` 포함:
- `reference_number`: 참조 번호 (1, 2, 3...)
- `score`: 유사도 점수 (0-1)
- `text_preview`: 텍스트 미리보기 (300자)
- `full_text`: 전체 텍스트
- `metadata`: 페이지, 청크 인덱스 등

### 2. 예외 키워드 하이라이팅
`highlighted_sources`에는 예외 키워드가 포함된 소스만 표시:
- `found_exception_keywords`: 발견된 키워드 리스트

### 3. 계층적 인덱싱
- Parent chunks: 2048자 (큰 맥락)
- Child chunks: 512자 (세밀한 검색)

### 4. Redis 공유
- document_analysis_redis와 동일한 Redis 사용
- doc:{doc_id} 키로 저장
- Pickle + Base64 직렬화

---

## Swagger UI 테스트

서버 시작 후:
```
http://localhost:8001/docs
```

"Document Clause Analysis (Redis)" 섹션에서 모든 엔드포인트 테스트 가능

---

## 예시 시나리오

### 시나리오 1: 지원금 확대 근거 찾기
```python
# 1. 문서 업로드
upload_response = requests.post(
    "http://localhost:8001/document-clause-analysis/upload-from-docs",
    json={"file_name": "2024소상공인_지원정책.pdf", "doc_id": "policy_2024"}
)

# 2. 지원금 확대 사유 분석
reason_response = requests.post(
    "http://localhost:8001/document-clause-analysis/analyze-reason",
    json={
        "doc_id": "policy_2024",
        "decision_or_action": "2024년 소상공인 지원금 확대",
        "top_k": 10
    }
)

analysis = reason_response.json()["data"]["analysis"]
citations = reason_response.json()["data"]["citations"]

print("=== 지원금 확대 사유 ===")
print(analysis)
print("\n=== 근거 출처 ===")
for citation in citations:
    print(citation)
```

### 시나리오 2: 폐업 지원 예외 조항 찾기
```python
# 예외 조항 검색
exception_response = requests.post(
    "http://localhost:8001/document-clause-analysis/find-exceptions",
    json={
        "doc_id": "policy_2024",
        "situation": "폐업 후 지원금 신청",
        "top_k": 10
    }
)

highlighted = exception_response.json()["data"]["highlighted_sources"]

print("=== 예외 조항 ===")
for source in highlighted:
    print(f"\n[참조 {source['reference_number']}]")
    print(f"키워드: {', '.join(source['found_exception_keywords'])}")
    print(f"페이지: {source['metadata']['page']}")
    print(f"내용:\n{source['text_preview']}")
```

---

## 문제 해결

### 문제 1: Redis 연결 오류
```json
{
  "status": false,
  "message": "Redis 연결 오류",
  "error": "Connection refused"
}
```
**해결**: Redis 서버 시작 확인
```bash
redis-server
```

### 문제 2: 문서를 찾을 수 없음
```json
{
  "status": false,
  "message": "문서를 찾을 수 없습니다.",
  "error": "DOCUMENT_NOT_FOUND"
}
```
**해결**: doc_id 확인, 문서 재업로드

### 문제 3: 예외 조항이 발견되지 않음
**해결**:
- top_k 값 증가 (10 → 20)
- situation 키워드 변경 (더 구체적으로)
- 문서에 실제로 예외 조항이 있는지 확인

---

**작성일**: 2026-01-15
**API 버전**: 1.0.0
**Router**: `/document-clause-analysis`
