"""
Document Analysis 공통 유틸리티 함수

PDF 로딩, 계층적 인덱싱, 스트리밍 등 문서 분석에 필요한 공통 함수들
"""

import os
import json
from pathlib import Path
from typing import AsyncIterator

from llama_index.core import Document, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import TextNode, NodeRelationship, RelatedNodeInfo
from llama_index.readers.file import PyMuPDFReader


async def load_pdf_from_path(pdf_path: str) -> list[Document]:
    """
    PDF 파일 로드

    Args:
        pdf_path: PDF 파일 경로

    Returns:
        Document 리스트 (페이지별)

    Raises:
        FileNotFoundError: 파일이 존재하지 않을 때
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")

    reader = PyMuPDFReader()
    documents = reader.load(file_path=Path(pdf_path))
    return documents


async def create_hierarchical_index(
    documents: list[Document],
) -> tuple[VectorStoreIndex, int, int]:
    """
    계층적 인덱스 생성

    Parent 노드(2048자)와 Child 노드(512자)로 구성된 계층적 인덱스 생성
    검색은 Child 노드로, 컨텍스트는 Parent 노드에서 가져옴

    Args:
        documents: LlamaIndex Document 리스트

    Returns:
        tuple: (VectorStoreIndex, 전체 노드 수, Child 노드 수)
    """
    # 문서 전체를 하나의 텍스트로 결합
    full_text = "\n\n".join([doc.text for doc in documents])

    # Parent 노드 생성 (큰 청크: 2048자)
    parent_splitter = SentenceSplitter(chunk_size=2048, chunk_overlap=100)
    parent_chunks = parent_splitter.split_text(full_text)

    all_nodes = []

    for parent_idx, parent_text in enumerate(parent_chunks):
        # Parent 노드
        parent_node = TextNode(
            text=parent_text,
            metadata={
                "node_type": "parent",
                "chunk_index": parent_idx,
            },
        )

        # Child 노드들 (작은 청크: 512자)
        child_splitter = SentenceSplitter(chunk_size=512, chunk_overlap=50)
        child_chunks = child_splitter.split_text(parent_text)

        child_nodes = []
        for child_idx, child_text in enumerate(child_chunks):
            child_node = TextNode(
                text=child_text,
                metadata={
                    "node_type": "child",
                    "parent_index": parent_idx,
                    "chunk_index": child_idx,
                },
            )

            # Child -> Parent 관계 설정
            child_node.relationships[NodeRelationship.PARENT] = RelatedNodeInfo(
                node_id=parent_node.node_id
            )

            child_nodes.append(child_node)

        # Parent -> Children 관계 설정
        parent_node.relationships[NodeRelationship.CHILD] = [
            RelatedNodeInfo(node_id=child.node_id) for child in child_nodes
        ]

        all_nodes.extend([parent_node] + child_nodes)

    # Child 노드만으로 인덱스 생성
    child_nodes_only = [n for n in all_nodes if n.metadata.get("node_type") == "child"]

    # 벡터 인덱스 생성
    index = VectorStoreIndex(child_nodes_only)

    return index, len(all_nodes), len(child_nodes_only)


async def stream_response(response_gen) -> AsyncIterator[str]:
    """
    스트리밍 응답 생성기 (Server-Sent Events 형식)

    Args:
        response_gen: LlamaIndex 스트리밍 응답 제너레이터

    Yields:
        SSE 형식의 JSON 문자열
    """
    for text in response_gen:
        yield f"data: {json.dumps({'text': text, 'done': False})}\n\n"
    yield f"data: {json.dumps({'text': '', 'done': True})}\n\n"


# ==================== Clause Analysis 헬퍼 함수 ====================

def extract_source_references(source_nodes: list, top_n: int = 5) -> list[dict]:
    """
    소스 노드에서 참조 정보 추출

    Args:
        source_nodes: 검색된 소스 노드 리스트 (NodeWithScore)
        top_n: 추출할 최대 노드 수

    Returns:
        참조 정보 딕셔너리 리스트
        - reference_number: 참조 번호 (1, 2, 3...)
        - score: 유사도 점수
        - text_preview: 텍스트 미리보기 (300자)
        - full_text: 전체 텍스트
        - metadata: 페이지, 청크 인덱스 등
    """
    references = []

    for idx, node in enumerate(source_nodes[:top_n], 1):
        # 노드 텍스트 추출
        node_text = getattr(node.node, "text", "")

        # 메타데이터 추출
        node_metadata = getattr(node.node, "metadata", {})

        node_info = {
            "reference_number": idx,
            "score": round(float(node.score or 0.0), 4),
            "text_preview": node_text[:300] + "..." if len(node_text) > 300 else node_text,
            "full_text": node_text,
            "metadata": {
                "page": node_metadata.get("page_label", "Unknown"),
                "chunk_index": node_metadata.get("chunk_index", 0),
                "node_type": node_metadata.get("node_type", "unknown"),
            }
        }

        # Child 노드인 경우 parent_index 추가
        if node_info["metadata"]["node_type"] == "child":
            node_info["metadata"]["parent_index"] = node_metadata.get("parent_index", 0)

        references.append(node_info)

    return references


def format_citation(reference: dict) -> str:
    """
    참조 정보를 인용 형식으로 변환

    Args:
        reference: extract_source_references()가 반환한 참조 정보

    Returns:
        인용 형식 문자열
        - Parent 노드: "[참조 1: 문단 45]"
        - Child 노드: "[참조 1: 문단 45-2]"

    Examples:
        >>> ref = {"reference_number": 1, "metadata": {"node_type": "parent", "chunk_index": 45}}
        >>> format_citation(ref)
        "[참조 1: 문단 45]"

        >>> ref = {"reference_number": 2, "metadata": {"node_type": "child", "parent_index": 45, "chunk_index": 2}}
        >>> format_citation(ref)
        "[참조 2: 문단 45-2]"
    """
    ref_num = reference["reference_number"]
    metadata = reference["metadata"]

    if metadata["node_type"] == "child":
        parent_idx = metadata.get("parent_index", 0)
        child_idx = metadata.get("chunk_index", 0)
        return f"[참조 {ref_num}: 문단 {parent_idx}-{child_idx}]"
    else:
        chunk_idx = metadata.get("chunk_index", 0)
        return f"[참조 {ref_num}: 문단 {chunk_idx}]"


def get_exception_keywords() -> list[str]:
    """
    한국어 예외 조항 키워드 리스트 반환

    정부 문서에서 예외 조항을 나타내는 일반적인 표현들

    Returns:
        예외 키워드 리스트
    """
    return [
        "다만",
        "단서",
        "예외",
        "제외",
        "이 경우",
        "특례",
        "불구하고"
    ]


def highlight_exception_sources(
    source_references: list[dict],
    exception_keywords: list[str] = None
) -> list[dict]:
    """
    예외 키워드가 포함된 소스만 필터링 및 하이라이팅

    Args:
        source_references: extract_source_references()가 반환한 참조 정보 리스트
        exception_keywords: 검색할 예외 키워드 (None이면 기본 키워드 사용)

    Returns:
        예외 키워드가 포함된 참조 정보 리스트
        각 참조에 "found_exception_keywords" 필드 추가

    Examples:
        >>> refs = [
        ...     {"reference_number": 1, "full_text": "다만, 허위 신고의 경우..."},
        ...     {"reference_number": 2, "full_text": "일반적인 경우..."}
        ... ]
        >>> highlighted = highlight_exception_sources(refs)
        >>> len(highlighted)
        1
        >>> highlighted[0]["found_exception_keywords"]
        ["다만"]
    """
    if exception_keywords is None:
        exception_keywords = get_exception_keywords()

    highlighted_sources = []

    for ref in source_references:
        full_text = ref.get("full_text", "")

        # 텍스트에서 발견된 예외 키워드 추출
        found_keywords = [
            keyword for keyword in exception_keywords
            if keyword in full_text
        ]

        if found_keywords:
            ref["found_exception_keywords"] = found_keywords
            highlighted_sources.append(ref)

    return highlighted_sources
