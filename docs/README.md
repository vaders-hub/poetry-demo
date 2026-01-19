# Poetry Demo 문서 디렉토리

이 디렉토리는 프로젝트의 모든 문서를 관리합니다.

## 📁 디렉토리 구조

```
docs/
├── README.md                          # 이 파일
├── reports/                           # 개발 작업 보고서
│   ├── RESPONSE_WRAPPER_STATUS.md     # Response Wrapper 적용 현황
│   ├── RESPONSE_WRAPPER_APPLIED.md    # Response Wrapper 적용 상세
│   ├── RESPONSE_WRAPPER_COMPLETE.md   # Response Wrapper 완료 보고서
│   ├── SESSION_SUMMARY.md             # 세션 요약
│   ├── CLAUSE_ANALYSIS_COMPLETE.md    # 조항 분석 기능 완료
│   ├── REFACTORING_COMPLETE.md        # 모델/유틸 분리 리팩토링
│   └── REDIS_CLIENT_REFACTORING.md    # Redis 클라이언트 공통화
│
├── RESPONSE_WRAPPER_GUIDE.md          # Response Wrapper 사용 가이드
├── ASYNC_LCEL_GUIDE.md                # LangChain LCEL 비동기 가이드
├── LLAMAINDEX_GUIDE.md                # LlamaIndex 사용 가이드
├── REDIS_SETUP_GUIDE.md               # Redis 설정 가이드
├── MCP_GUIDE.md                       # MCP (Model Context Protocol) 가이드
│
├── CLAUSE_ANALYSIS_API.md             # 조항 분석 API 문서
├── TABLE_ANALYSIS_API.md              # 표 분석 API 문서
├── TABLE_ANALYSIS_REQUEST_SAMPLES.md  # 표 분석 요청 샘플
├── DOCUMENT_ANALYSIS_SAMPLES.md       # 문서 분석 샘플 코드
├── LCEL_REQUEST_SAMPLES.md            # LCEL 요청 샘플
└── LLAMAINDEX_REQUEST_SAMPLES.md      # LlamaIndex 요청 샘플
```

---

## 📚 문서 카테고리

### 1. 개발 보고서 (`reports/`)

프로젝트 개발 과정에서 작성된 작업 완료 보고서입니다.

#### Response Wrapper 관련
- **RESPONSE_WRAPPER_STATUS.md**: 초기 적용 현황 분석
- **RESPONSE_WRAPPER_APPLIED.md**: 적용 상세 내역
- **RESPONSE_WRAPPER_COMPLETE.md**: 전체 완료 보고서 (78% 완료)

#### 조항 분석 기능
- **CLAUSE_ANALYSIS_COMPLETE.md**: 조항 분석 API 개발 완료 보고서
  - 사유 및 근거 분석
  - 예외 조항 검색
  - 특정 조항 검색

#### 리팩토링 작업
- **REFACTORING_COMPLETE.md**: 모델/헬퍼 함수 분리
- **REDIS_CLIENT_REFACTORING.md**: Redis 클라이언트 공통화 (22줄 중복 제거)

#### 세션 요약
- **SESSION_SUMMARY.md**: 전체 작업 세션 요약

---

### 2. 사용 가이드

프로젝트 개발 시 참고할 수 있는 기술 가이드입니다.

#### 백엔드 패턴
- **RESPONSE_WRAPPER_GUIDE.md**: 표준 API 응답 형식 가이드
  - `success_response()`, `error_response()`, `created_response()`
  - 사용 예시 및 베스트 프랙티스

#### LangChain & LlamaIndex
- **ASYNC_LCEL_GUIDE.md**: LangChain LCEL 비동기 처리 가이드
  - Runnable 인터페이스
  - Streaming, Batch 처리
- **LLAMAINDEX_GUIDE.md**: LlamaIndex 문서 인덱싱 가이드
  - 계층적 인덱싱
  - Query Engine 사용법

#### 인프라
- **REDIS_SETUP_GUIDE.md**: Redis 설치 및 설정
  - Windows/Linux/Mac 설치 방법
  - 연결 테스트
- **MCP_GUIDE.md**: Model Context Protocol 가이드
  - MCP 서버 설정
  - Tool 사용법

---

### 3. API 문서

각 API의 사용법과 샘플 요청입니다.

#### 문서 분석 API
- **CLAUSE_ANALYSIS_API.md**: 조항 분석 API 전체 문서
  - 사유 및 근거 분석
  - 예외 조항 검색
  - 특정 조항 검색
  - Request/Response 예시
  - 문제 해결 가이드

- **TABLE_ANALYSIS_API.md**: 표 분석 API 전체 문서 (NEW)
  - 표 중요도 분석 (가장 중요한 기준 N개 추출)
  - 표 조건 비교 (엄격함, 관대함 등)
  - 계층적 인덱싱 전략
  - Python 코드 샘플

- **TABLE_ANALYSIS_REQUEST_SAMPLES.md**: 표 분석 요청 샘플 (NEW)
  - 징계 기준표 중요도 분석
  - 가장 엄격한/관대한 기준 비교
  - Python 클라이언트 예시

- **DOCUMENT_ANALYSIS_SAMPLES.md**: 문서 분석 API 샘플
  - 업로드, 쿼리, 요약, 이슈 추출

#### LangChain & LlamaIndex
- **LCEL_REQUEST_SAMPLES.md**: LangChain LCEL 요청 샘플
  - 동기/비동기 채팅
  - 스트리밍

- **LLAMAINDEX_REQUEST_SAMPLES.md**: LlamaIndex 요청 샘플
  - 문서 업로드
  - 쿼리 실행

---

## 🔍 주요 문서 빠른 링크

### 시작하기
1. [Redis 설정](REDIS_SETUP_GUIDE.md) - Redis 설치 및 연결
2. [Response Wrapper 가이드](RESPONSE_WRAPPER_GUIDE.md) - API 응답 표준화
3. [LlamaIndex 가이드](LLAMAINDEX_GUIDE.md) - 문서 인덱싱 시작

### API 사용하기
- [조항 분석 API](CLAUSE_ANALYSIS_API.md) - 정부 문서 조항 분석
- [표 분석 API](TABLE_ANALYSIS_API.md) - 표·기준표 분석 (NEW)
- [표 분석 샘플](TABLE_ANALYSIS_REQUEST_SAMPLES.md) - 표 분석 요청 예시 (NEW)
- [문서 분석 샘플](DOCUMENT_ANALYSIS_SAMPLES.md) - 일반 문서 분석

### 개발 참고
- [리팩토링 완료 보고서](reports/REFACTORING_COMPLETE.md) - 코드 구조 개선
- [Redis 클라이언트 공통화](reports/REDIS_CLIENT_REFACTORING.md) - 중복 제거 사례

---

## 📝 문서 작성 규칙

### 파일명 규칙
- 가이드: `{주제}_GUIDE.md`
- API 문서: `{기능}_API.md`
- 샘플: `{기능}_SAMPLES.md`
- 보고서: `{작업명}_COMPLETE.md` (reports 디렉토리)

### 문서 구조
모든 문서는 다음 섹션을 포함해야 합니다:
1. **제목**: 명확한 문서 제목
2. **개요**: 문서의 목적과 내용 요약
3. **본문**: 상세 설명
4. **예시**: 코드 샘플 (해당되는 경우)
5. **참고**: 관련 문서 링크

---

## 🆕 새 문서 추가하기

### 가이드 문서
```bash
# docs/ 디렉토리에 추가
touch docs/NEW_FEATURE_GUIDE.md
```

### 보고서
```bash
# docs/reports/ 디렉토리에 추가
touch docs/reports/NEW_FEATURE_COMPLETE.md
```

### API 문서
```bash
# docs/ 디렉토리에 추가
touch docs/NEW_API_DOCUMENTATION.md
```

---

## 📊 문서 통계

### 카테고리별 파일 수
- 개발 보고서: 7개
- 사용 가이드: 5개
- API 문서: 6개

### 총 문서 수
**19개** (README 제외)

---

## 🔄 문서 업데이트 이력

### 2026-01-16
- ✅ 표 분석 API 문서 추가 (TABLE_ANALYSIS_API.md)
- ✅ 표 분석 요청 샘플 추가 (TABLE_ANALYSIS_REQUEST_SAMPLES.md)
- ✅ README.md 업데이트 (총 문서 19개)

### 2026-01-15
- ✅ 문서 디렉토리 구조 생성
- ✅ 모든 마크다운 파일 정리
- ✅ `docs/reports/` 디렉토리 생성
- ✅ 카테고리별 분류 완료
- ✅ README.md 작성

---

## 📮 문서 관련 문의

문서 내용이 불명확하거나 추가가 필요한 경우:
1. GitHub Issues에 문서 개선 요청 작성
2. 관련 문서 경로와 개선 사항 명시

---

**작성일**: 2026-01-15
**관리자**: Claude Sonnet 4.5
**문서 버전**: 1.0.0
