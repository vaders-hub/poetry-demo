# 보고서 및 체크리스트 생성 API

## 📋 개요

정부 문서로부터 내부 보고용 요약 메모 및 실무자 체크리스트를 자동 생성하는 API

**사용 사례**:
- 상급자 보고용 요약 문서 자동 생성
- 실무자 업무 체크리스트 자동 생성
- 절차/준수사항/검토사항 체크리스트

---

## 🎯 주요 기능

### 1. 보고서 초안 생성
문서를 분석하여 내부 보고용 요약 메모를 자동 생성합니다.

**출력 구성**:
- 보고서 제목
- 전체 요약
- 주요 포인트 (5-7개)
- 권장 사항 (3-5개)

### 2. 체크리스트 생성
문서 내용을 바탕으로 실무자 체크리스트를 자동 생성합니다.

**체크리스트 유형**:
- `procedure`: 절차 체크리스트
- `compliance`: 준수사항 체크리스트
- `review`: 검토사항 체크리스트

### 3. 모호한 표현 분석
문서 내용 중 모호하거나 해석 여지가 있는 표현을 지적하고 이유를 설명합니다.

**출력 구성**:
- 모호한 표현 목록
- 각 표현의 위치 및 이유
- 영향도 (모두 high로 표시)
- 개선 제안

### 4. FAQ 생성
문서 내용을 Q&A 형식으로 재구성하여 자주 묻는 질문을 생성합니다.

**출력 구성**:
- 유동적 개수의 Q&A (3-10개)
- 모든 항목 "기본 정보" 카테고리로 분류
- 실무자/일반인 관점의 질문

---

## 📡 API 엔드포인트

### Base URL
```
http://localhost:8001/document-report-generation
```

---

### 1. POST `/upload`

문서 업로드 및 인덱스 생성

#### Request
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
    "total_nodes": 150,
    "child_nodes": 140,
    "status": "indexed_for_report_generation"
  },
  "message": "문서가 성공적으로 인덱싱되었습니다 (보고서 생성용)."
}
```

---

### 2. POST `/generate-report-summary`

보고서 초안 생성

#### Request
```json
{
  "doc_id": "reprimand-sample-1",
  "max_length": 500,
  "top_k": 20
}
```

#### Response
```json
{
  "success": true,
  "data": {
    "doc_id": "reprimand-sample-1",
    "report_type": "internal",
    "title": "공무원 징계 기준 요약",
    "summary": "이 문서는 공무원 징계 처분의 종류와 기준을 규정한 지침입니다...",
    "key_points": [
      "징계 종류: 파면, 해임, 정직, 감봉, 견책 총 5가지",
      "파면은 가장 엄격한 처분으로 퇴직급여 미지급 및 5년간 재임용 제한",
      "경감/가중 사유: 평소 행실, 고의/과실 여부, 자진 신고 등",
      "징계위원회 의결을 거쳐 최종 결정",
      "피징계자에게 소명 기회 부여 필수"
    ],
    "recommendations": [
      "징계 기준표를 반드시 참조하여 처분 수위 결정",
      "경감/가중 사유를 면밀히 검토하여 공정성 확보",
      "절차적 정당성 확보 (소명 기회, 위원회 의결 등)"
    ],
    "full_text": "...",
    "source_references": [...]
  },
  "message": "보고서 초안이 생성되었습니다."
}
```

---

### 3. POST `/generate-checklist`

체크리스트 생성

#### Request
```json
{
  "doc_id": "reprimand-sample-1",
  "checklist_type": "procedure",
  "top_k": 20
}
```

**Parameters**:
- `checklist_type`: `procedure` (절차), `compliance` (준수사항), `review` (검토사항)

#### Response
```json
{
  "success": true,
  "data": {
    "doc_id": "reprimand-sample-1",
    "checklist_type": "procedure",
    "checklist_title": "징계 절차 체크리스트",
    "items": [
      {
        "category": "사전 준비",
        "tasks": [
          "비위 사실 확인 및 증거 수집",
          "관련 법령 및 규정 검토",
          "징계 기준표 확인"
        ]
      },
      {
        "category": "주요 절차",
        "tasks": [
          "징계위원회 소집 (7일 전 통지)",
          "피징계자 소명 기회 부여",
          "위원회 의결 진행",
          "징계 결정 통보 (서면)"
        ]
      },
      {
        "category": "사후 조치",
        "tasks": [
          "불복 절차 안내",
          "징계 결과 기록 보관"
        ]
      }
    ],
    "critical_items": [
      "피징계자 소명 기회 반드시 부여 (절차적 정당성)",
      "징계위원회 의결 필수 (법적 요건)",
      "징계 기준표에 따른 처분 수위 결정"
    ],
    "full_text": "...",
    "source_references": [...]
  },
  "message": "체크리스트가 생성되었습니다 (procedure 유형)."
}
```

---

### 4. POST `/analyze-ambiguous-text`

모호한 표현 분석

#### Request
```json
{
  "doc_id": "reprimand-sample-1",
  "top_k": 20
}
```

#### Response
```json
{
  "success": true,
  "data": {
    "doc_id": "reprimand-sample-1",
    "ambiguous_expressions": [
      {
        "expression": "상당한 기간",
        "location": "제3조 제2항",
        "reason": "'상당한'이라는 표현이 주관적이며 구체적 기간이 명시되지 않음",
        "impact": "high",
        "suggestion": "구체적인 일수 또는 개월 수로 명시 (예: '30일 이상', '3개월 이내')"
      },
      {
        "expression": "중대한 과실",
        "location": "징계 기준표",
        "reason": "'중대한'의 판단 기준이 불명확하여 자의적 해석 가능",
        "impact": "high",
        "suggestion": "중대한 과실의 구체적 사례나 판단 기준 제시"
      }
    ],
    "total_found": 2,
    "high_impact": 2,
    "full_text": "...",
    "source_references": [...]
  },
  "message": "모호한 표현 분석이 완료되었습니다."
}
```

---

### 5. POST `/generate-faq`

FAQ 생성

#### Request
```json
{
  "doc_id": "reprimand-sample-1",
  "num_questions": 5,
  "top_k": 20
}
```

**Parameters**:
- `num_questions`: 생성할 FAQ 개수 (3-10개, 유동적)

#### Response
```json
{
  "success": true,
  "data": {
    "doc_id": "reprimand-sample-1",
    "faq_items": [
      {
        "question": "공무원 징계 처분에는 어떤 종류가 있나요?",
        "answer": "총 5가지 종류가 있습니다: 파면, 해임, 정직, 감봉, 견책. 파면이 가장 엄격한 처분이며 견책이 가장 가벼운 처분입니다.",
        "category": "기본 정보"
      },
      {
        "question": "파면과 해임의 차이는 무엇인가요?",
        "answer": "파면은 퇴직급여가 지급되지 않고 5년간 재임용이 제한되는 반면, 해임은 퇴직급여가 일부 지급되고 3년간 재임용이 제한됩니다.",
        "category": "기본 정보"
      }
    ],
    "total_questions": 5,
    "full_text": "...",
    "source_references": [...]
  },
  "message": "FAQ가 생성되었습니다 (5개)."
}
```

---

### 6. GET `/health`

Health Check

#### Response
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "redis_connected": true,
    "service": "document_report_generation",
    "features": [
      "report_summary_generation",
      "checklist_generation",
      "ambiguous_text_analysis",
      "faq_generation"
    ]
  },
  "message": "보고서 생성 API가 정상 작동 중입니다."
}
```

---

## 🧪 사용 예시

### Python 클라이언트
```python
import requests

BASE_URL = "http://localhost:8001/document-report-generation"

# 1. 문서 업로드
upload_response = requests.post(
    f"{BASE_URL}/upload",
    json={
        "doc_id": "reprimand-sample-1",
        "file_name": "Reprimand-sample-1.pdf"
    }
)

# 2. 보고서 생성
report_response = requests.post(
    f"{BASE_URL}/generate-report-summary",
    json={
        "doc_id": "reprimand-sample-1",
        "max_length": 500,
        "top_k": 20
    }
)
print("보고서 제목:", report_response.json()["data"]["title"])
print("주요 포인트:", report_response.json()["data"]["key_points"])

# 3. 체크리스트 생성
checklist_response = requests.post(
    f"{BASE_URL}/generate-checklist",
    json={
        "doc_id": "reprimand-sample-1",
        "checklist_type": "procedure",
        "top_k": 20
    }
)
print("체크리스트:", checklist_response.json()["data"]["items"])

# 4. 모호한 표현 분석
ambiguous_response = requests.post(
    f"{BASE_URL}/analyze-ambiguous-text",
    json={
        "doc_id": "reprimand-sample-1",
        "top_k": 20
    }
)
print("모호한 표현:", ambiguous_response.json()["data"]["ambiguous_expressions"])

# 5. FAQ 생성
faq_response = requests.post(
    f"{BASE_URL}/generate-faq",
    json={
        "doc_id": "reprimand-sample-1",
        "num_questions": 5,
        "top_k": 20
    }
)
print("FAQ 항목:", faq_response.json()["data"]["faq_items"])
```

---

## 🔧 기술 스택

- **FastAPI**: API 프레임워크
- **LlamaIndex**: 문서 인덱싱 및 검색
  - Hierarchical Node Parser (Parent: 2048, Child: 512)
  - Response Mode: `tree_summarize` (계층적 요약)
- **Redis**: 인덱스 저장소
- **OpenAI**: GPT-4o-mini (LLM), text-embedding-3-small (Embedding)

---

## 📚 관련 문서

- [조항 분석 API](./CLAUSE_ANALYSIS_API.md)
- [표 분석 API](./TABLE_ANALYSIS_API.md)
- [LlamaIndex 가이드](./LLAMAINDEX_GUIDE.md)
- [Redis 설정 가이드](./REDIS_SETUP_GUIDE.md)

---

## 📝 변경 이력

### 2026-01-16
- ✅ 초기 구현 완료
- ✅ 보고서 초안 생성 기능
- ✅ 체크리스트 생성 기능 (3가지 유형)
- ✅ 공통 유틸리티 함수 추가 (`generate_structured_query`)
- ✅ 모호한 표현 분석 기능 추가
- ✅ FAQ 생성 기능 추가 (유동적 개수 3-10개)
