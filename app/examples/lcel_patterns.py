"""
LCEL (LangChain Expression Language) 패턴 학습 예제

이 모듈은 LangChain의 선언적 문법(LCEL)을 다양한 패턴으로 보여줍니다.
독립 실행 가능한 스크립트입니다.
"""

import asyncio
import os
from datetime import datetime

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import (
    RunnableBranch,
    RunnableLambda,
    RunnableParallel,
    RunnablePassthrough,
)
from langchain_openai import ChatOpenAI

# 환경 변수 로드
load_dotenv()


# ============================================================================
# LLM 초기화
# ============================================================================


def get_llm(temperature: float = 0.7):
    """OpenAI LLM 인스턴스 생성"""
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=temperature,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )


# ============================================================================
# Pattern 1: 기본 체인 (Prompt | LLM | Parser)
# ============================================================================


async def pattern_1_basic_chain():
    """
    가장 기본적인 LCEL 패턴

    Pipe(|) 연산자로 컴포넌트를 연결
    """
    print("\n" + "=" * 70)
    print("Pattern 1: Basic Chain")
    print("=" * 70)

    llm = get_llm()

    # 체인 구성
    prompt = ChatPromptTemplate.from_template("Tell me a short joke about {topic}")
    chain = prompt | llm | StrOutputParser()

    # 실행
    result = await chain.ainvoke({"topic": "programming"})
    print(f"Result: {result}")

    return result


# ============================================================================
# Pattern 2: RunnablePassthrough - 데이터 전달
# ============================================================================


async def pattern_2_passthrough():
    """
    RunnablePassthrough를 사용한 데이터 전달

    입력을 여러 단계로 전달하거나 일부를 변환
    """
    print("\n" + "=" * 70)
    print("Pattern 2: RunnablePassthrough")
    print("=" * 70)

    # 입력 데이터를 여러 형태로 전달
    chain = {
        "original": RunnablePassthrough(),
        "uppercase": RunnableLambda(lambda x: x.upper()),
        "length": RunnableLambda(lambda x: len(x)),
    } | RunnableLambda(
        lambda x: (
            f"Original: {x['original']}\n"
            f"Uppercase: {x['uppercase']}\n"
            f"Length: {x['length']}"
        )
    )

    result = await chain.ainvoke("hello world")
    print(f"Result:\n{result}")

    return result


# ============================================================================
# Pattern 3: RunnableParallel - 병렬 실행
# ============================================================================


async def pattern_3_parallel():
    """
    RunnableParallel을 사용한 병렬 실행

    여러 작업을 동시에 실행하여 효율성 향상
    """
    print("\n" + "=" * 70)
    print("Pattern 3: Parallel Execution")
    print("=" * 70)

    llm = get_llm()

    # 각기 다른 분석을 병렬로 수행
    text = "Python is a great programming language for beginners and experts alike."

    parallel_chain = RunnableParallel(
        {
            "sentiment": (
                ChatPromptTemplate.from_template(
                    "What is the sentiment (positive/negative/neutral) of: {text}"
                )
                | llm
                | StrOutputParser()
            ),
            "keywords": (
                ChatPromptTemplate.from_template("Extract 3 keywords from: {text}")
                | llm
                | StrOutputParser()
            ),
            "language": (
                ChatPromptTemplate.from_template(
                    "What programming language is mentioned in: {text}"
                )
                | llm
                | StrOutputParser()
            ),
        }
    )

    start = datetime.now()
    result = await parallel_chain.ainvoke({"text": text})
    elapsed = (datetime.now() - start).total_seconds()

    print(f"Sentiment: {result['sentiment']}")
    print(f"Keywords: {result['keywords']}")
    print(f"Language: {result['language']}")
    print(f"Elapsed: {elapsed:.2f}s")

    return result


# ============================================================================
# Pattern 4: RunnableLambda - 커스텀 로직
# ============================================================================


async def pattern_4_lambda():
    """
    RunnableLambda를 사용한 커스텀 로직

    체인 중간에 임의의 Python 함수 삽입
    """
    print("\n" + "=" * 70)
    print("Pattern 4: Custom Logic with RunnableLambda")
    print("=" * 70)

    llm = get_llm()

    # 전처리 함수
    def preprocess(text: str) -> dict:
        words = text.split()
        return {
            "text": text,
            "word_count": len(words),
            "has_numbers": any(char.isdigit() for char in text),
        }

    # 후처리 함수
    def postprocess(result: str) -> dict:
        return {
            "response": result,
            "length": len(result),
            "timestamp": datetime.now().isoformat(),
        }

    # 체인 구성
    chain = (
        RunnableLambda(preprocess)
        | ChatPromptTemplate.from_template(
            "Analyze this text: {text}\n"
            "Word count: {word_count}\n"
            "Has numbers: {has_numbers}"
        )
        | llm
        | StrOutputParser()
        | RunnableLambda(postprocess)
    )

    result = await chain.ainvoke("Hello world 123")
    print(f"Response: {result['response']}")
    print(f"Length: {result['length']}")
    print(f"Timestamp: {result['timestamp']}")

    return result


# ============================================================================
# Pattern 5: RunnableBranch - 조건부 실행
# ============================================================================


async def pattern_5_branch():
    """
    RunnableBranch를 사용한 조건부 실행

    입력에 따라 다른 체인 실행
    """
    print("\n" + "=" * 70)
    print("Pattern 5: Conditional Execution with Branch")
    print("=" * 70)

    llm = get_llm()

    # 길이에 따라 다른 프롬프트 사용
    def is_short(x: dict) -> bool:
        return len(x["text"]) < 20

    def is_medium(x: dict) -> bool:
        return 20 <= len(x["text"]) < 50

    short_chain = (
        ChatPromptTemplate.from_template("Give a very brief response: {text}")
        | llm
        | StrOutputParser()
    )

    medium_chain = (
        ChatPromptTemplate.from_template("Give a moderate response: {text}")
        | llm
        | StrOutputParser()
    )

    long_chain = (
        ChatPromptTemplate.from_template("Give a detailed response: {text}")
        | llm
        | StrOutputParser()
    )

    branch = RunnableBranch(
        (is_short, short_chain),
        (is_medium, medium_chain),
        long_chain,  # default
    )

    # 테스트
    texts = [
        "Hi",
        "What is Python?",
        "Explain the difference between synchronous and asynchronous programming in Python",
    ]

    for text in texts:
        result = await branch.ainvoke({"text": text})
        print(f"\nInput ({len(text)} chars): {text}")
        print(f"Output: {result[:100]}...")

    return "Branch pattern completed"


# ============================================================================
# Pattern 6: 체인 조합 (Chaining Chains)
# ============================================================================


async def pattern_6_chain_composition():
    """
    여러 체인을 조합하여 복잡한 파이프라인 구성

    출력이 다음 체인의 입력이 됨
    """
    print("\n" + "=" * 70)
    print("Pattern 6: Chain Composition")
    print("=" * 70)

    llm = get_llm()

    # Step 1: 주제 생성
    topic_chain = (
        ChatPromptTemplate.from_template(
            "Suggest a programming topic related to: {interest}"
        )
        | llm
        | StrOutputParser()
    )

    # Step 2: 주제에 대한 질문 생성
    question_chain = (
        ChatPromptTemplate.from_template("Generate a technical question about: {topic}")
        | llm
        | StrOutputParser()
    )

    # Step 3: 질문에 답변
    answer_chain = (
        ChatPromptTemplate.from_template("Answer this question: {question}")
        | llm
        | StrOutputParser()
    )

    # 전체 체인 실행
    interest = "web development"

    print(f"Interest: {interest}")

    topic = await topic_chain.ainvoke({"interest": interest})
    print(f"\nGenerated topic: {topic}")

    question = await question_chain.ainvoke({"topic": topic})
    print(f"\nGenerated question: {question}")

    answer = await answer_chain.ainvoke({"question": question})
    print(f"\nAnswer: {answer}")

    return answer


# ============================================================================
# Pattern 7: 맵 리듀스 패턴
# ============================================================================


async def pattern_7_map_reduce():
    """
    맵 리듀스 패턴

    여러 입력을 병렬로 처리(map)하고 결과를 합침(reduce)
    """
    print("\n" + "=" * 70)
    print("Pattern 7: Map-Reduce Pattern")
    print("=" * 70)

    llm = get_llm()

    # Map: 각 항목을 처리
    analyze_chain = (
        ChatPromptTemplate.from_template(
            "Rate this feature's importance (1-10): {feature}"
        )
        | llm
        | StrOutputParser()
    )

    features = [
        "User authentication",
        "Data caching",
        "Error logging",
        "API documentation",
    ]

    # 병렬로 각 feature 분석
    print("Analyzing features in parallel...")
    analyses = await asyncio.gather(
        *[analyze_chain.ainvoke({"feature": f}) for f in features]
    )

    # Reduce: 결과 합치기
    reduce_prompt = ChatPromptTemplate.from_template(
        "Summarize these feature ratings:\n{analyses}"
    )
    reduce_chain = reduce_prompt | llm | StrOutputParser()

    combined = "\n".join(
        [f"{feat}: {analysis}" for feat, analysis in zip(features, analyses, strict=True)]
    )

    summary = await reduce_chain.ainvoke({"analyses": combined})

    print(f"\nIndividual analyses:\n{combined}")
    print(f"\nSummary: {summary}")

    return summary


# ============================================================================
# Pattern 8: 스트리밍
# ============================================================================


async def pattern_8_streaming():
    """
    스트리밍 패턴

    토큰을 생성하는 대로 실시간 출력
    """
    print("\n" + "=" * 70)
    print("Pattern 8: Streaming")
    print("=" * 70)

    llm = get_llm()

    prompt = ChatPromptTemplate.from_template("Write a short story about {topic}")
    chain = prompt | llm | StrOutputParser()

    print("Streaming response:")
    print("-" * 70)

    full_response = ""
    async for chunk in chain.astream({"topic": "a robot learning to code"}):
        print(chunk, end="", flush=True)
        full_response += chunk

    print("\n" + "-" * 70)

    return full_response


# ============================================================================
# Pattern 9: 배치 처리
# ============================================================================


async def pattern_9_batch():
    """
    배치 처리 패턴

    여러 입력을 한 번에 효율적으로 처리
    """
    print("\n" + "=" * 70)
    print("Pattern 9: Batch Processing")
    print("=" * 70)

    llm = get_llm()

    prompt = ChatPromptTemplate.from_template("Categorize this: {item}")
    chain = prompt | llm | StrOutputParser()

    items = ["Python", "PostgreSQL", "React", "Docker", "FastAPI"]

    print(f"Processing {len(items)} items in batch...")

    start = datetime.now()
    results = await chain.abatch([{"item": item} for item in items])
    elapsed = (datetime.now() - start).total_seconds()

    for item, result in zip(items, results, strict=True):
        print(f"{item}: {result}")

    print(f"\nBatch processing took: {elapsed:.2f}s")

    return results


# ============================================================================
# Pattern 10: 복잡한 워크플로우
# ============================================================================


async def pattern_10_complex_workflow():
    """
    복잡한 워크플로우

    여러 패턴을 조합한 실전 예제
    """
    print("\n" + "=" * 70)
    print("Pattern 10: Complex Workflow")
    print("=" * 70)

    llm = get_llm()

    # 단계별 워크플로우
    topic = "FastAPI best practices"

    # 1. 병렬로 다양한 관점 생성
    perspectives = await RunnableParallel(
        {
            "technical": (
                ChatPromptTemplate.from_template("Technical aspects of: {topic}")
                | llm
                | StrOutputParser()
            ),
            "beginner": (
                ChatPromptTemplate.from_template("Beginner tips for: {topic}")
                | llm
                | StrOutputParser()
            ),
            "advanced": (
                ChatPromptTemplate.from_template("Advanced techniques for: {topic}")
                | llm
                | StrOutputParser()
            ),
        }
    ).ainvoke({"topic": topic})

    print(f"Topic: {topic}\n")
    print(f"Technical: {perspectives['technical'][:100]}...")
    print(f"Beginner: {perspectives['beginner'][:100]}...")
    print(f"Advanced: {perspectives['advanced'][:100]}...")

    # 2. 통합 요약
    summary_prompt = ChatPromptTemplate.from_template(
        "Create a comprehensive summary from these perspectives:\n"
        "Technical: {technical}\n"
        "Beginner: {beginner}\n"
        "Advanced: {advanced}"
    )
    summary_chain = summary_prompt | llm | StrOutputParser()

    summary = await summary_chain.ainvoke(perspectives)
    print(f"\nFinal Summary: {summary}")

    return summary


# ============================================================================
# 메인 실행 함수
# ============================================================================


async def run_all_patterns():
    """모든 패턴 실행"""
    print("=" * 70)
    print("LCEL (LangChain Expression Language) 패턴 예제")
    print("=" * 70)

    patterns = [
        ("Basic Chain", pattern_1_basic_chain),
        ("RunnablePassthrough", pattern_2_passthrough),
        ("Parallel Execution", pattern_3_parallel),
        ("Custom Logic", pattern_4_lambda),
        ("Conditional Branch", pattern_5_branch),
        ("Chain Composition", pattern_6_chain_composition),
        ("Map-Reduce", pattern_7_map_reduce),
        ("Streaming", pattern_8_streaming),
        ("Batch Processing", pattern_9_batch),
        ("Complex Workflow", pattern_10_complex_workflow),
    ]

    results = {}

    for name, pattern_func in patterns:
        try:
            result = await pattern_func()
            results[name] = {"status": "success"}
        except Exception as e:
            print(f"\nError in {name}: {e}")
            results[name] = {"status": "error", "error": str(e)}

        await asyncio.sleep(0.5)  # Rate limiting

    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    for name, result in results.items():
        status = result["status"]
        print(f"{name}: {status}")

    return results


def main():
    """동기 진입점"""
    asyncio.run(run_all_patterns())


if __name__ == "__main__":
    main()
