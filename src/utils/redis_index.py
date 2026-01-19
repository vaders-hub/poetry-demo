"""
Redis 인덱스 저장/로드 공통 유틸리티

LlamaIndex 인덱스를 Redis에 저장하고 로드하는 공통 함수들

Note:
    VectorStoreIndex를 직접 pickle하거나 StorageContext.to_dict()를 사용하면
    OpenAI 클라이언트 등 직렬화 불가능한 객체로 인해 문제가 발생할 수 있음.

    이 모듈은 노드 데이터(텍스트 + 임베딩)만 추출하여 JSON으로 저장하고,
    로드 시 노드로부터 인덱스를 재구성하는 방식을 사용함.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from llama_index.core import VectorStoreIndex
from llama_index.core.schema import TextNode

from src.utils.redis_client import get_redis_client

logger = logging.getLogger(__name__)


def _serialize_nodes(index: VectorStoreIndex) -> List[Dict[str, Any]]:
    """
    VectorStoreIndex에서 노드 데이터 추출 및 직렬화

    각 노드의 텍스트, 메타데이터, 임베딩을 딕셔너리로 변환
    """
    nodes_data = []

    # docstore에서 모든 노드 가져오기
    docstore = index.storage_context.docstore
    all_node_ids = list(docstore.docs.keys())
    logger.debug(f"docstore에서 {len(all_node_ids)}개 노드 ID 추출")

    # vector store에서 임베딩 딕셔너리 가져오기
    embedding_dict: Dict[str, Any] = {}
    try:
        vector_store = index.storage_context.vector_store
        if hasattr(vector_store, "_data") and hasattr(
            vector_store._data, "embedding_dict"  # type: ignore[attr-defined]
        ):
            embedding_dict = vector_store._data.embedding_dict  # type: ignore[attr-defined]
            logger.debug(f"임베딩 딕셔너리: {len(embedding_dict)}개")
    except Exception as e:
        logger.warning(f"임베딩 딕셔너리 접근 실패: {e}")

    for i, node_id in enumerate(all_node_ids):
        node = docstore.get_node(node_id)

        node_dict: Dict[str, Any] = {
            "id_": node.node_id,
            "text": node.get_content(),
            "metadata": node.metadata,
        }

        # 임베딩 추가
        embedding = embedding_dict.get(node_id)
        if embedding is not None:
            # 리스트로 변환 (numpy array일 수 있음)
            if hasattr(embedding, "tolist"):
                node_dict["embedding"] = embedding.tolist()  # type: ignore[union-attr]
            else:
                node_dict["embedding"] = list(embedding)

        nodes_data.append(node_dict)

        if (i + 1) % 10 == 0:
            logger.debug(f"노드 처리 중: {i + 1}/{len(all_node_ids)}")

    return nodes_data


def _deserialize_nodes(nodes_data: List[Dict[str, Any]]) -> List[TextNode]:
    """
    직렬화된 노드 데이터로부터 TextNode 리스트 복원
    """
    nodes = []

    for node_dict in nodes_data:
        node = TextNode(
            id_=node_dict.get("id_"),
            text=node_dict.get("text", ""),
            metadata=node_dict.get("metadata", {}),
            embedding=node_dict.get("embedding"),
        )
        nodes.append(node)

    return nodes


async def save_index_to_redis(
    doc_id: str,
    index: VectorStoreIndex,
    metadata: Dict[str, Any],
    ttl_seconds: Optional[int] = None,
) -> None:
    """
    인덱스를 Redis에 저장

    노드 데이터(텍스트 + 임베딩)만 추출하여 JSON으로 저장합니다.

    Args:
        doc_id: 문서 ID
        index: LlamaIndex VectorStoreIndex
        metadata: 메타데이터 딕셔너리
        ttl_seconds: TTL (초), None이면 TTL 설정 안 함

    Examples:
        >>> await save_index_to_redis(
        ...     doc_id="policy_2024",
        ...     index=my_index,
        ...     metadata={"file_name": "policy.pdf", "pages": 10},
        ...     ttl_seconds=86400  # 24시간
        ... )
    """
    client = await get_redis_client()

    logger.info(f"인덱스 저장 시작: doc_id={doc_id}")

    # 노드 데이터 추출
    nodes_data = _serialize_nodes(index)
    logger.info(f"노드 추출 완료: {len(nodes_data)}개")

    # JSON 직렬화
    logger.info("JSON 직렬화 시작...")
    try:
        nodes_json = json.dumps(nodes_data, ensure_ascii=False)
        logger.info(f"JSON 직렬화 완료: {len(nodes_json)} bytes")
    except Exception as e:
        logger.error(f"JSON 직렬화 실패: {e}")
        raise

    # 메타데이터에 업데이트 시간 추가
    metadata_with_timestamp = {
        **metadata,
        "updated_at": datetime.now().isoformat(),
        "node_count": len(nodes_data),
    }
    metadata_json = json.dumps(metadata_with_timestamp, ensure_ascii=False)
    logger.info("메타데이터 직렬화 완료")

    # Redis에 저장
    logger.info(
        f"Redis 저장 시작... (nodes: {len(nodes_json)} bytes, metadata: {len(metadata_json)} bytes)"
    )

    try:
        # 타임아웃 설정 (30초)
        result = await asyncio.wait_for(
            client.hset(  # type: ignore
                f"doc:{doc_id}",
                mapping={
                    "nodes": nodes_json,
                    "metadata": metadata_json,
                },
            ),
            timeout=30.0,
        )
        logger.info(f"Redis hset 결과: {result}")
    except asyncio.TimeoutError:
        logger.error("Redis hset 타임아웃 (30초)")
        raise
    except Exception as e:
        logger.error(f"Redis hset 오류: {type(e).__name__}: {e}")
        raise

    logger.info(f"Redis 저장 완료: doc_id={doc_id}")

    # TTL 설정 (선택사항)
    if ttl_seconds is not None:
        await client.expire(f"doc:{doc_id}", ttl_seconds)


async def load_index_from_redis(
    doc_id: str,
) -> tuple[VectorStoreIndex, Dict[str, Any]]:
    """
    Redis에서 인덱스 로드

    저장된 노드 데이터로부터 VectorStoreIndex를 재구성합니다.
    이미 임베딩이 저장되어 있으므로 추가 API 호출 없이 인덱스 생성.

    Args:
        doc_id: 문서 ID

    Returns:
        tuple: (VectorStoreIndex, 메타데이터 딕셔너리)

    Raises:
        ValueError: 문서를 찾을 수 없거나 인덱스가 손상된 경우

    Examples:
        >>> index, metadata = await load_index_from_redis("policy_2024")
        >>> print(metadata["file_name"])
        "policy.pdf"
    """
    client = await get_redis_client()

    # Redis에서 데이터 가져오기
    data = await client.hgetall(f"doc:{doc_id}")  # type: ignore

    if not data:
        raise ValueError(f"문서 ID '{doc_id}'를 Redis에서 찾을 수 없습니다.")

    # 노드 데이터 복원
    nodes_bytes = data.get(b"nodes")
    metadata_bytes = data.get(b"metadata")

    if not nodes_bytes:
        raise ValueError(f"문서 ID '{doc_id}'의 인덱스가 손상되었습니다.")

    # 노드 역직렬화
    nodes_data = json.loads(nodes_bytes.decode("utf-8"))
    nodes = _deserialize_nodes(nodes_data)

    # VectorStoreIndex 재구성 (임베딩이 이미 있으므로 API 호출 없음)
    index = VectorStoreIndex(nodes=nodes)

    # 메타데이터 파싱
    metadata: Dict[str, Any] = {}
    if metadata_bytes:
        metadata = json.loads(metadata_bytes.decode("utf-8"))

    return index, metadata


async def check_document_exists(doc_id: str) -> bool:
    """
    문서가 Redis에 존재하는지 확인

    Args:
        doc_id: 문서 ID

    Returns:
        존재 여부 (True/False)
    """
    client = await get_redis_client()
    exists = await client.exists(f"doc:{doc_id}")
    return exists > 0  # type: ignore


async def delete_document_from_redis(doc_id: str) -> bool:
    """
    Redis에서 문서 삭제

    Args:
        doc_id: 문서 ID

    Returns:
        삭제 성공 여부
    """
    client = await get_redis_client()
    result = await client.delete(f"doc:{doc_id}")
    return result > 0  # type: ignore


async def list_all_documents() -> list[Dict[str, Any]]:
    """
    Redis에 저장된 모든 문서 목록 조회

    Returns:
        문서 정보 리스트 (doc_id + 메타데이터)
    """
    client = await get_redis_client()

    # 모든 doc:* 키 찾기
    keys: list[bytes] = []
    cursor = 0
    while True:
        cursor, batch = await client.scan(cursor, match="doc:*", count=100)  # type: ignore
        keys.extend(batch)
        if cursor == 0:
            break

    documents: list[Dict[str, Any]] = []
    for key in keys:
        doc_id = key.decode("utf-8").replace("doc:", "")
        metadata_bytes = await client.hget(key, "metadata")  # type: ignore
        if metadata_bytes:
            metadata = json.loads(metadata_bytes.decode("utf-8"))  # type: ignore
            documents.append({"doc_id": doc_id, **metadata})

    return documents
