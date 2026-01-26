"""
LCEL (LangChain Expression Language) Examples Router

이 모듈은 LangChain의 선언적 문법(LCEL)과 FastAPI의 비동기 처리를 학습하기 위한 예제들을 제공합니다.
"""

import asyncio
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.output_parsers import (
    JsonOutputParser,
    PydanticOutputParser,
    StrOutputParser,
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import (
    RunnableLambda,
    RunnableParallel,
    RunnablePassthrough,
)
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

router = APIRouter(prefix="/lcel", tags=["LCEL Examples"])

# OpenAI 모델 초기화
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)


# ============================================================================
# Request/Response Models
# ============================================================================


class SimpleQuery(BaseModel):
    """단순 질의 요청"""

    query: str


class TranslationRequest(BaseModel):
    """번역 요청"""

    text: str
    source_lang: str = "Korean"
    target_lang: str = "English"


class MultiStepRequest(BaseModel):
    """다단계 처리 요청"""

    topic: str
    num_points: int = 3


class ParallelRequest(BaseModel):
    """병렬 처리 요청"""

    text: str


# ============================================================================
# Example 1: 기본 LCEL Chain (Prompt | LLM | Parser)
# ============================================================================


@router.post("/basic-chain")
async def basic_chain(request: SimpleQuery):
    """
    가장 기본적인 LCEL 체인 예제

    Chain 구조: Prompt Template | LLM | Output Parser
    - Prompt: 사용자 입력을 프롬프트 템플릿에 주입
    - LLM: 언어 모델 실행
    - Parser: 응답을 문자열로 파싱
    """
    # LCEL 체인 정의
    prompt = ChatPromptTemplate.from_template(
        "You are a helpful assistant. Answer the following question: {query}"
    )
    chain = prompt | llm | StrOutputParser()

    # 비동기 실행
    start_time = datetime.now()
    result = await chain.ainvoke({"query": request.query})
    end_time = datetime.now()

    return {
        "result": result,
        "execution_time_ms": (end_time - start_time).total_seconds() * 1000,
        "chain_structure": "Prompt | LLM | StrOutputParser",
    }


# ============================================================================
# Example 2: Streaming Response (비동기 스트리밍)
# ============================================================================


@router.post("/streaming-chain")
async def streaming_chain(request: SimpleQuery):
    """
    스트리밍 응답 예제 - FastAPI의 StreamingResponse 활용

    실시간으로 토큰을 생성하며 클라이언트에 전송
    """
    prompt = ChatPromptTemplate.from_template("Answer this question in detail: {query}")
    chain = prompt | llm | StrOutputParser()

    async def generate():
        async for chunk in chain.astream({"query": request.query}):
            yield f"data: {chunk}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# ============================================================================
# Example 3: RunnablePassthrough (데이터 전달)
# ============================================================================


@router.post("/passthrough-chain")
async def passthrough_chain(request: SimpleQuery):
    """
    RunnablePassthrough 예제

    입력 데이터를 다음 단계로 그대로 전달하거나 일부만 수정
    """
    prompt = ChatPromptTemplate.from_template(
        "Original query: {original}\nProcessed query: {processed}"
    )

    # RunnablePassthrough를 사용하여 원본 유지하면서 처리된 버전도 추가
    chain = (
        {
            "original": RunnablePassthrough(),
            "processed": RunnableLambda(lambda x: x.upper()),
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    result = await chain.ainvoke(request.query)

    return {
        "result": result,
        "explanation": "RunnablePassthrough keeps original data while adding processed version",
    }


# ============================================================================
# Example 4: Multi-step Chain (다단계 체인)
# ============================================================================


@router.post("/multi-step-chain")
async def multi_step_chain(request: MultiStepRequest):
    """
    다단계 체인 예제

    1단계: 주제에 대한 핵심 포인트 생성
    2단계: 각 포인트를 상세히 설명
    """
    # Step 1: 핵심 포인트 생성
    points_prompt = ChatPromptTemplate.from_template(
        "List {num_points} key points about {topic}. Return as JSON array with 'points' key."
    )
    points_chain = points_prompt | llm | JsonOutputParser()

    # Step 2: 각 포인트 설명
    async def explain_points(points_data: dict):
        points = points_data.get("points", [])
        explanations = []

        for point in points:
            explain_prompt = ChatPromptTemplate.from_template(
                "Explain this point in 2-3 sentences: {point}"
            )
            explain_chain = explain_prompt | llm | StrOutputParser()
            explanation = await explain_chain.ainvoke({"point": point})
            explanations.append({"point": point, "explanation": explanation})

        return explanations

    # 전체 체인 실행
    start_time = datetime.now()
    points_result = await points_chain.ainvoke(
        {"topic": request.topic, "num_points": request.num_points}
    )
    explanations = await explain_points(points_result)
    end_time = datetime.now()

    return {
        "topic": request.topic,
        "points_with_explanations": explanations,
        "execution_time_ms": (end_time - start_time).total_seconds() * 1000,
        "explanation": "Sequential processing: first generate points, then explain each",
    }


# ============================================================================
# Example 5: Parallel Execution (병렬 실행)
# ============================================================================


@router.post("/parallel-chain")
async def parallel_chain(request: ParallelRequest):
    """
    RunnableParallel을 사용한 병렬 실행 예제

    여러 작업을 동시에 실행하여 처리 시간 단축
    """
    # 각각 다른 작업을 병렬로 수행
    sentiment_prompt = ChatPromptTemplate.from_template(
        "Analyze the sentiment of this text (positive/negative/neutral): {text}"
    )
    summary_prompt = ChatPromptTemplate.from_template(
        "Summarize this text in one sentence: {text}"
    )
    keywords_prompt = ChatPromptTemplate.from_template(
        "Extract 3-5 keywords from this text as JSON array: {text}"
    )

    # 병렬 체인 구성
    parallel_chain = RunnableParallel(
        {
            "sentiment": sentiment_prompt | llm | StrOutputParser(),
            "summary": summary_prompt | llm | StrOutputParser(),
            "keywords": keywords_prompt | llm | JsonOutputParser(),
        }
    )

    # 비동기 병렬 실행
    start_time = datetime.now()
    results = await parallel_chain.ainvoke({"text": request.text})
    end_time = datetime.now()

    return {
        "analysis": results,
        "execution_time_ms": (end_time - start_time).total_seconds() * 1000,
        "explanation": "Three tasks executed in parallel: sentiment, summary, keywords",
    }


# ============================================================================
# Example 6: Translation Chain with Custom Logic
# ============================================================================


@router.post("/translation-chain")
async def translation_chain(request: TranslationRequest):
    """
    번역 체인 예제 - 커스텀 로직 포함

    RunnableLambda를 사용하여 커스텀 전처리/후처리 추가
    """

    # 전처리: 텍스트 정제
    def preprocess(data: dict) -> dict:
        text = data["text"].strip()
        return {**data, "text": text, "char_count": len(text)}

    # 후처리: 메타데이터 추가
    def postprocess(result: str) -> dict:
        return {
            "translation": result,
            "translated_at": datetime.now().isoformat(),
            "char_count": len(result),
        }

    prompt = ChatPromptTemplate.from_template(
        "Translate the following {source_lang} text to {target_lang}:\n\n{text}"
    )

    # 전체 체인
    chain = (
        RunnableLambda(preprocess)
        | prompt
        | llm
        | StrOutputParser()
        | RunnableLambda(postprocess)
    )

    result = await chain.ainvoke(
        {
            "text": request.text,
            "source_lang": request.source_lang,
            "target_lang": request.target_lang,
        }
    )

    return {
        "result": result,
        "original_text": request.text,
        "chain_structure": "Preprocess | Prompt | LLM | Parser | Postprocess",
    }


# ============================================================================
# Example 7: Conditional Chain (조건부 실행)
# ============================================================================


@router.post("/conditional-chain")
async def conditional_chain(request: SimpleQuery):
    """
    조건부 체인 예제

    입력에 따라 다른 체인 실행
    """

    # 입력 길이에 따라 다른 프롬프트 사용
    def choose_prompt(query: str) -> ChatPromptTemplate:
        if len(query) < 50:
            return ChatPromptTemplate.from_template("Give a brief answer to: {query}")
        else:
            return ChatPromptTemplate.from_template(
                "Provide a detailed answer with examples to: {query}"
            )

    # 조건부 실행
    prompt = choose_prompt(request.query)
    chain = prompt | llm | StrOutputParser()

    result = await chain.ainvoke({"query": request.query})

    return {
        "result": result,
        "query_length": len(request.query),
        "prompt_type": "brief" if len(request.query) < 50 else "detailed",
        "explanation": "Different prompts based on query length",
    }


# ============================================================================
# Example 8: Batch Processing (배치 처리)
# ============================================================================


class BatchRequest(BaseModel):
    queries: list[str]


@router.post("/batch-chain")
async def batch_chain(request: BatchRequest):
    """
    배치 처리 예제

    여러 입력을 한 번에 처리 (비동기 병렬)
    """
    prompt = ChatPromptTemplate.from_template("Answer briefly: {query}")
    chain = prompt | llm | StrOutputParser()

    start_time = datetime.now()

    # abatch를 사용한 병렬 배치 처리
    inputs = [{"query": q} for q in request.queries]
    results = await chain.abatch(inputs)

    end_time = datetime.now()

    return {
        "results": [
            {"query": q, "answer": r} for q, r in zip(request.queries, results, strict=True)
        ],
        "total_queries": len(request.queries),
        "execution_time_ms": (end_time - start_time).total_seconds() * 1000,
        "explanation": "All queries processed in parallel using abatch()",
    }


# ============================================================================
# Example 9: Chain with Retry Logic (재시도 로직)
# ============================================================================


@router.post("/retry-chain")
async def retry_chain(request: SimpleQuery):
    """
    재시도 로직이 있는 체인

    실패 시 자동으로 재시도
    """
    prompt = ChatPromptTemplate.from_template("Answer this question: {query}")
    chain = prompt | llm | StrOutputParser()

    max_retries = 3
    attempt = 0
    last_error = None

    while attempt < max_retries:
        try:
            start_time = datetime.now()
            result = await chain.ainvoke({"query": request.query})
            end_time = datetime.now()

            return {
                "result": result,
                "attempts": attempt + 1,
                "execution_time_ms": (end_time - start_time).total_seconds() * 1000,
                "explanation": "Successfully completed with retry logic",
            }
        except Exception as e:
            last_error = str(e)
            attempt += 1
            if attempt < max_retries:
                await asyncio.sleep(1)  # 재시도 전 대기

    raise HTTPException(
        status_code=500,
        detail=f"Failed after {max_retries} attempts. Last error: {last_error}",
    )


# ============================================================================
# Example 10: Complex Chain with Multiple Steps
# ============================================================================


class ComplexRequest(BaseModel):
    topic: str
    format: str = "markdown"  # markdown, json, plain


@router.post("/complex-chain")
async def complex_chain(request: ComplexRequest):
    """
    복잡한 다단계 체인 예제

    1. 주제 분석
    2. 콘텐츠 생성
    3. 포맷 변환
    4. 품질 검증
    """
    # Step 1: 주제 분석
    analyze_prompt = ChatPromptTemplate.from_template(
        "Analyze this topic and suggest 3 subtopics: {topic}"
    )
    analyze_chain = analyze_prompt | llm | StrOutputParser()

    # Step 2: 콘텐츠 생성
    async def generate_content(analysis: str, topic: str) -> str:
        content_prompt = ChatPromptTemplate.from_template(
            "Based on this analysis:\n{analysis}\n\nWrite detailed content about: {topic}"
        )
        content_chain = content_prompt | llm | StrOutputParser()
        return await content_chain.ainvoke({"analysis": analysis, "topic": topic})

    # Step 3: 포맷 변환
    async def format_content(content: str, format_type: str) -> str:
        if format_type == "json":
            format_prompt = ChatPromptTemplate.from_template(
                "Convert this content to JSON format:\n{content}"
            )
        elif format_type == "markdown":
            format_prompt = ChatPromptTemplate.from_template(
                "Format this content as markdown:\n{content}"
            )
        else:
            return content

        format_chain = format_prompt | llm | StrOutputParser()
        return await format_chain.ainvoke({"content": content})

    # Step 4: 품질 검증
    async def validate_quality(content: str) -> dict:
        validate_prompt = ChatPromptTemplate.from_template(
            "Rate the quality of this content (1-10) and provide brief feedback:\n{content}"
        )
        validate_chain = validate_prompt | llm | StrOutputParser()
        feedback = await validate_chain.ainvoke({"content": content})
        return {"content": content, "quality_feedback": feedback}

    # 전체 파이프라인 실행
    start_time = datetime.now()

    analysis = await analyze_chain.ainvoke({"topic": request.topic})
    content = await generate_content(analysis, request.topic)
    formatted = await format_content(content, request.format)
    final_result = await validate_quality(formatted)

    end_time = datetime.now()

    return {
        "result": final_result,
        "execution_time_ms": (end_time - start_time).total_seconds() * 1000,
        "pipeline_steps": [
            "1. Topic Analysis",
            "2. Content Generation",
            "3. Format Conversion",
            "4. Quality Validation",
        ],
        "explanation": "Multi-step pipeline with analysis, generation, formatting, and validation",
    }


# ============================================================================
# Pydantic Structured Output Examples
# ============================================================================


# Pydantic 모델 정의
class Person(BaseModel):
    """사람 정보를 나타내는 구조화된 모델"""

    name: str = Field(description="사람의 이름")
    age: int | None = Field(default=None, description="사람의 나이")
    occupation: str | None = Field(default=None, description="직업")
    email: str | None = Field(default=None, description="이메일 주소")


class MovieReview(BaseModel):
    """영화 리뷰를 나타내는 구조화된 모델"""

    title: str = Field(description="영화 제목")
    rating: int = Field(description="평점 (1-10)", ge=1, le=10)
    summary: str = Field(description="리뷰 요약 (1-2 문장)")
    pros: list[str] = Field(description="장점 목록")
    cons: list[str] = Field(description="단점 목록")
    recommended: bool = Field(description="추천 여부")


class ProductAnalysis(BaseModel):
    """제품 분석 결과를 나타내는 구조화된 모델"""

    product_name: str = Field(description="제품명")
    category: str = Field(description="제품 카테고리")
    target_audience: list[str] = Field(description="타겟 고객층")
    key_features: list[str] = Field(description="주요 기능")
    price_range: str = Field(description="가격대")
    market_position: str = Field(description="시장 포지션")


class CodeAnalysis(BaseModel):
    """코드 분석 결과를 나타내는 구조화된 모델"""

    language: str = Field(description="프로그래밍 언어")
    complexity: str = Field(description="복잡도 (low/medium/high)")
    purpose: str = Field(description="코드의 목적")
    improvements: list[str] = Field(description="개선 제안 사항")
    security_issues: list[str] = Field(description="보안 이슈")
    estimated_lines: int = Field(description="예상 코드 줄 수")


# Request Models
class PersonExtractionRequest(BaseModel):
    text: str = Field(description="사람 정보가 포함된 텍스트")


class MovieReviewRequest(BaseModel):
    movie_description: str = Field(description="영화 설명")


class ProductAnalysisRequest(BaseModel):
    product_description: str = Field(description="제품 설명")


class CodeAnalysisRequest(BaseModel):
    code_description: str = Field(description="코드 설명 또는 요구사항")


# ============================================================================
# Example 11: Pydantic Output Parser - 기본
# ============================================================================


@router.post("/pydantic-person", response_model=Person)
async def extract_person_info(request: PersonExtractionRequest):
    """
    Pydantic 모델을 사용한 구조화된 데이터 추출 (기본 예제)

    텍스트에서 사람 정보를 추출하여 Pydantic 모델로 반환
    """
    # Pydantic 파서 생성
    parser = PydanticOutputParser(pydantic_object=Person)

    # 포맷 지시사항을 포함한 프롬프트
    prompt = ChatPromptTemplate.from_template(
        "Extract person information from the following text.\n"
        "If any information is not available, use null for that field.\n"
        "Make reasonable inferences when possible (e.g., estimate age from context).\n"
        "{format_instructions}\n"
        "Text: {text}\n"
    )

    # 체인 구성
    chain = (
        {
            "text": RunnablePassthrough(),
            "format_instructions": lambda _: parser.get_format_instructions(),
        }
        | prompt
        | llm
        | parser
    )

    # 실행
    datetime.now()
    result = await chain.ainvoke(request.text)
    datetime.now()

    # Pydantic 모델이 반환되므로 FastAPI가 자동으로 직렬화
    return result


# ============================================================================
# Example 12: Pydantic Output Parser - 복잡한 구조
# ============================================================================


@router.post("/pydantic-movie-review", response_model=MovieReview)
async def generate_movie_review(request: MovieReviewRequest):
    """
    Pydantic 모델을 사용한 복잡한 구조화된 데이터 생성

    영화 설명을 바탕으로 구조화된 리뷰 생성
    """
    parser = PydanticOutputParser(pydantic_object=MovieReview)

    prompt = ChatPromptTemplate.from_template(
        "Generate a movie review based on the following description.\n"
        "Provide realistic ratings, pros, cons, and a recommendation.\n"
        "{format_instructions}\n"
        "Movie: {movie_description}\n"
    )

    chain = (
        {
            "movie_description": RunnablePassthrough(),
            "format_instructions": lambda _: parser.get_format_instructions(),
        }
        | prompt
        | llm
        | parser
    )

    result = await chain.ainvoke(request.movie_description)
    return result


# ============================================================================
# Example 13: Pydantic with Structured Output (OpenAI 함수 호출)
# ============================================================================


@router.post("/pydantic-structured-product")
async def analyze_product_structured(request: ProductAnalysisRequest):
    """
    OpenAI의 structured output 기능을 사용한 Pydantic 모델 생성

    with_structured_output()을 사용하여 더 안정적인 구조화 출력
    """
    # structured output을 사용하는 LLM
    structured_llm = llm.with_structured_output(ProductAnalysis)

    prompt = ChatPromptTemplate.from_template(
        "Analyze the following product and provide detailed information:\n"
        "{product_description}"
    )

    chain = prompt | structured_llm

    start_time = datetime.now()
    result = await chain.ainvoke({"product_description": request.product_description})
    end_time = datetime.now()

    return {
        "result": result.dict(),
        "execution_time_ms": (end_time - start_time).total_seconds() * 1000,
        "method": "with_structured_output",
        "explanation": "Uses OpenAI function calling for more reliable structured output",
    }


# ============================================================================
# Example 14: Pydantic 병렬 구조화 출력
# ============================================================================


@router.post("/pydantic-parallel")
async def parallel_structured_analysis(request: ProductAnalysisRequest):
    """
    여러 Pydantic 모델을 병렬로 생성

    동일한 입력에 대해 다른 구조의 분석을 동시에 수행
    """
    # 제품 분석
    product_llm = llm.with_structured_output(ProductAnalysis)
    product_prompt = ChatPromptTemplate.from_template("Analyze this product: {text}")
    product_chain = product_prompt | product_llm

    # 사람 정보 추출 (제품 설명에서 언급된 사람)
    person_parser = PydanticOutputParser(pydantic_object=Person)
    person_prompt = ChatPromptTemplate.from_template(
        "If there's any person mentioned in this product description, extract their info.\n"
        "If no person is mentioned, make up a fictional product manager.\n"
        "{format_instructions}\n"
        "Text: {text}\n"
    )
    person_chain = (
        {
            "text": RunnablePassthrough(),
            "format_instructions": lambda _: person_parser.get_format_instructions(),
        }
        | person_prompt
        | llm
        | person_parser
    )

    # 병렬 실행
    parallel_chain = RunnableParallel(
        {"product_analysis": product_chain, "person_info": person_chain}
    )

    start_time = datetime.now()
    result = await parallel_chain.ainvoke({"text": request.product_description})
    end_time = datetime.now()

    return {
        "product_analysis": result["product_analysis"].dict(),
        "person_info": result["person_info"].dict(),
        "execution_time_ms": (end_time - start_time).total_seconds() * 1000,
        "explanation": "Two different Pydantic models generated in parallel",
    }


# ============================================================================
# Example 15: Pydantic 리스트 처리
# ============================================================================


class PersonList(BaseModel):
    """여러 사람의 정보를 담는 리스트"""

    people: list[Person] = Field(description="사람들의 목록")
    total_count: int = Field(description="총 인원 수")


class TeamAnalysisRequest(BaseModel):
    team_description: str = Field(description="팀 설명")


@router.post("/pydantic-list")
async def extract_team_members(request: TeamAnalysisRequest):
    """
    Pydantic 모델 리스트 생성

    텍스트에서 여러 사람의 정보를 추출하여 리스트로 반환
    """
    structured_llm = llm.with_structured_output(PersonList)

    prompt = ChatPromptTemplate.from_template(
        "Extract information about all people mentioned in the following team description.\n"
        "Team: {team_description}"
    )

    chain = prompt | structured_llm

    start_time = datetime.now()
    result = await chain.ainvoke({"team_description": request.team_description})
    end_time = datetime.now()

    return {
        "result": result.dict(),
        "execution_time_ms": (end_time - start_time).total_seconds() * 1000,
        "explanation": "Extracted multiple Person objects into a list",
    }


# ============================================================================
# Example 16: Pydantic with 후처리
# ============================================================================


@router.post("/pydantic-with-postprocessing")
async def code_analysis_with_postprocessing(request: CodeAnalysisRequest):
    """
    Pydantic 구조화 출력 + 후처리

    구조화된 출력을 생성한 후 추가 처리 수행
    """
    structured_llm = llm.with_structured_output(CodeAnalysis)

    prompt = ChatPromptTemplate.from_template(
        "Analyze the following code requirements and provide detailed analysis:\n"
        "{code_description}"
    )

    # 후처리 함수
    def enrich_analysis(analysis: CodeAnalysis) -> dict:
        """분석 결과에 추가 정보 부여"""
        return {
            "analysis": analysis.dict(),
            "risk_level": "high" if len(analysis.security_issues) > 2 else "low",
            "development_time_estimate": f"{analysis.estimated_lines // 10} hours",
            "requires_review": analysis.complexity == "high"
            or len(analysis.security_issues) > 0,
            "timestamp": datetime.now().isoformat(),
        }

    # 체인 구성
    chain = prompt | structured_llm | RunnableLambda(enrich_analysis)

    start_time = datetime.now()
    result = await chain.ainvoke({"code_description": request.code_description})
    end_time = datetime.now()

    result["execution_time_ms"] = (end_time - start_time).total_seconds() * 1000
    result["explanation"] = "Pydantic output with additional post-processing"

    return result


# ============================================================================
# Example 17: Pydantic 배치 처리
# ============================================================================


class BatchPersonExtractionRequest(BaseModel):
    texts: list[str] = Field(description="사람 정보가 포함된 텍스트 목록")


@router.post("/pydantic-batch")
async def batch_person_extraction(request: BatchPersonExtractionRequest):
    """
    Pydantic 구조화 출력 배치 처리

    여러 텍스트에서 동시에 사람 정보를 구조화하여 추출
    """
    structured_llm = llm.with_structured_output(Person)

    prompt = ChatPromptTemplate.from_template("Extract person information from: {text}")

    chain = prompt | structured_llm

    start_time = datetime.now()

    # 배치 처리
    inputs = [{"text": text} for text in request.texts]
    results = await chain.abatch(inputs)

    end_time = datetime.now()

    return {
        "results": [person.dict() for person in results],
        "total_processed": len(results),
        "execution_time_ms": (end_time - start_time).total_seconds() * 1000,
        "explanation": "Batch processing with Pydantic structured output",
    }


# ============================================================================
# Example 18: Pydantic with 조건부 모델 선택
# ============================================================================


class SimpleAnalysis(BaseModel):
    """간단한 분석 결과"""

    summary: str = Field(description="간단한 요약")
    category: str = Field(description="카테고리")


class DetailedAnalysis(BaseModel):
    """상세한 분석 결과"""

    summary: str = Field(description="상세한 요약")
    category: str = Field(description="카테고리")
    subcategories: list[str] = Field(description="하위 카테고리")
    key_points: list[str] = Field(description="주요 포인트")
    recommendations: list[str] = Field(description="추천 사항")


class ConditionalAnalysisRequest(BaseModel):
    text: str = Field(description="분석할 텍스트")
    detailed: bool = Field(default=False, description="상세 분석 여부")


@router.post("/pydantic-conditional")
async def conditional_structured_output(request: ConditionalAnalysisRequest):
    """
    조건에 따라 다른 Pydantic 모델 사용

    입력에 따라 간단한 분석 또는 상세 분석 수행
    """
    # 조건에 따라 다른 모델 선택
    model = DetailedAnalysis if request.detailed else SimpleAnalysis
    structured_llm = llm.with_structured_output(model)

    prompt_text = (
        "Provide a detailed analysis of: {text}"
        if request.detailed
        else "Provide a brief analysis of: {text}"
    )

    prompt = ChatPromptTemplate.from_template(prompt_text)
    chain = prompt | structured_llm

    start_time = datetime.now()
    result = await chain.ainvoke({"text": request.text})
    end_time = datetime.now()

    return {
        "result": result.dict(),
        "model_used": "DetailedAnalysis" if request.detailed else "SimpleAnalysis",
        "execution_time_ms": (end_time - start_time).total_seconds() * 1000,
        "explanation": "Different Pydantic models based on condition",
    }
