# 조항 분석 기능 개발 완료 보고서

## ✅ 완료 요약

**작업 완료일**: 2026-01-15
**작업 시간**: 약 30분
**상태**: 완료 (테스트 대기)

---

## 개발된 기능

### 1. 사유 및 근거 분석
**Endpoint**: `POST /document-clause-analysis/analyze-reason`

**기능**:
- 특정 조치/판단에 대한 구체적 사유 분석
- 근거 문단 추출 및 출처 표시
- 참조 번호로 인용 ([참조 1: 문단 45])

**주요 응답 필드**:
```json
{
  "analysis": "## 1. 주요 사유\n...",
  "source_references": [...],
  "citations": ["[참조 1: 문단 45]", ...],
  "total_sources_found": 10
}
```

---

### 2. 예외 조항 검색
**Endpoint**: `POST /document-clause-analysis/find-exceptions`

**기능**:
- "다만", "단서", "예외적으로" 등 예외 키워드 자동 검색
- 예외 조항 하이라이팅
- 발견된 키워드 표시

**검색 키워드**:
- "다만"
- "단서"
- "예외" / "예외적으로"
- "제외" / "제외하고"
- "이 경우"
- "특례"
- "불구하고"

**주요 응답 필드**:
```json
{
  "exception_analysis": "...",
  "highlighted_sources": [
    {
      "reference_number": 1,
      "found_exception_keywords": ["다만", "특례"],
      "text_preview": "...",
      ...
    }
  ],
  "exception_clauses_found": 2
}
```

---

### 3. 특정 조항 검색
**Endpoint**: `POST /document-clause-analysis/search-clause`

**기능**:
- 조항 번호로 검색 (제1조, 제12조)
- 부칙, 별표 등 특수 조항 검색

---

### 4. 문서 업로드
**Endpoint**: `POST /document-clause-analysis/upload-from-docs`

**기능**:
- PDF 파일 업로드
- 계층적 인덱싱 (Parent: 2048자, Child: 512자)
- Redis 저장 (document_analysis_redis와 공유)

---

### 5. Health Check
**Endpoint**: `GET /document-clause-analysis/health`

**기능**:
- API 상태 확인
- Redis 연결 확인

---

## 기술 구현 세부사항

### 1. 파일 구조
```
src/routers/
└── document_clause_analysis.py  [NEW - 460줄]
    ├── 5개 엔드포인트
    ├── 2개 헬퍼 함수
    └── 4개 Request 모델
```

### 2. 헬퍼 함수

#### `extract_source_references()`
```python
def extract_source_references(source_nodes: List, top_n: int = 5):
    """소스 노드에서 참조 정보 추출"""
    references = []
    for idx, node in enumerate(source_nodes[:top_n], 1):
        node_info = {
            "reference_number": idx,
            "score": round(float(node.score or 0.0), 4),
            "text_preview": getattr(node.node, "text", "")[:300] + "...",
            "full_text": getattr(node.node, "text", ""),
            "metadata": {
                "page": getattr(node.node, "metadata", {}).get("page_label", "Unknown"),
                "chunk_index": getattr(node.node, "metadata", {}).get("chunk_index", 0),
                "node_type": getattr(node.node, "metadata", {}).get("node_type", "unknown"),
            }
        }
        if node_info["metadata"]["node_type"] == "child":
            node_info["metadata"]["parent_index"] = getattr(node.node, "metadata", {}).get("parent_index", 0)
        references.append(node_info)
    return references
```

#### `format_citation()`
```python
def format_citation(reference: Dict[str, Any]) -> str:
    """인용 형식 생성: [참조 1: 문단 45] 또는 [참조 1: 문단 45-2]"""
    ref_num = reference["reference_number"]
    metadata = reference["metadata"]

    if metadata["node_type"] == "child":
        return f"[참조 {ref_num}: 문단 {metadata['parent_index']}-{metadata['chunk_index']}]"
    else:
        return f"[참조 {ref_num}: 문단 {metadata['chunk_index']}]"
```

### 3. Request 모델

```python
class DocumentUploadRequest(BaseModel):
    """문서 업로드 요청"""
    file_name: str
    doc_id: str

class ReasonAnalysisRequest(BaseModel):
    """사유 및 근거 분석 요청"""
    doc_id: str
    decision_or_action: str
    top_k: int = 10

class ExceptionClauseRequest(BaseModel):
    """예외 조항 검색 요청"""
    doc_id: str
    situation: str
    top_k: int = 10

class ClauseSearchRequest(BaseModel):
    """특정 조항 검색 요청"""
    doc_id: str
    clause_keyword: str
    top_k: int = 5
```

### 4. Redis 통합

**저장 방식**: document_analysis_redis.py와 동일
```python
# 키: doc:{doc_id}
# 값: Base64(Pickle(index))

redis_key = f"doc:{doc_id}"
index_bytes = pickle.dumps(index)
index_base64 = base64.b64encode(index_bytes).decode('utf-8')
redis_client.set(redis_key, index_base64)
```

**불러오기**:
```python
index_data = redis_client.get(redis_key)
index_bytes = base64.b64decode(index_data)
index = pickle.loads(index_bytes)
```

### 5. 프롬프트 엔지니어링

#### 사유 분석 프롬프트
```python
query = f"""
다음 조치 또는 판단에 대한 구체적인 사유와 근거를 분석해주세요:

**조치/판단**: {request.decision_or_action}

아래 형식으로 답변해주세요:

## 1. 주요 사유
- [사유 1]
- [사유 2]
...

## 2. 근거 및 배경
- [근거 1]
- [근거 2]
...

## 3. 관련 조항 또는 정책
- [조항/정책 1]
- [조항/정책 2]
...

각 항목에는 문서의 구체적인 내용을 인용하여 근거를 명확히 해주세요.
"""
```

#### 예외 조항 검색 프롬프트
```python
exception_keywords = ["다만", "단서", "예외", "제외", "이 경우", "특례", "불구하고"]

query = f"""
다음 상황에 대해 적용 가능한 예외 조항, 단서 조항, 특례 규정을 찾아주세요:

**상황**: {request.situation}

문서에서 다음과 같은 표현을 포함한 조항을 우선적으로 찾아주세요:
- "다만", "단서", "예외적으로", "제외하고", "이 경우"
- "특례", "특별한 경우", "별도로 정하는"
- "~을 제외하고는", "~에도 불구하고"

발견된 예외 조항을 아래 형식으로 정리해주세요:

## 발견된 예외 조항

### 1. [예외 조항 제목]
[예외 조항 내용 전문 또는 요약]

### 2. [예외 조항 제목]
[예외 조항 내용 전문 또는 요약]
...
"""
```

---

## 변경된 파일

### 1. `src/routers/document_clause_analysis.py` [NEW]
**라인 수**: 460줄
**엔드포인트**: 5개
**상태**: 완료

### 2. `src/router.py` [UPDATED]
**변경사항**:
```python
# Import 추가
from src.routers import document_clause_analysis

# Router 등록
app.include_router(document_clause_analysis.router)
```

### 3. `CLAUSE_ANALYSIS_API.md` [NEW]
**내용**: 전체 API 사용 가이드
**라인 수**: 500+줄
**포함 내용**:
- API 엔드포인트 상세 설명
- Request/Response 예시
- 사용 흐름
- Python 코드 예시
- 문제 해결 가이드

---

## 테스트 검증

### 1. Import 테스트
```bash
✅ document_clause_analysis.py imported successfully!
✅ Main router with all endpoints imported successfully
```

### 2. 서버 시작 테스트 (사용자 실행 필요)
```bash
poetry run start
# 예상: http://localhost:8001
```

### 3. Swagger UI 테스트 (사용자 실행 필요)
```
http://localhost:8001/docs
→ "Document Clause Analysis (Redis)" 섹션 확인
```

---

## API 테스트 시나리오

### 시나리오 1: 지원금 확대 근거 분석

#### Step 1: 문서 업로드
```bash
curl -X POST "http://localhost:8001/document-clause-analysis/upload-from-docs" \
  -H "Content-Type: application/json" \
  -d '{
    "file_name": "2024소상공인_지원정책.pdf",
    "doc_id": "policy_2024"
  }'
```

**예상 응답**:
```json
{
  "status": true,
  "message": "문서가 업로드되고 인덱스가 생성되었습니다.",
  "data": {
    "doc_id": "policy_2024",
    "file_name": "2024소상공인_지원정책.pdf",
    "total_pages": 145,
    "total_chunks": 287
  },
  "execution_time_ms": 12345.67
}
```

#### Step 2: 사유 분석
```bash
curl -X POST "http://localhost:8001/document-clause-analysis/analyze-reason" \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "policy_2024",
    "decision_or_action": "소상공인 지원금 확대",
    "top_k": 10
  }'
```

**예상 응답**:
```json
{
  "status": true,
  "message": "사유 및 근거 분석이 완료되었습니다.",
  "data": {
    "analysis": "## 1. 주요 사유\n- 코로나19로 인한 매출 감소\n- 물가 상승으로 경영난 심화\n\n## 2. 근거 및 배경\n- 2023년 폐업률 15% 증가\n- 정부 경제활성화 정책\n\n## 3. 관련 조항\n- 소상공인 지원법 제12조",
    "source_references": [
      {
        "reference_number": 1,
        "score": 0.8965,
        "text_preview": "2023년 소상공인 현황 분석...",
        "metadata": {"page": 23, "chunk_index": 45}
      }
    ],
    "citations": ["[참조 1: 문단 45]"],
    "total_sources_found": 10
  },
  "execution_time_ms": 3456.78
}
```

---

### 시나리오 2: 폐업 예외 조항 검색

```bash
curl -X POST "http://localhost:8001/document-clause-analysis/find-exceptions" \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "policy_2024",
    "situation": "경영난으로 인한 폐업",
    "top_k": 10
  }'
```

**예상 응답**:
```json
{
  "status": true,
  "message": "예외 조항 검색이 완료되었습니다.",
  "data": {
    "exception_analysis": "## 발견된 예외 조항\n\n### 1. 폐업 지원금 예외\n**다만**, 허위 신고나 중복 수령의 경우 지급하지 않는다.\n\n### 2. 임대료 지원 특례\n**이 경우** 월 200만원까지 특례 지원 가능...",
    "highlighted_sources": [
      {
        "reference_number": 1,
        "score": 0.9123,
        "text_preview": "제15조(지원금 지급) 다만, 허위 신고나 중복 수령의 경우...",
        "found_exception_keywords": ["다만"],
        "metadata": {"page": 34}
      },
      {
        "reference_number": 3,
        "score": 0.8567,
        "text_preview": "임대료 지원 월 150만원 한도. 이 경우 특례로...",
        "found_exception_keywords": ["이 경우", "특례"],
        "metadata": {"page": 45}
      }
    ],
    "exception_clauses_found": 2
  },
  "execution_time_ms": 2345.67
}
```

---

## 주요 기능 상세

### 1. 출처 추적 시스템

**source_references 구조**:
```json
{
  "reference_number": 1,        // 참조 번호
  "score": 0.8965,              // 유사도 점수
  "text_preview": "...",        // 300자 미리보기
  "full_text": "...",           // 전체 텍스트
  "metadata": {
    "page": 23,                 // 페이지 번호
    "chunk_index": 45,          // 청크 인덱스
    "node_type": "parent",      // parent or child
    "parent_index": 112         // (child만) 부모 인덱스
  }
}
```

**citations 형식**:
- Parent chunk: `[참조 1: 문단 45]`
- Child chunk: `[참조 2: 문단 112-1]`

### 2. 예외 키워드 하이라이팅

**highlighted_sources**에만 포함되는 조건:
```python
found_keywords = [
    keyword for keyword in exception_keywords
    if keyword in ref["full_text"]
]
if found_keywords:
    ref["found_exception_keywords"] = found_keywords
    highlighted_sources.append(ref)
```

**발견된 키워드 표시**:
```json
{
  "found_exception_keywords": ["다만", "특례"]
}
```

### 3. 계층적 인덱싱

**Parent Chunks** (큰 맥락):
- 크기: 2048자
- 용도: 전체 문맥 파악

**Child Chunks** (세밀한 검색):
- 크기: 512자
- 용도: 정확한 문구 검색

**장점**:
- 큰 맥락과 세밀한 검색 동시 지원
- 검색 정확도 향상

---

## 사용자 요구사항 충족

### ✅ 요구사항 1: 조치·판단 사유 및 근거 출처
> "조치(또는 판단)가 내려진 구체적인 사유는 무엇이며, 근거 문단은 어디인가요?"

**구현**:
- `POST /analyze-reason` 엔드포인트
- `source_references`로 근거 문단 제공
- `citations`로 출처 표시 ([참조 1: 문단 45])
- 페이지 번호, 청크 인덱스 포함

---

### ✅ 요구사항 2: 예외 조항 검색
> "동일한 상황에서 예외가 적용될 수 있는 조건이 문서에 명시되어 있나요?"
> "다만, 단서, 예외적으로" 처리

**구현**:
- `POST /find-exceptions` 엔드포인트
- 7개 예외 키워드 자동 검색: ["다만", "단서", "예외", "제외", "이 경우", "특례", "불구하고"]
- `highlighted_sources`로 예외 조항만 필터링
- `found_exception_keywords`로 발견된 키워드 표시

---

### ✅ Redis 사용
- document_analysis_redis.py와 동일한 Redis 사용
- doc:{doc_id} 키 형식
- Pickle + Base64 직렬화

---

### ✅ 파일 분리
- 새 파일 생성: `document_clause_analysis.py`
- document_analysis_redis.py 크기 유지
- 명확한 책임 분리

---

### ✅ PDF 문서 적합성
정부 정책 문서에 최적화:
- 조항 번호 검색 (제1조, 제12조)
- 예외 조항 한국어 키워드
- 페이지 번호 추적
- 계층적 인덱싱으로 문맥 유지

---

## 이점 요약

### 1. 정확한 출처 추적
- 모든 분석 결과에 참조 번호
- 페이지 번호, 문단 인덱스 제공
- 원문 미리보기 300자

### 2. 자동 예외 조항 검색
- 7개 키워드 자동 검색
- 발견된 키워드 하이라이팅
- 예외 조항만 필터링

### 3. 한국어 정부 문서 최적화
- 한국어 예외 표현 전문 검색
- 조항 번호 체계 지원
- 문맥 유지 인덱싱

### 4. 확장 가능한 구조
- Redis 공유로 저장소 통합
- 독립적인 라우터 파일
- 쉬운 엔드포인트 추가

### 5. 개발자 친화적 API
- 명확한 Request/Response
- Response wrapper 통일
- 상세한 메타데이터

---

## 다음 단계 (테스트)

### 1. 서버 시작
```bash
poetry run start
```

### 2. Swagger UI 접속
```
http://localhost:8001/docs
```

### 3. 실제 PDF 테스트

#### Step 1: 문서 업로드
- Endpoint: `POST /document-clause-analysis/upload-from-docs`
- Body:
```json
{
  "file_name": "2024소상공인_지원정책.pdf",
  "doc_id": "test_policy_001"
}
```

#### Step 2: 사유 분석 테스트
- Endpoint: `POST /document-clause-analysis/analyze-reason`
- Body:
```json
{
  "doc_id": "test_policy_001",
  "decision_or_action": "소상공인 지원금 확대",
  "top_k": 10
}
```
- 확인사항:
  - [ ] analysis 필드에 사유/근거 분석 결과
  - [ ] source_references에 참조 정보
  - [ ] citations에 인용 형식
  - [ ] 페이지 번호 정확성

#### Step 3: 예외 조항 테스트
- Endpoint: `POST /document-clause-analysis/find-exceptions`
- Body:
```json
{
  "doc_id": "test_policy_001",
  "situation": "경영난으로 인한 폐업",
  "top_k": 10
}
```
- 확인사항:
  - [ ] highlighted_sources에 예외 키워드 포함 소스
  - [ ] found_exception_keywords 필드 존재
  - [ ] exception_clauses_found 개수 정확

#### Step 4: 특정 조항 테스트
- Endpoint: `POST /document-clause-analysis/search-clause`
- Body:
```json
{
  "doc_id": "test_policy_001",
  "clause_keyword": "제1조",
  "top_k": 5
}
```
- 확인사항:
  - [ ] 제1조 조항 검색 결과
  - [ ] 정확한 매칭

---

## 체크리스트

### 개발 완료
- [x] document_clause_analysis.py 생성 (460줄)
- [x] 5개 엔드포인트 구현
- [x] 2개 헬퍼 함수 구현
- [x] src/router.py에 등록
- [x] Import 테스트 통과

### 문서화 완료
- [x] CLAUSE_ANALYSIS_API.md (500+줄)
- [x] CLAUSE_ANALYSIS_COMPLETE.md (현재 문서)
- [x] 전체 API 가이드
- [x] 사용 예시 작성

### 테스트 대기 (사용자 실행)
- [ ] 서버 시작
- [ ] Swagger UI 확인
- [ ] 실제 PDF 업로드
- [ ] 사유 분석 테스트
- [ ] 예외 조항 검색 테스트
- [ ] 특정 조항 검색 테스트

---

## 파일 구조

```
D:\lab\python\code\poetry-demo\
├── src/
│   ├── routers/
│   │   ├── document_clause_analysis.py   [NEW - 460줄]
│   │   ├── document_analysis_redis.py    [기존]
│   │   └── ...
│   └── router.py                         [UPDATED]
├── CLAUSE_ANALYSIS_API.md                [NEW - 500+줄]
├── CLAUSE_ANALYSIS_COMPLETE.md           [NEW - 현재 문서]
└── RESPONSE_WRAPPER_COMPLETE.md          [기존]
```

---

## 마무리

### ✅ 완료된 작업
1. 조항 분석 라우터 생성 (document_clause_analysis.py)
2. 5개 엔드포인트 구현 (upload, analyze-reason, find-exceptions, search-clause, health)
3. 출처 추적 시스템 (source_references, citations)
4. 예외 키워드 하이라이팅 (7개 키워드)
5. Redis 통합 (document_analysis_redis와 공유)
6. 메인 라우터 등록
7. Import 테스트 통과
8. 전체 API 가이드 작성

### 🎯 달성한 목표
- **요구사항 1**: ✅ 사유·근거 분석 + 출처 표시
- **요구사항 2**: ✅ 예외 조항 검색 ("다만", "단서", "예외적으로")
- **Redis 사용**: ✅ document_analysis_redis와 공유
- **파일 분리**: ✅ 독립적인 라우터 파일
- **PDF 적합성**: ✅ 정부 문서 최적화

### 🚀 다음 작업
**이제 서버를 시작하고 실제 PDF로 테스트할 준비가 완료되었습니다!**

```bash
# 1. 서버 시작
poetry run start

# 2. Swagger UI 접속
http://localhost:8001/docs

# 3. "Document Clause Analysis (Redis)" 섹션에서 테스트
```

---

**작성일**: 2026-01-15
**작성자**: Claude Sonnet 4.5
**Router**: `/document-clause-analysis`
**엔드포인트 수**: 5개
**코드 라인 수**: 460줄
**문서 라인 수**: 500+줄
**완료율**: 100% (테스트 대기)
