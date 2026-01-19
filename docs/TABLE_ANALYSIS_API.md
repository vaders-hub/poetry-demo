# 표·항목 기반 분석 API

## 📋 개요

정부 문서의 표, 기준표, 비교표 등을 분석하는 전문 API

**구현 방식**: LlamaIndex 기본 기능 활용 (접근 1)
- 계층적 인덱싱으로 표 내용 처리
- 별도 테이블 파서 불필요
- LLM의 해석 능력 활용

---

## 🎯 주요 기능

### 1. 표 중요도 분석
표에서 가장 중요한 기준 N개를 추출하고 이유를 설명합니다.

### 2. 표 조건 비교
표의 조건들을 특정 관점(엄격함, 처벌 강도 등)에서 비교합니다.

---

## 🏗️ 아키텍처

### 파일 구조
```
src/
├── models/
│   └── document_analysis.py        # TableImportanceRequest, TableComparisonRequest
├── routers/
│   └── document_table_analysis.py  # 표 분석 라우터 (새 파일)
└── utils/
    ├── redis_client.py              # Redis 클라이언트 (공유)
    └── document_analysis.py         # 문서 분석 헬퍼 (공유)
```

### 저장소
- **Redis**: 인덱스 저장소 (document_clause_analysis와 공유 가능)

### 인덱싱 전략
- **Parent 청크**: 2048 chars (표 전체 구조 파악)
- **Child 청크**: 512 chars (세부 항목 검색)
- **Response Mode**:
  - 중요도 분석: `tree_summarize` (계층적 요약)
  - 조건 비교: `compact` (효율적 비교)

---

## 📡 API 엔드포인트

### Base URL
```
http://localhost:8001/document-table-analysis
```

---

### 1. POST `/upload`

문서 업로드 및 표 분석용 인덱스 생성

#### Request Body
```json
{
  "doc_id": "reprimand-sample-1",
  "file_name": "Reprimand-sample-1.pdf"
}
```

#### Response
```json
{
  "success": true,
  "data": {
    "doc_id": "reprimand-sample-1",
    "file_name": "Reprimand-sample-1.pdf",
    "node_count": 150,
    "status": "indexed_for_table_analysis"
  },
  "message": "문서가 성공적으로 인덱싱되었습니다 (표 분석용)."
}
```

---

### 2. POST `/analyze-table-importance`

표에서 가장 중요한 기준 N개 추출

#### Request Body
```json
{
  "doc_id": "reprimand-sample-1",
  "table_context": "징계 기준표",
  "top_n": 3,
  "top_k": 15
}
```

**Parameters**:
- `doc_id`: 문서 ID (필수)
- `table_context`: 표 관련 맥락 (선택, 예: "징계 기준표", "처분 사유별 기준")
- `top_n`: 추출할 중요 기준 개수 (기본값: 3, 범위: 1-10)
- `top_k`: 검색할 청크 개수 (기본값: 15, 범위: 5-30)

#### Response
```json
{
  "success": true,
  "data": {
    "doc_id": "reprimand-sample-1",
    "table_context": "징계 기준표",
    "top_n": 3,
    "analysis_result": "[1위] 기준명: 비위의 정도\n중요한 이유: 징계 처분의 가장 핵심적인 판단 기준으로, 비위의 경중에 따라 파면부터 경징계까지 차등 적용됩니다...\n\n[2위] 기준명: 고의 또는 과실 여부\n중요한 이유: ...\n\n[3위] 기준명: 평소 행실 및 근무성적\n중요한 이유: ...",
    "source_references": [
      {
        "reference_number": 1,
        "score": 0.8542,
        "text_preview": "비위의 정도가 심하거나 고의로 인한 경우에는 파면 또는 해임에 처한다...",
        "metadata": {
          "page": "3",
          "chunk_index": 45
        }
      },
      {
        "reference_number": 2,
        "score": 0.8123,
        "text_preview": "평소 행실과 근무성적이 우수한 경우 1단계 경감할 수 있다...",
        "metadata": {
          "page": "5",
          "chunk_index": 78
        }
      }
    ],
    "metadata": {
      "total_nodes_searched": 15,
      "file_name": "Reprimand-sample-1.pdf",
      "analyzed_at": "2026-01-16T09:00:00"
    }
  },
  "message": "표 중요도 분석 완료 (상위 3개)"
}
```

---

### 3. POST `/compare-table-criteria`

표의 조건들을 비교하여 특정 관점에서 가장 엄격한/관대한 기준 도출

#### Request Body
```json
{
  "doc_id": "reprimand-sample-1",
  "comparison_aspect": "엄격함",
  "table_context": "징계 기준표",
  "top_k": 15
}
```

**Parameters**:
- `doc_id`: 문서 ID (필수)
- `comparison_aspect`: 비교 관점 (기본값: "엄격함", 예: "처벌 강도", "적용 범위")
- `table_context`: 표 관련 맥락 (선택)
- `top_k`: 검색할 청크 개수 (기본값: 15, 범위: 5-30)

#### Response
```json
{
  "success": true,
  "data": {
    "doc_id": "reprimand-sample-1",
    "table_context": "징계 기준표",
    "comparison_aspect": "엄격함",
    "comparison_result": "[가장 엄격한 기준]\n기준명: 파면 (직위 해제 + 퇴직급여 미지급)\n이유: 모든 징계 처분 중 가장 중한 처분으로, 공무원 신분 상실과 함께 퇴직급여도 지급되지 않습니다...\n\n[다른 기준들과의 비교]\n- 해임: 파면과 유사하나 퇴직급여 일부 지급 가능\n- 정직: 신분 유지, 급여 미지급\n- 감봉: 신분 유지, 급여 감액\n- 견책: 신분 및 급여 유지, 경고 수준",
    "source_references": [
      {
        "reference_number": 1,
        "score": 0.8921,
        "text_preview": "파면: 공무원 관계에서 배제하며, 퇴직급여의 전부 또는 일부를 지급하지 아니한다...",
        "metadata": {
          "page": "2",
          "chunk_index": 23
        }
      }
    ],
    "metadata": {
      "total_nodes_searched": 15,
      "file_name": "Reprimand-sample-1.pdf",
      "analyzed_at": "2026-01-16T09:05:00"
    }
  },
  "message": "표 조건 비교 완료 ('엄격함' 관점)"
}
```

---

### 4. GET `/health`

API Health Check

#### Response
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "redis_connected": true,
    "service": "document_table_analysis",
    "features": [
      "table_importance_analysis",
      "table_criteria_comparison"
    ],
    "timestamp": "2026-01-16T09:10:00"
  },
  "message": "표 분석 API가 정상 작동 중입니다."
}
```

---

## 🧪 테스트 예시

### 1. 문서 업로드
```bash
curl -X POST http://localhost:8001/document-table-analysis/upload \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "reprimand-sample-1",
    "file_name": "Reprimand-sample-1.pdf"
  }'
```

### 2. 표 중요도 분석
```bash
curl -X POST http://localhost:8001/document-table-analysis/analyze-table-importance \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "reprimand-sample-1",
    "table_context": "징계 기준표",
    "top_n": 3,
    "top_k": 15
  }'
```

### 3. 표 조건 비교
```bash
curl -X POST http://localhost:8001/document-table-analysis/compare-table-criteria \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "reprimand-sample-1",
    "comparison_aspect": "엄격함",
    "table_context": "징계 기준표",
    "top_k": 15
  }'
```

---

## 🔧 기술 스택

- **FastAPI**: API 프레임워크
- **LlamaIndex**: 문서 인덱싱 및 검색
  - Hierarchical Node Parser (Parent: 2048, Child: 512)
  - OpenAI Embeddings (text-embedding-3-small)
  - OpenAI LLM (gpt-4o-mini)
- **Redis**: 인덱스 저장소
- **Pydantic**: 요청/응답 검증

---

## 🎨 설계 특징

### 1. LlamaIndex 기본 기능 활용
- 별도 테이블 파서 불필요
- 텍스트 기반 표 분석
- LLM의 강력한 해석 능력 활용

### 2. 계층적 인덱싱
- Parent 청크로 표 전체 구조 파악
- Child 청크로 세부 항목 검색

### 3. Response Mode 최적화
- **중요도 분석**: `tree_summarize` - 계층적 요약으로 표 전체 이해
- **조건 비교**: `compact` - 효율적 비교 분석

### 4. 코드 재사용
- Redis 클라이언트: `src/utils/redis_client.py` 공유
- 문서 분석 헬퍼: `src/utils/document_analysis.py` 공유
- Models: `src/models/document_analysis.py` 공유

---

## 📊 제한사항

### 현재 구현 (접근 1)
- 복잡한 다단계 표의 정확도가 낮을 수 있음
- 표 구조 자체(행/열)를 명시적으로 인식하지 못함
- 텍스트로 추출된 표 내용에 의존

### 향후 개선 (접근 2)
필요 시 전문 테이블 파서 추가 가능:
- `pdfplumber`: PDF 표 추출
- `camelot-py`: 고급 표 파싱
- 표 구조를 명시적으로 인식
- 행/열 기반 정확한 비교

---

## 🚀 다음 단계

### 추가 가능한 기능
1. **표 검색** (`/search-table`)
   - 특정 조건에 해당하는 표 항목 검색
   - 예: "파면 사유가 무엇인가요?"

2. **표 요약** (`/summarize-table`)
   - 표 전체 내용을 간단히 요약
   - 주요 항목만 추출

3. **표 구조 분석** (`/analyze-table-structure`)
   - 표의 행/열 개수, 제목 등 구조 정보
   - 전문 테이블 파서 필요

---

## 📚 관련 문서

- [조항 분석 API](./CLAUSE_ANALYSIS_API.md)
- [LlamaIndex 가이드](./LLAMAINDEX_GUIDE.md)
- [Redis 설정 가이드](./REDIS_SETUP_GUIDE.md)
- [Response Wrapper 가이드](./RESPONSE_WRAPPER_GUIDE.md)

---

## 📝 변경 이력

### 2026-01-16
- ✅ 초기 구현 완료 (접근 1: LlamaIndex 기본 기능)
- ✅ 표 중요도 분석 엔드포인트
- ✅ 표 조건 비교 엔드포인트
- ✅ Models 분리 (src/models/document_analysis.py)
- ✅ Redis 클라이언트 공유
- ✅ 문서화 완료
