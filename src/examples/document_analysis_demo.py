"""
실무형 문서 분석 데모

PDF 문서를 LlamaIndex로 인덱싱하고 실무 질문에 답변하는 예제
1. 문서 목적 및 핵심 내용 요약 (스트리밍 응답)
2. 문제로 지적된 주요 사안 추출
"""

import asyncio

from llama_index.core import Settings, VectorStoreIndex
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

from src.utils import load_pdf_from_path, create_hierarchical_index


# LlamaIndex 전역 설정
Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.1)
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
Settings.chunk_size = 512
Settings.chunk_overlap = 50


def print_section(title: str):
    """섹션 헤더 출력"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


async def load_pdf_document_with_logging(pdf_path: str):
    """PDF 문서 로드 (로깅 포함)"""
    print(f"📄 PDF 로드 중: {pdf_path}")
    documents = await load_pdf_from_path(pdf_path)
    print(f"✓ {len(documents)} 페이지 로드 완료")
    return documents


async def create_hierarchical_index_with_logging(documents):
    """계층적 인덱스 생성 (로깅 포함)"""
    print("\n🔧 계층적 인덱스 생성 중...")
    index, total_nodes, child_nodes_count = await create_hierarchical_index(documents)
    parent_count = (total_nodes - child_nodes_count) // 2  # 추정
    print(
        f"✓ 총 {total_nodes}개 노드 생성 (Parent: ~{parent_count}, Child: {child_nodes_count})"
    )
    print("✓ 인덱스 생성 완료")
    return index


async def streaming_summary(index: VectorStoreIndex) -> None:
    """
    질문 1: 문서의 목적과 핵심 내용 요약 (스트리밍)

    스트리밍 응답을 통해 실시간으로 요약 내용을 출력
    """
    print_section("질문 1: 이 문서의 목적과 핵심 내용을 한 문단으로 요약해 주세요")

    query_engine = index.as_query_engine(streaming=True, similarity_top_k=5)

    query = """
    이 문서의 목적과 핵심 내용을 한 문단(200자 이내)으로 요약해 주세요.
    정부의 정책 방향, 주요 지원 내용, 예산 규모 등을 포함해주세요.
    """

    print("💬 질의 중...\n")
    print("📝 스트리밍 응답:\n")
    print("-" * 80)

    streaming_response = query_engine.query(query)

    # 스트리밍 출력
    full_response = ""
    for text in streaming_response.response_gen:  # type: ignore[attr-defined]
        print(text, end="", flush=True)
        full_response += text

    print("\n" + "-" * 80)
    print(f"\n✓ 요약 완료 ({len(full_response)}자)")

    # 참조된 소스 노드 정보
    if hasattr(streaming_response, "source_nodes"):
        print(f"\n📚 참조된 문서 청크: {len(streaming_response.source_nodes)}개")
        for i, node in enumerate(streaming_response.source_nodes[:3], 1):
            text = getattr(node.node, "text", "")[:100]  # type: ignore[attr-defined]
            print(f"  {i}. 유사도: {node.score:.3f} | 텍스트: {text}...")


async def extract_issues(index: VectorStoreIndex) -> None:
    """
    질문 2: 문제로 지적된 주요 사안 추출

    문서에서 문제점, 개선사항, 변경내용 등을 추출
    """
    print_section("질문 2: 이 문서에서 문제로 지적된 주요 사안은 무엇인가요?")

    query_engine = index.as_query_engine(
        similarity_top_k=8, response_mode="tree_summarize"
    )

    query = """
    이 정부 정책 문서에서 다음 내용을 추출해주세요:
    1. 기존에 존재하던 문제점이나 개선이 필요한 사항
    2. 2024년 대비 2025년에 달라지는 내용 (변경사항)
    3. 새롭게 신설되거나 확대되는 지원 사업

    각 항목을 명확하게 구분하여 정리해주세요.
    """

    print("💬 질의 중...\n")

    response = query_engine.query(query)

    print("📋 핵심 이슈 추출 결과:\n")
    print("-" * 80)
    print(str(response))  # type: ignore[attr-defined]
    print("-" * 80)

    # 참조된 소스 노드 정보
    print(f"\n📚 참조된 문서 청크: {len(response.source_nodes)}개")

    # 유사도 높은 순으로 정렬
    sorted_nodes = sorted(
        response.source_nodes, key=lambda x: x.score or 0.0, reverse=True
    )

    print("\n🔍 관련도가 높은 문서 섹션:")
    for i, node in enumerate(sorted_nodes[:5], 1):
        print(f"\n  [{i}] 유사도: {node.score:.3f}")
        text = getattr(node.node, "text", "")[:200]  # type: ignore[attr-defined]
        print(f"      내용: {text}...")


async def additional_analysis(index: VectorStoreIndex) -> None:
    """
    추가 분석: 예산 규모, 지원 대상 등 구체적 정보 추출
    """
    print_section("추가 분석: 구체적 정보 추출")

    query_engine = index.as_query_engine(similarity_top_k=5)

    questions = [
        "2025년 소상공인 지원 예산 총 규모는 얼마인가요?",
        "신규로 도입되는 주요 사업은 무엇인가요?",
        "가장 큰 예산이 배정된 사업은 무엇인가요?",
    ]

    for i, question in enumerate(questions, 1):
        print(f"\n❓ 질문 {i}: {question}")
        print("-" * 80)

        response = query_engine.query(question)
        print(f"✅ 답변: {str(response)}")  # type: ignore[attr-defined]


async def main():
    """메인 실행 함수"""
    print("\n" + "█" * 80)
    print("  실무형 문서 분석 데모 - 2025년 소상공인 지원사업 공고 분석")
    print("█" * 80)

    # PDF 파일 경로
    pdf_path = "docs/Reprimand-sample-1.pdf"

    try:
        # 1. PDF 문서 로드
        documents = await load_pdf_document_with_logging(pdf_path)

        # 2. 계층적 인덱스 생성
        index = await create_hierarchical_index_with_logging(documents)

        # 3. 질문 1: 문서 목적 및 핵심 내용 요약 (스트리밍)
        await streaming_summary(index)

        # 4. 질문 2: 문제로 지적된 주요 사안 추출
        await extract_issues(index)

        # 5. 추가 분석
        await additional_analysis(index)

        print("\n" + "█" * 80)
        print("  분석 완료!")
        print("█" * 80 + "\n")

    except FileNotFoundError as e:
        print(f"\n❌ 오류: {e}")
        print("   docs 폴더에 PDF 파일을 배치했는지 확인해주세요.")
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류 발생: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
