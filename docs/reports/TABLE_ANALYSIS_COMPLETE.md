# 표·항목 기반 분석 API 개발 완료 보고서

## 📋 작업 개요

**작업 기간**: 2026-01-16
**작업 유형**: 신규 기능 개발
**구현 방식**: 접근 1 - LlamaIndex 기본 기능 활용

---

## ✅ 완료된 작업

### 1. Request Models 추가
**파일**: `src/models/document_analysis.py`

```python
# 추가된 모델 (2개)
class TableImportanceRequest(BaseModel):
    """표 중요도 분석 요청"""
    doc_id: str
    table_context: str = ""  # 표 맥락 (선택)
    top_n: int = 3           # 중요 기준 개수
    top_k: int = 15          # 검색 청크 개수

class TableComparisonRequest(BaseModel):
    """표 조건 비교 요청"""
    doc_id: str
    comparison_aspect: str = "엄격함"  # 비교 관점
    table_context: str = ""            # 표 맥락 (선택)
    top_k: int = 15                    # 검색 청크 개수
```

---

### 2. 새 라우터 파일 생성
**파일**: `src/routers/document_table_analysis.py` (새 파일)

**엔드포인트 (4개)**:
1. `POST /upload` - 문서 업로드 및 표 분석용 인덱스 생성
2. `POST /analyze-table-importance` - 표 중요도 분석
3. `POST /compare-table-criteria` - 표 조건 비교
4. `GET /health` - Health Check

**코드 재사용**:
- Redis 클라이언트: `src/utils/redis_client.py` 공유
- 문서 분석 헬퍼: `src/utils/document_analysis.py` 공유
- Models: `src/models/document_analysis.py` 공유

---

### 3. 라우터 등록
**파일**: `src/router.py`

```python
from src.routers import document_table_analysis

app.include_router(document_table_analysis.router)
```

**등록된 라우트**:
```
/document-table-analysis/upload
/document-table-analysis/analyze-table-importance
/document-table-analysis/compare-table-criteria
/document-table-analysis/health
```

---

### 4. 문서화 완료

#### 4.1 API 문서
**파일**: `docs/TABLE_ANALYSIS_API.md`

**내용**:
- 개요 및 아키텍처
- 엔드포인트 상세 설명
- Request/Response 예시
- 기술 스택
- 설계 특징 및 제한사항
- 향후 개선 방안

#### 4.2 요청 샘플
**파일**: `docs/TABLE_ANALYSIS_REQUEST_SAMPLES.md`

**내용**:
- 기본 워크플로우
- 표 중요도 분석 샘플 (3가지 사례)
- 표 조건 비교 샘플 (4가지 사례)
- Python 클라이언트 예시
- 실전 사용 팁

#### 4.3 문서 인덱스 업데이트
**파일**: `docs/README.md`

- 표 분석 API 문서 추가
- 카테고리별 분류 업데이트
- 총 문서 수: 17개 → 19개

---

## 🎯 구현된 기능

### 1. 표 중요도 분석 (`/analyze-table-importance`)

**목적**: 표에서 가장 중요한 기준 N개 추출

**예시 질문**:
- "징계 기준표에서 가장 중요한 기준 3가지는?"
- "처분 사유별 기준표에서 핵심 항목은?"

**Response 형식**:
```
[1위] 기준명: 비위의 정도
중요한 이유: 징계 처분의 가장 핵심적인 판단 기준...
표 내용: '비위의 정도가 심하거나...'

[2위] 기준명: 고의 또는 과실 여부
중요한 이유: ...
```

**특징**:
- `tree_summarize` 모드로 계층적 요약
- 소스 참조 제공 (reference_number, score, text_preview)
- 표 맥락 지정 가능 (table_context)

---

### 2. 표 조건 비교 (`/compare-table-criteria`)

**목적**: 표의 조건들을 특정 관점에서 비교

**예시 질문**:
- "징계 기준표에서 가장 엄격한 조건은?"
- "처분 사유별로 비교했을 때 가장 강한 처벌은?"

**비교 관점 예시**:
- `엄격함`: 가장 엄격한 조건
- `관대함`: 가장 관대한 조건
- `처벌 강도`: 처벌 수위 비교
- `적용 범위`: 적용 대상이 가장 넓은 조건

**Response 형식**:
```
[가장 엄격한 기준]
기준명: 파면 (직위 해제 + 퇴직급여 미지급)
이유: 모든 징계 처분 중 가장 중한 처분...
표 내용: '파면: 공무원 관계에서 배제하며...'

[다른 기준들과의 비교]
- 해임: 파면과 유사하나 퇴직급여 일부 지급 가능
- 정직: 신분 유지, 급여 미지급
- 감봉: 신분 유지, 급여 감액
```

**특징**:
- `compact` 모드로 효율적 비교
- 상대적 순위 제공
- 차이점 명시

---

## 🏗️ 기술적 특징

### 1. 계층적 인덱싱
```python
# Parent 청크: 2048 chars (표 전체 구조 파악)
# Child 청크: 512 chars (세부 항목 검색)
index, node_count = create_hierarchical_index(
    documents=documents,
    parent_chunk_size=2048,
    child_chunk_size=512,
)
```

**이유**:
- 표 전체 맥락 파악 (Parent)
- 세부 항목 정밀 검색 (Child)

---

### 2. Response Mode 최적화

#### 중요도 분석: `tree_summarize`
```python
query_engine = index.as_query_engine(
    similarity_top_k=request.top_k,
    response_mode="tree_summarize",  # 계층적 요약
)
```

**이유**: 표 전체를 이해하고 중요도 순위 매기기

#### 조건 비교: `compact`
```python
query_engine = index.as_query_engine(
    similarity_top_k=request.top_k,
    response_mode="compact",  # 효율적 비교
)
```

**이유**: 여러 조건을 효율적으로 비교

---

### 3. 코드 재사용

#### Redis 클라이언트 공유
```python
from src.utils import get_redis_client, ping_redis
```

**효과**: 중복 코드 제거, 일관된 Redis 관리

#### 문서 분석 헬퍼 공유
```python
from src.utils.document_analysis import (
    load_pdf_from_path,
    create_hierarchical_index,
)
```

**효과**: 동일한 인덱싱 전략 사용

---

## 📊 파일 변경 사항

### 신규 파일 (3개)
1. `src/routers/document_table_analysis.py` - 표 분석 라우터 (350줄)
2. `docs/TABLE_ANALYSIS_API.md` - API 문서 (450줄)
3. `docs/TABLE_ANALYSIS_REQUEST_SAMPLES.md` - 요청 샘플 (550줄)

### 수정 파일 (3개)
1. `src/models/document_analysis.py` - 모델 2개 추가 (+27줄)
2. `src/router.py` - 라우터 등록 (+2줄)
3. `docs/README.md` - 문서 인덱스 업데이트 (+10줄)

### 총 코드 증가
- 라우터: +350줄
- 모델: +27줄
- 문서: +1000줄
- **총계**: +1377줄

---

## 🧪 검증 결과

### Import 테스트
```bash
✅ poetry run python -c "from src.routers import document_table_analysis"
✅ poetry run python -c "from src.models.document_analysis import TableImportanceRequest, TableComparisonRequest"
```

### 라우트 등록 확인
```bash
✅ /document-table-analysis/upload
✅ /document-table-analysis/analyze-table-importance
✅ /document-table-analysis/compare-table-criteria
✅ /document-table-analysis/health
```

---

## 🎨 설계 결정

### 접근 1 선택 (LlamaIndex 기본 기능)

**선택 이유**:
1. 별도 테이블 파서 불필요
2. 현재 코드에 쉽게 통합 가능
3. 빠른 구현 가능
4. LLM의 강력한 해석 능력 활용

**장점**:
- 텍스트 기반 표 분석 가능
- 구현 복잡도 낮음
- 유지보수 용이

**제한사항**:
- 복잡한 다단계 표의 정확도가 낮을 수 있음
- 표 구조 자체(행/열)를 명시적으로 인식하지 못함

**향후 개선 (필요 시)**:
- 접근 2: 전문 테이블 파서 추가 (`pdfplumber`, `camelot-py`)
- 표 구조 명시적 인식
- 행/열 기반 정확한 비교

---

### 새 파일로 분리

**이유**:
- `document_clause_analysis.py`와 기능 분리
- 각 파일의 책임 명확화
- 향후 확장성 고려

**효과**:
- 코드 가독성 향상
- 독립적 테스트 가능
- 모듈화된 구조

---

## 📚 문서화 전략

### API 문서 (TABLE_ANALYSIS_API.md)
- 개요 및 아키텍처 설명
- 엔드포인트 상세 문서
- 기술 스택 명시
- 제한사항 및 향후 개선 방안

### 요청 샘플 (TABLE_ANALYSIS_REQUEST_SAMPLES.md)
- 실제 사용 예시 중심
- 4가지 비교 관점 샘플
- Python 클라이언트 코드
- 실전 사용 팁

### 문서 인덱스 업데이트
- docs/README.md에 새 문서 추가
- 카테고리별 분류
- 빠른 링크 제공

---

## 🚀 다음 단계 (향후 개선)

### 추가 가능한 기능
1. **표 검색** (`/search-table`)
   - 특정 조건에 해당하는 표 항목 검색
   - 예: "파면 사유가 무엇인가요?"

2. **표 요약** (`/summarize-table`)
   - 표 전체 내용을 간단히 요약
   - 주요 항목만 추출

3. **표 구조 분석** (`/analyze-table-structure`)
   - 표의 행/열 개수, 제목 등 구조 정보
   - 전문 테이블 파서 필요 (접근 2)

### 정확도 개선 (접근 2)
필요 시 전문 테이블 파서 추가:
```python
# pdfplumber 또는 camelot-py 사용
import pdfplumber

with pdfplumber.open(pdf_path) as pdf:
    for page in pdf.pages:
        tables = page.extract_tables()
        # 표 구조 명시적 처리
```

---

## 📝 주요 의사결정

### 1. 접근 1 vs 접근 2
**결정**: 접근 1 (LlamaIndex 기본 기능)
**이유**: 빠른 구현, 낮은 복잡도, 충분한 정확도

### 2. 새 파일 생성 vs 기존 파일 확장
**결정**: 새 파일 생성 (`document_table_analysis.py`)
**이유**: 기능 분리, 코드 가독성, 모듈화

### 3. Response Mode 선택
**결정**:
- 중요도 분석: `tree_summarize`
- 조건 비교: `compact`

**이유**: 각 작업 특성에 최적화

### 4. 계층적 인덱싱 파라미터
**결정**:
- Parent: 2048 chars
- Child: 512 chars

**이유**: 표 전체 파악 + 세부 검색 균형

---

## 🎯 성공 지표

### 코드 품질
- ✅ 모든 imports 성공
- ✅ 라우트 정상 등록
- ✅ 코드 재사용 (Redis, 헬퍼 함수)
- ✅ Pydantic 검증 적용

### 문서화
- ✅ API 문서 완성
- ✅ 요청 샘플 완성
- ✅ Python 클라이언트 예시 제공
- ✅ 문서 인덱스 업데이트

### 기능성
- ✅ 표 중요도 분석 구현
- ✅ 표 조건 비교 구현
- ✅ 소스 참조 제공
- ✅ 유연한 파라미터 설정

---

## 🔗 관련 파일

### 코드
- `src/routers/document_table_analysis.py`
- `src/models/document_analysis.py`
- `src/router.py`

### 문서
- `docs/TABLE_ANALYSIS_API.md`
- `docs/TABLE_ANALYSIS_REQUEST_SAMPLES.md`
- `docs/README.md`

### 유틸리티 (공유)
- `src/utils/redis_client.py`
- `src/utils/document_analysis.py`

---

## 📅 작업 이력

### 2026-01-16
- ✅ Request models 추가 (TableImportanceRequest, TableComparisonRequest)
- ✅ document_table_analysis.py 라우터 생성 (350줄)
- ✅ 표 중요도 분석 엔드포인트 구현
- ✅ 표 조건 비교 엔드포인트 구현
- ✅ main.py에 라우터 등록
- ✅ Import 테스트 및 검증 완료
- ✅ API 문서 작성 (TABLE_ANALYSIS_API.md)
- ✅ 요청 샘플 작성 (TABLE_ANALYSIS_REQUEST_SAMPLES.md)
- ✅ docs/README.md 업데이트

---

## ✨ 결론

표·항목 기반 분석 API가 성공적으로 구현되었습니다.

**주요 성과**:
1. 2개의 핵심 기능 구현 (중요도 분석, 조건 비교)
2. 코드 재사용을 통한 효율적 구현
3. 포괄적인 문서화 완료
4. 향후 확장 가능한 구조 설계

**기술적 하이라이트**:
- LlamaIndex 기본 기능으로 표 분석 구현
- 계층적 인덱싱 전략 (Parent: 2048, Child: 512)
- Response Mode 최적화 (tree_summarize, compact)
- 유틸리티 공유로 중복 제거

**다음 단계**:
- 실제 사용 후 피드백 수집
- 정확도 평가
- 필요 시 접근 2 (전문 테이블 파서) 검토

---

**작성자**: Claude Sonnet 4.5
**작성일**: 2026-01-16
**문서 버전**: 1.0.0
