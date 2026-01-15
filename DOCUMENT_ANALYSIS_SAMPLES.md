# 실무형 문서 분석 API Request Samples

PDF 문서 분석 엔드포인트 테스트를 위한 샘플 Request Body 모음입니다.
Swagger UI(http://localhost:8001/docs)에서 바로 복사하여 사용할 수 있습니다.

---

## 📋 목차

1. [문서 업로드](#1-문서-업로드)
2. [문서 요약](#2-문서-요약)
3. [문서 요약 (스트리밍)](#3-문서-요약-스트리밍)
4. [주요 이슈 추출](#4-주요-이슈-추출)
5. [자유 질의응답](#5-자유-질의응답)
6. [문서 목록 조회](#6-문서-목록-조회)
7. [사용 시나리오](#7-사용-시나리오)

---

## 1. 문서 업로드

### Endpoint: `POST /document-analysis/upload-from-docs`

docs 폴더에 배치된 PDF 파일을 인덱싱합니다.

#### 샘플 1: 정부 정책 문서

```json
{
  "doc_id": "policy_2025",
  "file_name": "Reprimand-sample-1.pdf"
}
```

#### 샘플 2: 기술 문서

```json
{
  "doc_id": "tech_spec",
  "file_name": "technical_specification.pdf"
}
```

#### 샘플 3: 보고서

```json
{
  "doc_id": "annual_report",
  "file_name": "2024_annual_report.pdf"
}
```

**응답 예시:**

```json
{
  "doc_id": "policy_2025",
  "file_name": "Reprimand-sample-1.pdf",
  "num_pages": 17,
  "total_nodes": 342,
  "child_nodes": 256,
  "execution_time_ms": 3456.78,
  "message": "PDF 파일이 성공적으로 인덱싱되었습니다."
}
```

---

## 2. 문서 요약

### Endpoint: `POST /document-analysis/summary`

문서의 목적과 핵심 내용을 한 문단으로 요약합니다.

#### 샘플 1: 기본 요약 (200자)

```json
{
  "doc_id": "policy_2025",
  "max_length": 200
}
```

#### 샘플 2: 짧은 요약 (100자)

```json
{
  "doc_id": "policy_2025",
  "max_length": 100
}
```

#### 샘플 3: 긴 요약 (500자)

```json
{
  "doc_id": "policy_2025",
  "max_length": 500
}
```

**응답 예시:**

```json
{
  "doc_id": "policy_2025",
  "summary": "중소벤처기업부는 2025년 소상공인 지원을 위해 역대 최대 규모인 5.9조원의 예산을 편성하였습니다. 기업가형 소상공인 육성, 디지털 역량 강화, 경영 부담 완화 등 7개 분야 23개 사업에 8,170억원을 투입하며, 특히 배달·택배비 지원, 브랜드 소상공인 육성 등 신규 사업을 도입하여 영세 소상공인의 경영 안정과 유망 소상공인의 성장을 동시에 지원합니다.",
  "summary_length": 189,
  "source_nodes_count": 5,
  "execution_time_ms": 2341.56,
  "explanation": "문서의 목적과 핵심 내용을 요약했습니다."
}
```

---

## 3. 문서 요약 (스트리밍)

### Endpoint: `POST /document-analysis/summary-streaming`

실시간 스트리밍 방식으로 요약을 제공합니다. (Server-Sent Events)

#### 샘플 1: 스트리밍 요약

```json
{
  "doc_id": "policy_2025",
  "max_length": 200
}
```

**응답 형식:** Server-Sent Events (SSE)

```
data: {"text": "중소벤처기업부는", "done": false}

data: {"text": " 2025년", "done": false}

data: {"text": " 소상공인", "done": false}

...

data: {"text": "", "done": true}
```

**프론트엔드 사용 예시:**

```javascript
const eventSource = new EventSource('/document-analysis/summary-streaming');

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.done) {
    eventSource.close();
  } else {
    console.log(data.text); // 스트리밍 텍스트 출력
  }
};
```

---

## 4. 주요 이슈 추출

### Endpoint: `POST /document-analysis/extract-issues`

문서에서 문제점, 개선사항, 변경내용 등을 추출합니다.

#### 샘플 1: 기본 이슈 추출

```json
{
  "doc_id": "policy_2025",
  "top_k": 8
}
```

#### 샘플 2: 상세 이슈 추출

```json
{
  "doc_id": "policy_2025",
  "top_k": 15
}
```

#### 샘플 3: 간단 이슈 추출

```json
{
  "doc_id": "policy_2025",
  "top_k": 5
}
```

**응답 예시:**

```json
{
  "doc_id": "policy_2025",
  "issues": "1. 기존 문제점:\n- 소상공인의 온라인 소비 증가와 배달·택배 비용 부담 증가\n- 위기 소상공인의 재기 지원 체계 미흡\n\n2. 2024년 대비 2025년 변경사항:\n- 희망리턴패키지 예산 937억원 대폭 확대 (1,513억→2,450억)\n- 점포철거비 지원 단가 및 금액 상향 (250만원→400만원)\n- 기업가형 소상공인 지원 예산 300억원 증가\n\n3. 신규 신설/확대 사업:\n- 배달·택배비 지원사업 신설 (2,037억원, 67.9만명 지원)\n- 브랜드 소상공인 육성(TOPS) 신설 (150억원, 3,000개사)\n- 혁신 소상공인 투자연계 신설 (300억원, 300개사)\n- 지역상권활력지원 신설 (20억원, 2개소)",
  "source_nodes": [
    {
      "score": 0.876,
      "text_preview": "위기 소상공인을 돕기 위한 희망리턴패키지 예산이 '24년 1,513억원에서 '25년 2,450억원으로 937억원 대폭 확대된다...",
      "metadata": {
        "node_type": "child",
        "parent_index": 3,
        "chunk_index": 2
      }
    }
  ],
  "total_source_nodes": 8,
  "execution_time_ms": 4567.89,
  "explanation": "문서에서 주요 이슈를 추출했습니다."
}
```

---

## 5. 자유 질의응답

### Endpoint: `POST /document-analysis/query`

인덱싱된 문서에 대해 자유롭게 질문할 수 있습니다.

#### 샘플 1: 예산 관련 질문

```json
{
  "doc_id": "policy_2025",
  "query": "2025년 소상공인 지원 예산 총 규모는 얼마인가요?",
  "streaming": false,
  "top_k": 5
}
```

#### 샘플 2: 신규 사업 질문

```json
{
  "doc_id": "policy_2025",
  "query": "신규로 도입되는 주요 사업은 무엇인가요?",
  "streaming": false,
  "top_k": 8
}
```

#### 샘플 3: 지원 대상 질문

```json
{
  "doc_id": "policy_2025",
  "query": "배달·택배비 지원 사업의 대상과 지원 금액은?",
  "streaming": false,
  "top_k": 5
}
```

#### 샘플 4: 스트리밍 질문

```json
{
  "doc_id": "policy_2025",
  "query": "희망리턴패키지 사업의 주요 변경사항을 자세히 설명해주세요.",
  "streaming": true,
  "top_k": 10
}
```

#### 샘플 5: 비교 질문

```json
{
  "doc_id": "policy_2025",
  "query": "2024년과 2025년의 가장 큰 차이점은 무엇인가요?",
  "streaming": false,
  "top_k": 10
}
```

**응답 예시 (streaming: false):**

```json
{
  "doc_id": "policy_2025",
  "query": "2025년 소상공인 지원 예산 총 규모는 얼마인가요?",
  "response": "2025년 소상공인 지원을 위한 정부 예산은 역대 최대 규모인 5.9조원으로 책정되었습니다. 이 중 중소벤처기업부의 공모사업은 7개 분야 23개 사업으로 8,170억원 규모입니다.",
  "source_nodes": [
    {
      "score": 0.923,
      "text_preview": "2025년 소상공인 지원을 위한 정부 예산은 역대 최대 규모인 5.9조원으로 책정되었으며..."
    }
  ],
  "execution_time_ms": 1234.56
}
```

---

## 6. 문서 목록 조회

### Endpoint: `GET /document-analysis/list-documents`

Request Body 불필요 (GET 요청)

**응답 예시:**

```json
{
  "total_documents": 3,
  "documents": [
    {
      "doc_id": "policy_2025",
      "file_name": "Reprimand-sample-1.pdf",
      "num_pages": 17,
      "total_nodes": 342,
      "child_nodes": 256,
      "created_at": "2024-01-15T10:30:00"
    },
    {
      "doc_id": "tech_spec",
      "file_name": "technical_specification.pdf",
      "num_pages": 25,
      "total_nodes": 458,
      "child_nodes": 342,
      "created_at": "2024-01-15T11:00:00"
    }
  ]
}
```

### Endpoint: `DELETE /document-analysis/delete-document/{doc_id}`

URL 경로에 doc_id 지정

**예시:** `DELETE /document-analysis/delete-document/policy_2025`

---

## 7. 사용 시나리오

### 시나리오 1: 정부 정책 문서 분석

```
1. 문서 업로드
   POST /document-analysis/upload-from-docs
   { "doc_id": "policy_2025", "file_name": "Reprimand-sample-1.pdf" }

2. 문서 요약 (스트리밍)
   POST /document-analysis/summary-streaming
   { "doc_id": "policy_2025", "max_length": 200 }

3. 주요 이슈 추출
   POST /document-analysis/extract-issues
   { "doc_id": "policy_2025", "top_k": 10 }

4. 구체적 질문
   POST /document-analysis/query
   { "doc_id": "policy_2025", "query": "배달·택배비 지원 대상은?", "streaming": false }
```

### 시나리오 2: 기술 문서 검색

```
1. 문서 업로드
   POST /document-analysis/upload-from-docs
   { "doc_id": "api_spec", "file_name": "api_specification.pdf" }

2. 특정 기능 검색
   POST /document-analysis/query
   { "doc_id": "api_spec", "query": "인증 방식은 무엇인가요?", "top_k": 5 }

3. 전체 개요 확인
   POST /document-analysis/summary
   { "doc_id": "api_spec", "max_length": 300 }
```

### 시나리오 3: 여러 문서 비교

```
1. 문서 A 업로드
   POST /document-analysis/upload-from-docs
   { "doc_id": "report_2024", "file_name": "2024_report.pdf" }

2. 문서 B 업로드
   POST /document-analysis/upload-from-docs
   { "doc_id": "report_2025", "file_name": "2025_report.pdf" }

3. 각 문서 요약
   POST /document-analysis/summary
   { "doc_id": "report_2024", "max_length": 200 }

   POST /document-analysis/summary
   { "doc_id": "report_2025", "max_length": 200 }

4. 동일 질문으로 비교
   POST /document-analysis/query
   { "doc_id": "report_2024", "query": "주요 성과는?", "streaming": false }

   POST /document-analysis/query
   { "doc_id": "report_2025", "query": "주요 성과는?", "streaming": false }
```

---

## 💡 사용 팁

### 1. 문서 ID 명명 규칙

- 의미 있는 이름 사용: `policy_2025`, `tech_spec_v2`, `annual_report_2024`
- 날짜 포함: `meeting_notes_20240115`
- 버전 포함: `api_spec_v3`

### 2. 최적의 top_k 값

- **간단한 질문**: top_k = 3~5
- **일반 질문**: top_k = 5~8
- **복잡한 질문**: top_k = 8~15
- **전체 문서 요약**: top_k = 10~20

### 3. 스트리밍 vs 일반 응답

- **스트리밍 권장**: 긴 요약, 사용자 경험 중요
- **일반 응답 권장**: 짧은 답변, API 통합, 테스트

### 4. 요약 길이 설정

- **짧은 요약**: 100자 (핵심만)
- **일반 요약**: 200자 (균형)
- **상세 요약**: 500자 (세부사항 포함)

---

## 🔗 관련 문서

- [LlamaIndex 완벽 가이드](./LLAMAINDEX_GUIDE.md)
- [LlamaIndex 샘플 모음](./LLAMAINDEX_REQUEST_SAMPLES.md)
- [독립 실행 예제](./src/examples/document_analysis_demo.py)

---

**작성일**: 2024-01-15
**버전**: 1.0
