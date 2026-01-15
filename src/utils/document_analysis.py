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
