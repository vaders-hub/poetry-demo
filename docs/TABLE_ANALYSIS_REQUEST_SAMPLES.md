# 표 분석 API 요청 샘플

## 📋 개요

표·항목 기반 분석 API의 실제 사용 예시 모음

---

## 🔄 기본 워크플로우

### 1단계: 문서 업로드
### 2단계: 표 중요도 분석
### 3단계: 표 조건 비교

---

## 📤 1. 문서 업로드

### Request
```bash
POST http://localhost:8001/document-table-analysis/upload
Content-Type: application/json

{
  "doc_id": "reprimand-sample-1",
  "file_name": "Reprimand-sample-1.pdf"
}
```

### Response
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

## 📊 2. 표 중요도 분석

### 사례 1: 징계 기준표에서 중요한 기준 3가지

#### Request
```bash
POST http://localhost:8001/document-table-analysis/analyze-table-importance
Content-Type: application/json

{
  "doc_id": "reprimand-sample-1",
  "table_context": "징계 기준표",
  "top_n": 3,
  "top_k": 15
}
```

#### Response (예상)
```json
{
  "success": true,
  "data": {
    "doc_id": "reprimand-sample-1",
    "table_context": "징계 기준표",
    "top_n": 3,
    "analysis_result": "[1위] 기준명: 비위의 정도\n중요한 이유: 징계 처분의 가장 핵심적인 판단 기준으로, 비위의 경중에 따라 파면부터 경징계까지 차등 적용됩니다. 공무원법 제78조에 따라 비위의 정도가 심한 경우 파면 또는 해임에 처할 수 있습니다.\n표 내용: '비위의 정도가 심하거나 고의로 인한 경우에는 파면 또는 해임에 처한다'\n\n[2위] 기준명: 고의 또는 과실 여부\n중요한 이유: 동일한 비위 행위라도 고의성 유무에 따라 처분 수위가 크게 달라집니다. 고의적 비위는 가중 처분, 과실에 의한 비위는 경감 처분의 근거가 됩니다.\n표 내용: '고의로 인한 비위는 1단계 가중, 과실로 인한 비위는 1단계 경감할 수 있다'\n\n[3위] 기준명: 평소 행실 및 근무성적\n중요한 이유: 비위 행위 이전의 근무 태도와 성적이 우수한 경우 정상참작 사유로 인정되어 처분을 경감할 수 있는 근거가 됩니다.\n표 내용: '평소 행실과 근무성적이 우수한 경우 1단계 경감할 수 있다'",
    "source_references": [
      {
        "reference_number": 1,
        "score": 0.8542,
        "text_preview": "비위의 정도가 심하거나 고의로 인한 경우에는 파면 또는 해임에 처한다. 다만, 정상참작의 사유가 있는 경우에는...",
        "metadata": {
          "page": "3",
          "chunk_index": 45
        }
      },
      {
        "reference_number": 2,
        "score": 0.8123,
        "text_preview": "평소 행실과 근무성적이 우수한 경우 1단계 경감할 수 있다. 이 경우 징계위원회의 의결을 거쳐야 한다...",
        "metadata": {
          "page": "5",
          "chunk_index": 78
        }
      },
      {
        "reference_number": 3,
        "score": 0.7895,
        "text_preview": "고의로 인한 비위는 1단계 가중, 과실로 인한 비위는 1단계 경감할 수 있다...",
        "metadata": {
          "page": "4",
          "chunk_index": 62
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

### 사례 2: 처분 종류별 효과 비교표에서 중요 항목 5가지

#### Request
```bash
POST http://localhost:8001/document-table-analysis/analyze-table-importance
Content-Type: application/json

{
  "doc_id": "reprimand-sample-1",
  "table_context": "처분 종류별 효과 비교표",
  "top_n": 5,
  "top_k": 20
}
```

---

### 사례 3: 맥락 없이 전체 표 분석

#### Request
```bash
POST http://localhost:8001/document-table-analysis/analyze-table-importance
Content-Type: application/json

{
  "doc_id": "reprimand-sample-1",
  "table_context": "",
  "top_n": 3,
  "top_k": 15
}
```

---

## ⚖️ 3. 표 조건 비교

### 사례 1: 가장 엄격한 기준 찾기

#### Request
```bash
POST http://localhost:8001/document-table-analysis/compare-table-criteria
Content-Type: application/json

{
  "doc_id": "reprimand-sample-1",
  "comparison_aspect": "엄격함",
  "table_context": "징계 기준표",
  "top_k": 15
}
```

#### Response (예상)
```json
{
  "success": true,
  "data": {
    "doc_id": "reprimand-sample-1",
    "table_context": "징계 기준표",
    "comparison_aspect": "엄격함",
    "comparison_result": "[가장 엄격한 기준]\n기준명: 파면 (직위 해제 + 퇴직급여 미지급)\n이유: 모든 징계 처분 중 가장 중한 처분으로, 공무원 신분을 완전히 상실하며 퇴직급여의 전부 또는 일부를 지급하지 않습니다. 복직이 불가능하며, 5년간 공무원 재임용이 제한됩니다.\n표 내용: '파면: 공무원 관계에서 배제하며, 퇴직급여의 전부 또는 일부를 지급하지 아니한다. 파면된 자는 5년간 공무원으로 임용될 수 없다.'\n\n[다른 기준들과의 비교]\n- 해임 (2순위 엄격): 파면과 유사하나 퇴직급여 일부 지급 가능, 3년간 재임용 제한\n- 정직 (3순위 엄격): 신분 유지되나 1개월~3개월 직무 정지 및 급여 미지급\n- 감봉 (4순위 엄격): 신분 유지, 1개월~3개월 급여 1/3 감액\n- 견책 (5순위 엄격): 신분 및 급여 유지, 경고 수준의 징계\n\n상대적 엄격함 정도:\n파면 > 해임 > 정직 > 감봉 > 견책\n\n파면이 가장 엄격한 이유:\n1. 공무원 신분 완전 상실 (해임도 동일)\n2. 퇴직급여 전액 미지급 가능 (해임은 일부 지급)\n3. 재임용 제한 기간 최장 (5년)",
    "source_references": [
      {
        "reference_number": 1,
        "score": 0.8921,
        "text_preview": "파면: 공무원 관계에서 배제하며, 퇴직급여의 전부 또는 일부를 지급하지 아니한다. 파면된 자는 5년간 공무원으로 임용될 수 없다...",
        "metadata": {
          "page": "2",
          "chunk_index": 23
        }
      },
      {
        "reference_number": 2,
        "score": 0.8654,
        "text_preview": "해임: 공무원 관계에서 배제한다. 해임된 자는 3년간 공무원으로 임용될 수 없다. 다만, 퇴직급여는 법령에 따라 지급할 수 있다...",
        "metadata": {
          "page": "2",
          "chunk_index": 24
        }
      },
      {
        "reference_number": 3,
        "score": 0.8234,
        "text_preview": "정직: 1개월 이상 3개월 이하의 기간 동안 공무원의 신분은 보유하나 직무에 종사하지 못하며 보수의 전액을 감한다...",
        "metadata": {
          "page": "2",
          "chunk_index": 25
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

### 사례 2: 가장 관대한 기준 찾기

#### Request
```bash
POST http://localhost:8001/document-table-analysis/compare-table-criteria
Content-Type: application/json

{
  "doc_id": "reprimand-sample-1",
  "comparison_aspect": "관대함",
  "table_context": "징계 기준표",
  "top_k": 15
}
```

---

### 사례 3: 처벌 강도 비교

#### Request
```bash
POST http://localhost:8001/document-table-analysis/compare-table-criteria
Content-Type: application/json

{
  "doc_id": "reprimand-sample-1",
  "comparison_aspect": "처벌 강도",
  "table_context": "징계 기준표",
  "top_k": 20
}
```

---

### 사례 4: 적용 범위 비교

#### Request
```bash
POST http://localhost:8001/document-table-analysis/compare-table-criteria
Content-Type: application/json

{
  "doc_id": "reprimand-sample-1",
  "comparison_aspect": "적용 범위",
  "table_context": "경감 및 가중 사유표",
  "top_k": 15
}
```

---

## ❤️ 4. Health Check

### Request
```bash
GET http://localhost:8001/document-table-analysis/health
```

### Response
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

## 🔧 실전 사용 팁

### 1. table_context 활용
- **명시적 지정**: 문서에 여러 표가 있을 때 특정 표 지정
- **빈 문자열**: 전체 표를 대상으로 분석

### 2. top_n 설정
- **3개**: 가장 일반적, 핵심만 추출
- **5개**: 더 자세한 분석
- **10개**: 표 전체 항목 파악

### 3. top_k 설정
- **15개**: 기본값, 균형잡힌 검색
- **20-30개**: 복잡한 표, 더 많은 맥락 필요
- **5-10개**: 간단한 표, 빠른 응답

### 4. comparison_aspect 예시
- **엄격함**: 가장 엄격한 조건 찾기
- **관대함**: 가장 관대한 조건 찾기
- **처벌 강도**: 처벌 수위 비교
- **적용 범위**: 적용 대상이 가장 넓은 조건
- **절차 복잡도**: 절차가 가장 복잡한 조건

---

## 📊 응답 데이터 활용

### source_references 활용
```python
for ref in response["data"]["source_references"]:
    print(f"참조 {ref['reference_number']}: 유사도 {ref['score']}")
    print(f"페이지: {ref['metadata']['page']}")
    print(f"내용: {ref['text_preview']}")
    print("---")
```

### analysis_result 파싱
```python
result = response["data"]["analysis_result"]

# [1위], [2위] 등으로 분리
items = result.split("\n\n")
for item in items:
    if item.startswith("["):
        print(item)
```

---

## 🧪 Python 클라이언트 예시

### 전체 워크플로우
```python
import requests

BASE_URL = "http://localhost:8001/document-table-analysis"

# 1. 문서 업로드
upload_response = requests.post(
    f"{BASE_URL}/upload",
    json={
        "doc_id": "reprimand-sample-1",
        "file_name": "Reprimand-sample-1.pdf"
    }
)
print("Upload:", upload_response.json())

# 2. 표 중요도 분석
importance_response = requests.post(
    f"{BASE_URL}/analyze-table-importance",
    json={
        "doc_id": "reprimand-sample-1",
        "table_context": "징계 기준표",
        "top_n": 3,
        "top_k": 15
    }
)
print("Importance:", importance_response.json()["data"]["analysis_result"])

# 3. 표 조건 비교
comparison_response = requests.post(
    f"{BASE_URL}/compare-table-criteria",
    json={
        "doc_id": "reprimand-sample-1",
        "comparison_aspect": "엄격함",
        "table_context": "징계 기준표",
        "top_k": 15
    }
)
print("Comparison:", comparison_response.json()["data"]["comparison_result"])
```

---

## 📚 관련 문서

- [표 분석 API 문서](./TABLE_ANALYSIS_API.md)
- [조항 분석 API 요청 샘플](./CLAUSE_ANALYSIS_REQUEST_SAMPLES.md)
- [LlamaIndex 가이드](./LLAMAINDEX_GUIDE.md)
