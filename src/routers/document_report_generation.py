"""
보고서 및 체크리스트 생성 API Router (Redis)

정부 문서로부터 보고서 초안 및 실무 체크리스트를 자동 생성하는 API
- Models는 src/models/document_analysis.py에서 import
- Redis 유틸리티는 src/utils/redis_index.py에서 import
"""

from datetime import datetime

from fastapi import APIRouter

from src.models.document_analysis import (
    ReportSummaryRequest,
    ChecklistRequest,
    AmbiguousTextRequest,
    FAQGenerationRequest,
)
from src.utils import (
    success_response,
    error_response,
    ping_redis,
    load_index_from_redis,
    generate_structured_query,
)


router = APIRouter(
    prefix="/document-report-generation",
    tags=["Document Report Generation (Redis)"],
)


# ============================================================================
# API Endpoints
# ============================================================================


@router.post("/generate-report-summary")
async def generate_report_summary(request: ReportSummaryRequest):
    """
    내부 보고용 요약 메모 생성

    문서 내용을 분석하여 상급자 보고용 요약문을 자동 생성합니다.

    Returns:
    - title: 보고서 제목
    - summary: 전체 요약
    - key_points: 주요 포인트 리스트
    - recommendations: 권장 사항
    - source_references: 참조 소스
    """
    try:
        # Redis에서 인덱스 로드
        index, metadata = await load_index_from_redis(request.doc_id)

        # 보고서 요약 쿼리
        query = f"""
이 문서를 내부 보고용으로 요약해 주세요. 상급자에게 보고할 때 필요한 핵심 내용을 중심으로 작성해 주세요.

다음 형식으로 작성해 주세요:

[보고서 제목]
문서의 주제를 한 줄로 요약한 제목

[전체 요약] ({request.max_length}자 이내)
문서의 전체 내용을 간결하게 요약

[주요 포인트] (5-7개)
1. 첫 번째 주요 내용
2. 두 번째 주요 내용
3. ...

[권장 사항] (3-5개)
- 실무자가 주의해야 할 사항
- 후속 조치가 필요한 사항
- 검토가 필요한 부분

각 섹션을 명확히 구분하여 작성해 주세요.
"""

        # 쿼리 실행
        response_text, source_nodes = await generate_structured_query(
            index=index,
            query=query,
            response_mode="tree_summarize",  # 계층적 요약
            top_k=request.top_k,
        )

        # 응답 파싱
        sections = parse_report_sections(response_text)

        # 소스 참조 추출
        references = []
        for idx, node in enumerate(source_nodes[:10], 1):  # 상위 10개 소스
            node_text = getattr(node.node, "text", "")
            node_metadata = getattr(node.node, "metadata", {})

            references.append(
                {
                    "reference_number": idx,
                    "score": round(float(node.score or 0.0), 4),
                    "text_preview": (
                        node_text[:300] + "..." if len(node_text) > 300 else node_text
                    ),
                    "metadata": {
                        "page": node_metadata.get("page_label", "Unknown"),
                        "chunk_index": node_metadata.get("chunk_index", 0),
                    },
                }
            )

        return success_response(
            data={
                "doc_id": request.doc_id,
                "report_type": "internal",
                "title": sections.get("title", "보고서 요약"),
                "summary": sections.get("summary", ""),
                "key_points": sections.get("key_points", []),
                "recommendations": sections.get("recommendations", []),
                "full_text": response_text,
                "source_references": references,
                "metadata": {
                    "total_nodes_searched": len(source_nodes),
                    "file_name": metadata.get("file_name", "Unknown"),
                    "generated_at": datetime.now().isoformat(),
                    "max_length": request.max_length,
                },
            },
            message="보고서 초안이 생성되었습니다.",
        )

    except ValueError as e:
        return error_response(str(e), 404)
    except Exception as e:
        return error_response(f"보고서 생성 실패: {str(e)}", 500)


@router.post("/generate-checklist")
async def generate_checklist(request: ChecklistRequest):
    """
    실무자 체크리스트 생성

    문서 내용을 분석하여 실무자가 확인해야 할 체크리스트를 자동 생성합니다.

    Returns:
    - checklist_title: 체크리스트 제목
    - checklist_type: 유형 (procedure, compliance, review)
    - items: 체크리스트 항목 (카테고리별)
    - critical_items: 필수 확인 항목
    - source_references: 참조 소스
    """
    try:
        # Redis에서 인덱스 로드
        index, metadata = await load_index_from_redis(request.doc_id)

        # 체크리스트 유형별 쿼리 생성
        checklist_prompts = {
            "procedure": """
이 문서의 내용을 바탕으로 실무자가 반드시 따라야 할 절차 체크리스트를 만들어 주세요.

다음 형식으로 작성해 주세요:

[체크리스트 제목]
문서의 주제에 맞는 체크리스트 제목

[사전 준비]
□ 준비 항목 1
□ 준비 항목 2
...

[주요 절차]
□ 절차 단계 1
□ 절차 단계 2
...

[사후 조치]
□ 후속 조치 1
□ 후속 조치 2
...

[필수 확인 사항] (⚠️ 표시)
⚠️ 반드시 확인해야 할 사항 1
⚠️ 반드시 확인해야 할 사항 2
...

각 항목은 명확하고 실행 가능하게 작성해 주세요.
""",
            "compliance": """
이 문서의 규정 및 기준을 바탕으로 준수 사항 체크리스트를 만들어 주세요.

다음 형식으로 작성해 주세요:

[체크리스트 제목]
준수 사항 체크리스트 제목

[법적 요구사항]
□ 법적 준수 사항 1
□ 법적 준수 사항 2
...

[내부 규정]
□ 내부 규정 준수 사항 1
□ 내부 규정 준수 사항 2
...

[위반 시 조치사항]
□ 위반 사항 확인 절차
□ 시정 조치 방법
...

[필수 확인 사항] (⚠️ 표시)
⚠️ 반드시 준수해야 할 사항 1
⚠️ 반드시 준수해야 할 사항 2
...
""",
            "review": """
이 문서의 내용을 검토할 때 확인해야 할 체크리스트를 만들어 주세요.

다음 형식으로 작성해 주세요:

[체크리스트 제목]
검토 체크리스트 제목

[문서 적정성 검토]
□ 검토 항목 1
□ 검토 항목 2
...

[내용 검증]
□ 검증 항목 1
□ 검증 항목 2
...

[누락 사항 확인]
□ 확인 항목 1
□ 확인 항목 2
...

[필수 확인 사항] (⚠️ 표시)
⚠️ 반드시 검토해야 할 사항 1
⚠️ 반드시 검토해야 할 사항 2
...
""",
        }

        query = checklist_prompts.get(
            request.checklist_type, checklist_prompts["procedure"]
        )

        # 쿼리 실행
        response_text, source_nodes = await generate_structured_query(
            index=index,
            query=query,
            response_mode="tree_summarize",  # 계층적 요약
            top_k=request.top_k,
        )

        # 응답 파싱
        checklist_data = parse_checklist_sections(response_text)

        # 소스 참조 추출
        references = []
        for idx, node in enumerate(source_nodes[:10], 1):  # 상위 10개 소스
            node_text = getattr(node.node, "text", "")
            node_metadata = getattr(node.node, "metadata", {})

            references.append(
                {
                    "reference_number": idx,
                    "score": round(float(node.score or 0.0), 4),
                    "text_preview": (
                        node_text[:300] + "..." if len(node_text) > 300 else node_text
                    ),
                    "metadata": {
                        "page": node_metadata.get("page_label", "Unknown"),
                        "chunk_index": node_metadata.get("chunk_index", 0),
                    },
                }
            )

        return success_response(
            data={
                "doc_id": request.doc_id,
                "checklist_type": request.checklist_type,
                "checklist_title": checklist_data.get("title", "체크리스트"),
                "items": checklist_data.get("items", []),
                "critical_items": checklist_data.get("critical_items", []),
                "full_text": response_text,
                "source_references": references,
                "metadata": {
                    "total_nodes_searched": len(source_nodes),
                    "file_name": metadata.get("file_name", "Unknown"),
                    "generated_at": datetime.now().isoformat(),
                },
            },
            message=f"체크리스트가 생성되었습니다 ({request.checklist_type} 유형).",
        )

    except ValueError as e:
        return error_response(str(e), 404)
    except Exception as e:
        return error_response(f"체크리스트 생성 실패: {str(e)}", 500)


@router.get("/health")
async def health_check():
    """
    보고서 생성 API Health Check
    """
    redis_connected = await ping_redis()

    return success_response(
        data={
            "status": "healthy",
            "redis_connected": redis_connected,
            "service": "document_report_generation",
            "features": [
                "report_summary_generation",
                "checklist_generation",
            ],
            "timestamp": datetime.now().isoformat(),
        },
        message="보고서 생성 API가 정상 작동 중입니다.",
    )


# ============================================================================
# Helper Functions
# ============================================================================


def parse_report_sections(response_text: str) -> dict:
    """
    보고서 응답 텍스트를 섹션별로 파싱

    Args:
        response_text: LLM 응답 텍스트

    Returns:
        섹션별 데이터 딕셔너리
    """
    sections = {
        "title": "",
        "summary": "",
        "key_points": [],
        "recommendations": [],
    }

    lines = response_text.split("\n")
    current_section = None

    for line in lines:
        line = line.strip()

        # 섹션 구분
        if "[보고서 제목]" in line or "제목:" in line:
            current_section = "title"
            continue
        elif "[전체 요약]" in line or "요약:" in line:
            current_section = "summary"
            continue
        elif "[주요 포인트]" in line or "주요 내용:" in line:
            current_section = "key_points"
            continue
        elif "[권장 사항]" in line or "권장사항:" in line:
            current_section = "recommendations"
            continue

        # 내용 추출
        if line and current_section:
            if current_section == "title" and not sections["title"]:
                sections["title"] = line
            elif current_section == "summary":
                if sections["summary"]:
                    sections["summary"] += " " + line
                else:
                    sections["summary"] = line
            elif current_section == "key_points" and (
                line.startswith(("1", "2", "3", "4", "5", "6", "7", "8", "9", "-"))
            ):
                sections["key_points"].append(line.lstrip("1234567890-. "))
            elif current_section == "recommendations" and line.startswith(
                ("-", "•", "○", "1", "2", "3")
            ):
                sections["recommendations"].append(line.lstrip("-•○1234567890. "))

    return sections


def parse_checklist_sections(response_text: str) -> dict:
    """
    체크리스트 응답 텍스트를 섹션별로 파싱

    Args:
        response_text: LLM 응답 텍스트

    Returns:
        체크리스트 데이터 딕셔너리
    """
    checklist_data = {
        "title": "",
        "items": [],
        "critical_items": [],
    }

    lines = response_text.split("\n")
    current_category = None

    for line in lines:
        line = line.strip()

        # 제목 추출
        if "[체크리스트 제목]" in line:
            continue
        elif not checklist_data["title"] and line and not line.startswith("["):
            checklist_data["title"] = line
            continue

        # 카테고리 구분
        if line.startswith("[") and line.endswith("]"):
            category_name = line.strip("[]")
            if "필수 확인" in category_name or "⚠️" in category_name:
                current_category = "critical"
            else:
                current_category = category_name
                checklist_data["items"].append({"category": category_name, "tasks": []})
            continue

        # 체크리스트 항목 추출
        if line and (
            line.startswith("□") or line.startswith("⚠️") or line.startswith("-")
        ):
            task = line.lstrip("□⚠️- ")
            if current_category == "critical":
                checklist_data["critical_items"].append(task)
            elif current_category and checklist_data["items"]:
                checklist_data["items"][-1]["tasks"].append(task)

    return checklist_data


# ============================================================================
# 신규 엔드포인트: 모호한 표현 분석 & FAQ 생성
# ============================================================================


@router.post("/analyze-ambiguous-text")
async def analyze_ambiguous_text(request: AmbiguousTextRequest):
    """
    모호한 표현 분석

    문서에서 해석 여지가 있는 모호한 표현을 찾아 지적하고 이유를 설명합니다.

    Returns:
    - ambiguous_expressions: 모호한 표현 리스트
      - expression: 모호한 표현
      - location: 위치 정보
      - reason: 모호한 이유
      - impact: 영향도 (high)
      - suggestion: 개선 제안
    - summary: 전체 요약
    """
    try:
        # Redis에서 인덱스 로드
        index, metadata = await load_index_from_redis(request.doc_id)

        # 모호한 표현 분석 쿼리
        query = """
이 문서에서 모호하거나 해석 여지가 있는 표현들을 찾아 지적해 주세요.

다음 형식으로 작성해 주세요:

[모호한 표현 1]
표현: "정확한 표현 인용"
위치: 조항 또는 문단 번호
이유: 왜 모호한지 구체적으로 설명
영향: high (모든 항목 high로 표시)
개선 제안: 명확하게 개선하는 방법

[모호한 표현 2]
표현: "..."
위치: ...
이유: ...
영향: high
개선 제안: ...

[모호한 표현 3]
...

최소 5개 이상의 모호한 표현을 찾아주세요.

모호한 표현의 예시:
- "상당한 이유", "특별한 사정", "필요한 경우" 등 기준이 불명확한 표현
- "심한 경우", "경미한 경우" 등 정량적 기준이 없는 표현
- "적절한", "합리적인" 등 주관적 판단이 개입되는 표현
- "정상참작", "재량" 등 범위가 불명확한 표현
"""

        # 쿼리 실행
        response_text, source_nodes = await generate_structured_query(
            index=index,
            query=query,
            response_mode="tree_summarize",
            top_k=request.top_k,
        )

        # 응답 파싱
        ambiguous_data = parse_ambiguous_expressions(response_text)

        # 소스 참조 추출
        references = []
        for idx, node in enumerate(source_nodes[:10], 1):
            node_text = getattr(node.node, "text", "")
            node_metadata = getattr(node.node, "metadata", {})

            references.append(
                {
                    "reference_number": idx,
                    "score": round(float(node.score or 0.0), 4),
                    "text_preview": (
                        node_text[:300] + "..." if len(node_text) > 300 else node_text
                    ),
                    "metadata": {
                        "page": node_metadata.get("page_label", "Unknown"),
                        "chunk_index": node_metadata.get("chunk_index", 0),
                    },
                }
            )

        return success_response(
            data={
                "doc_id": request.doc_id,
                "ambiguous_expressions": ambiguous_data.get("expressions", []),
                "total_found": len(ambiguous_data.get("expressions", [])),
                "high_impact": len(
                    [
                        e
                        for e in ambiguous_data.get("expressions", [])
                        if e.get("impact") == "high"
                    ]
                ),
                "summary": ambiguous_data.get("summary", ""),
                "full_text": response_text,
                "source_references": references,
                "metadata": {
                    "total_nodes_searched": len(source_nodes),
                    "file_name": metadata.get("file_name", "Unknown"),
                    "analyzed_at": datetime.now().isoformat(),
                },
            },
            message="모호한 표현 분석이 완료되었습니다.",
        )

    except ValueError as e:
        return error_response(str(e), 404)
    except Exception as e:
        return error_response(f"모호한 표현 분석 실패: {str(e)}", 500)


@router.post("/generate-faq")
async def generate_faq(request: FAQGenerationRequest):
    """
    FAQ 생성

    문서 내용을 Q&A 형식으로 재구성합니다.

    Returns:
    - faq_items: FAQ 리스트
      - question: 질문
      - answer: 답변
      - category: 카테고리 (기본 정보)
    - total_questions: 전체 질문 수
    """
    try:
        # Redis에서 인덱스 로드
        index, metadata = await load_index_from_redis(request.doc_id)

        # FAQ 생성 쿼리
        query = f"""
이 문서의 내용을 FAQ (자주 묻는 질문) 형식으로 {request.num_questions}개 작성해 주세요.

다음 형식으로 작성해 주세요:

Q1. [질문 내용]
A1. [답변 내용 - 구체적이고 명확하게]

Q2. [질문 내용]
A2. [답변 내용]

Q3. [질문 내용]
A3. [답변 내용]

...

Q{request.num_questions}. [질문 내용]
A{request.num_questions}. [답변 내용]

FAQ 작성 가이드:
- 질문은 실무자나 일반인이 가장 궁금해할 만한 내용으로 작성
- 답변은 문서의 내용을 바탕으로 정확하고 명확하게 작성
- 모든 FAQ는 "기본 정보" 카테고리로 분류
- 질문은 "~인가요?", "~무엇인가요?" 등 의문문 형태로 작성
- 답변은 핵심 내용을 먼저 제시하고, 필요시 부가 설명 추가

예시 질문 주제:
- 문서의 주요 내용이나 목적
- 중요한 개념이나 용어의 정의
- 주요 절차나 방법
- 기준이나 조건
- 주의사항이나 제한사항
"""

        # 쿼리 실행
        response_text, source_nodes = await generate_structured_query(
            index=index,
            query=query,
            response_mode="tree_summarize",
            top_k=request.top_k,
        )

        # 응답 파싱
        faq_data = parse_faq_items(response_text, request.num_questions)

        # 소스 참조 추출
        references = []
        for idx, node in enumerate(source_nodes[:10], 1):
            node_text = getattr(node.node, "text", "")
            node_metadata = getattr(node.node, "metadata", {})

            references.append(
                {
                    "reference_number": idx,
                    "score": round(float(node.score or 0.0), 4),
                    "text_preview": (
                        node_text[:300] + "..." if len(node_text) > 300 else node_text
                    ),
                    "metadata": {
                        "page": node_metadata.get("page_label", "Unknown"),
                        "chunk_index": node_metadata.get("chunk_index", 0),
                    },
                }
            )

        return success_response(
            data={
                "doc_id": request.doc_id,
                "faq_items": faq_data.get("items", []),
                "total_questions": len(faq_data.get("items", [])),
                "full_text": response_text,
                "source_references": references,
                "metadata": {
                    "total_nodes_searched": len(source_nodes),
                    "file_name": metadata.get("file_name", "Unknown"),
                    "generated_at": datetime.now().isoformat(),
                    "requested_questions": request.num_questions,
                },
            },
            message=f"FAQ {len(faq_data.get('items', []))}개가 생성되었습니다.",
        )

    except ValueError as e:
        return error_response(str(e), 404)
    except Exception as e:
        return error_response(f"FAQ 생성 실패: {str(e)}", 500)


# ============================================================================
# 신규 Helper Functions
# ============================================================================


def parse_ambiguous_expressions(response_text: str) -> dict:
    """
    모호한 표현 응답 텍스트 파싱

    Args:
        response_text: LLM 응답 텍스트

    Returns:
        모호한 표현 데이터 딕셔너리
    """
    ambiguous_data = {"expressions": [], "summary": ""}

    lines = response_text.split("\n")
    current_expression = None

    for line in lines:
        line = line.strip()

        # 새로운 표현 시작
        if line.startswith("[모호한 표현"):
            if current_expression:
                ambiguous_data["expressions"].append(current_expression)
            current_expression = {
                "expression": "",
                "location": "",
                "reason": "",
                "impact": "high",
                "suggestion": "",
            }
            continue

        # 필드 추출
        if current_expression is not None:
            if line.startswith("표현:"):
                current_expression["expression"] = line.replace("표현:", "").strip(' "')
            elif line.startswith("위치:"):
                current_expression["location"] = line.replace("위치:", "").strip()
            elif line.startswith("이유:"):
                current_expression["reason"] = line.replace("이유:", "").strip()
            elif line.startswith("영향:"):
                current_expression["impact"] = "high"  # 항상 high로 설정
            elif line.startswith("개선 제안:") or line.startswith("개선제안:"):
                current_expression["suggestion"] = (
                    line.replace("개선 제안:", "").replace("개선제안:", "").strip()
                )

    # 마지막 표현 추가
    if current_expression and current_expression.get("expression"):
        ambiguous_data["expressions"].append(current_expression)

    # 요약 생성
    if ambiguous_data["expressions"]:
        ambiguous_data["summary"] = (
            f"총 {len(ambiguous_data['expressions'])}개의 모호한 표현이 발견되었습니다."
        )

    return ambiguous_data


def parse_faq_items(response_text: str, requested_num: int) -> dict:
    """
    FAQ 응답 텍스트 파싱

    Args:
        response_text: LLM 응답 텍스트
        requested_num: 요청한 FAQ 개수

    Returns:
        FAQ 데이터 딕셔너리
    """
    faq_data = {"items": []}

    lines = response_text.split("\n")
    current_question = None
    current_answer = ""

    for line in lines:
        line = line.strip()

        # 질문 시작 (Q1., Q2., ...)
        if line.startswith("Q") and "." in line[:5]:
            # 이전 Q&A 저장
            if current_question and current_answer:
                faq_data["items"].append(
                    {
                        "question": current_question,
                        "answer": current_answer.strip(),
                        "category": "기본 정보",
                    }
                )

            # 새로운 질문 시작
            question_text = (
                line.split(".", 1)[1].strip() if "." in line else line[2:].strip()
            )
            current_question = question_text
            current_answer = ""
            continue

        # 답변 시작 (A1., A2., ...)
        if line.startswith("A") and "." in line[:5]:
            answer_text = (
                line.split(".", 1)[1].strip() if "." in line else line[2:].strip()
            )
            current_answer = answer_text
            continue

        # 답변 이어지는 부분
        if current_question and line and not line.startswith("Q"):
            if current_answer:
                current_answer += " " + line
            else:
                current_answer = line

    # 마지막 Q&A 저장
    if current_question and current_answer:
        faq_data["items"].append(
            {
                "question": current_question,
                "answer": current_answer.strip(),
                "category": "기본 정보",
            }
        )

    return faq_data
