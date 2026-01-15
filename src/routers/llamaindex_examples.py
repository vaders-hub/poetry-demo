"""
LlamaIndex Hierarchical Indexing Examples Router

이 모듈은 LlamaIndex를 사용하여 복잡한 문서 구조(Table, JSON)를 계층적으로 인덱싱하는 방법을 학습하기 위한 예제들을 제공합니다.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import json
import asyncio
from datetime import datetime
import pandas as pd
from io import StringIO

from llama_index.core import (
    Document,
    VectorStoreIndex,
    SummaryIndex,
    TreeIndex,
    KeywordTableIndex,
    Settings,
)
from llama_index.core.node_parser import (
    SimpleNodeParser,
    HierarchicalNodeParser,
    SentenceSplitter,
)
from llama_index.core.schema import TextNode, NodeRelationship, RelatedNodeInfo
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.query_engine import RouterQueryEngine
from llama_index.core.selectors import LLMSingleSelector
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.retrievers import RecursiveRetriever
from llama_index.core.query_engine import RetrieverQueryEngine

router = APIRouter(prefix="/llamaindex", tags=["LlamaIndex Examples"])

# Global settings for LlamaIndex
Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.1)
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
Settings.chunk_size = 512
Settings.chunk_overlap = 50

# Global storage for indices (in production, use persistent storage)
_indices_storage = {}


# ============================================================================
# Request/Response Models
# ============================================================================


class DocumentRequest(BaseModel):
    """단순 문서 요청"""
    text: str = Field(description="인덱싱할 문서 텍스트")
    doc_id: str = Field(description="문서 ID")


class QueryRequest(BaseModel):
    """쿼리 요청"""
    query: str = Field(description="질의문")
    index_id: str = Field(description="인덱스 ID")


class JSONDocumentRequest(BaseModel):
    """JSON 문서 요청"""
    json_data: Dict[str, Any] = Field(description="JSON 데이터")
    doc_id: str = Field(description="문서 ID")


class TableDataRequest(BaseModel):
    """테이블 데이터 요청"""
    csv_data: str = Field(description="CSV 형식의 테이블 데이터")
    doc_id: str = Field(description="문서 ID")


class HierarchicalDocRequest(BaseModel):
    """계층적 문서 요청"""
    sections: List[Dict[str, Any]] = Field(description="섹션 목록")
    doc_id: str = Field(description="문서 ID")


class MultiDocumentRequest(BaseModel):
    """다중 문서 요청"""
    documents: List[Dict[str, str]] = Field(description="문서 목록 (id, text, metadata)")
    index_id: str = Field(description="인덱스 ID")


# ============================================================================
# Example 1: 기본 Vector Index (Simple Document Indexing)
# ============================================================================


@router.post("/basic-vector-index")
async def create_basic_vector_index(request: DocumentRequest):
    """
    기본 벡터 인덱스 생성

    단일 문서를 벡터 인덱스로 변환하여 저장
    """
    try:
        start_time = datetime.now()

        # Document 생성
        document = Document(
            text=request.text,
            metadata={"doc_id": request.doc_id, "created_at": datetime.now().isoformat()}
        )

        # VectorStoreIndex 생성
        index = VectorStoreIndex.from_documents([document])

        # 인덱스 저장
        index_id = f"vector_{request.doc_id}"
        _indices_storage[index_id] = index

        end_time = datetime.now()

        return {
            "index_id": index_id,
            "index_type": "VectorStoreIndex",
            "num_documents": 1,
            "text_length": len(request.text),
            "execution_time_ms": (end_time - start_time).total_seconds() * 1000,
            "explanation": "Basic vector index created using embeddings"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Example 2: Query Vector Index
# ============================================================================


@router.post("/query-vector-index")
async def query_vector_index(request: QueryRequest):
    """
    벡터 인덱스 쿼리

    저장된 벡터 인덱스에 대해 질의 수행
    """
    try:
        if request.index_id not in _indices_storage:
            raise HTTPException(status_code=404, detail=f"Index {request.index_id} not found")

        start_time = datetime.now()

        # 인덱스 가져오기
        index = _indices_storage[request.index_id]

        # 쿼리 엔진 생성
        query_engine = index.as_query_engine()

        # 쿼리 실행
        response = query_engine.query(request.query)

        end_time = datetime.now()

        return {
            "query": request.query,
            "response": str(response),
            "source_nodes": [
                {
                    "text": node.node.text[:200] + "..." if len(node.node.text) > 200 else node.node.text,
                    "score": node.score,
                    "metadata": node.node.metadata
                }
                for node in response.source_nodes
            ],
            "execution_time_ms": (end_time - start_time).total_seconds() * 1000,
            "explanation": "Query executed against vector index"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Example 3: Hierarchical Node Parser (계층적 노드 파싱)
# ============================================================================


@router.post("/hierarchical-index")
async def create_hierarchical_index(request: HierarchicalDocRequest):
    """
    계층적 인덱스 생성

    문서를 계층적 구조로 파싱하여 인덱스 생성
    Parent nodes (큰 청크) -> Child nodes (작은 청크)
    """
    try:
        start_time = datetime.now()

        # 계층적 노드 파서 생성
        node_parser = HierarchicalNodeParser.from_defaults(
            chunk_sizes=[2048, 512, 128]  # 3단계 계층: 큰 청크 -> 중간 -> 작은 청크
        )

        # 섹션별 Document 생성
        documents = []
        for section in request.sections:
            doc = Document(
                text=section.get("text", ""),
                metadata={
                    "doc_id": request.doc_id,
                    "section_title": section.get("title", ""),
                    "section_level": section.get("level", 1),
                    "created_at": datetime.now().isoformat()
                }
            )
            documents.append(doc)

        # 계층적 노드 파싱
        nodes = node_parser.get_nodes_from_documents(documents)

        # Leaf nodes 필터링 (자식 노드가 없는 노드들)
        leaf_nodes = [node for node in nodes if not node.relationships.get(NodeRelationship.CHILD)]

        # VectorStoreIndex 생성 (leaf nodes만 사용)
        index = VectorStoreIndex(leaf_nodes)

        # 인덱스 저장
        index_id = f"hierarchical_{request.doc_id}"
        _indices_storage[index_id] = {
            "index": index,
            "all_nodes": nodes,
            "leaf_nodes": leaf_nodes
        }

        end_time = datetime.now()

        return {
            "index_id": index_id,
            "index_type": "Hierarchical VectorStoreIndex",
            "num_sections": len(request.sections),
            "total_nodes": len(nodes),
            "leaf_nodes": len(leaf_nodes),
            "hierarchy_levels": 3,
            "execution_time_ms": (end_time - start_time).total_seconds() * 1000,
            "explanation": "Hierarchical index with 3 levels: 2048 -> 512 -> 128 chunks"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Example 4: JSON Document Indexing (구조화된 데이터)
# ============================================================================


@router.post("/json-index")
async def create_json_index(request: JSONDocumentRequest):
    """
    JSON 문서 인덱싱

    구조화된 JSON 데이터를 평탄화하여 인덱싱
    """
    try:
        start_time = datetime.now()

        # JSON을 텍스트로 변환하는 헬퍼 함수
        def json_to_text(data: Any, prefix: str = "") -> List[str]:
            """JSON을 계층적 텍스트로 변환"""
            texts = []

            if isinstance(data, dict):
                for key, value in data.items():
                    new_prefix = f"{prefix}.{key}" if prefix else key
                    if isinstance(value, (dict, list)):
                        texts.extend(json_to_text(value, new_prefix))
                    else:
                        texts.append(f"{new_prefix}: {value}")
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    new_prefix = f"{prefix}[{i}]"
                    if isinstance(item, (dict, list)):
                        texts.extend(json_to_text(item, new_prefix))
                    else:
                        texts.append(f"{new_prefix}: {item}")
            else:
                texts.append(f"{prefix}: {data}")

            return texts

        # JSON을 텍스트로 변환
        text_lines = json_to_text(request.json_data)

        # 각 필드를 별도의 노드로 생성
        nodes = []
        for line in text_lines:
            node = TextNode(
                text=line,
                metadata={
                    "doc_id": request.doc_id,
                    "source": "json",
                    "full_json": json.dumps(request.json_data)
                }
            )
            nodes.append(node)

        # 전체 JSON도 하나의 노드로 추가
        summary_node = TextNode(
            text=json.dumps(request.json_data, indent=2),
            metadata={
                "doc_id": request.doc_id,
                "source": "json",
                "node_type": "summary"
            }
        )
        nodes.append(summary_node)

        # 인덱스 생성
        index = VectorStoreIndex(nodes)

        # 인덱스 저장
        index_id = f"json_{request.doc_id}"
        _indices_storage[index_id] = index

        end_time = datetime.now()

        return {
            "index_id": index_id,
            "index_type": "JSON VectorStoreIndex",
            "num_fields": len(text_lines),
            "num_nodes": len(nodes),
            "execution_time_ms": (end_time - start_time).total_seconds() * 1000,
            "sample_fields": text_lines[:5],
            "explanation": "JSON data flattened and indexed with hierarchical field paths"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Example 5: Table/CSV Indexing (테이블 데이터)
# ============================================================================


@router.post("/table-index")
async def create_table_index(request: TableDataRequest):
    """
    테이블 데이터 인덱싱

    CSV 형식의 테이블 데이터를 행/열 기반으로 인덱싱
    """
    try:
        start_time = datetime.now()

        # CSV 파싱
        df = pd.read_csv(StringIO(request.csv_data))

        # 각 행을 별도의 노드로 생성
        row_nodes = []
        for idx, row in df.iterrows():
            row_text = " | ".join([f"{col}: {row[col]}" for col in df.columns])
            node = TextNode(
                text=row_text,
                metadata={
                    "doc_id": request.doc_id,
                    "row_index": idx,
                    "source": "table",
                    "node_type": "row"
                }
            )
            row_nodes.append(node)

        # 각 열의 요약도 노드로 생성
        column_nodes = []
        for col in df.columns:
            col_summary = f"Column '{col}': {df[col].describe().to_dict() if df[col].dtype in ['int64', 'float64'] else df[col].value_counts().to_dict()}"
            node = TextNode(
                text=col_summary,
                metadata={
                    "doc_id": request.doc_id,
                    "column_name": col,
                    "source": "table",
                    "node_type": "column_summary"
                }
            )
            column_nodes.append(node)

        # 전체 테이블 요약
        table_summary = f"Table with {len(df)} rows and {len(df.columns)} columns. Columns: {', '.join(df.columns)}"
        summary_node = TextNode(
            text=table_summary,
            metadata={
                "doc_id": request.doc_id,
                "source": "table",
                "node_type": "table_summary"
            }
        )

        # 모든 노드 결합
        all_nodes = row_nodes + column_nodes + [summary_node]

        # 인덱스 생성
        index = VectorStoreIndex(all_nodes)

        # 인덱스 저장
        index_id = f"table_{request.doc_id}"
        _indices_storage[index_id] = index

        end_time = datetime.now()

        return {
            "index_id": index_id,
            "index_type": "Table VectorStoreIndex",
            "num_rows": len(df),
            "num_columns": len(df.columns),
            "columns": list(df.columns),
            "total_nodes": len(all_nodes),
            "execution_time_ms": (end_time - start_time).total_seconds() * 1000,
            "explanation": "Table indexed with row nodes, column summaries, and table summary"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Example 6: Multiple Index Types (Router Query Engine)
# ============================================================================


@router.post("/multi-index")
async def create_multi_index(request: MultiDocumentRequest):
    """
    다중 인덱스 타입 생성 및 Router Query Engine

    여러 문서를 서로 다른 인덱스 타입으로 생성하고
    Router를 사용하여 적절한 인덱스를 자동 선택
    """
    try:
        start_time = datetime.now()

        # 문서 생성
        documents = []
        for doc_data in request.documents:
            doc = Document(
                text=doc_data["text"],
                metadata={
                    "doc_id": doc_data["id"],
                    "category": doc_data.get("category", "general"),
                }
            )
            documents.append(doc)

        # 1. Vector Index (의미 기반 검색)
        vector_index = VectorStoreIndex.from_documents(documents)

        # 2. Summary Index (전체 문서 요약)
        summary_index = SummaryIndex.from_documents(documents)

        # 3. Keyword Table Index (키워드 기반 검색)
        keyword_index = KeywordTableIndex.from_documents(documents)

        # Query Engine Tools 생성
        vector_tool = QueryEngineTool(
            query_engine=vector_index.as_query_engine(),
            metadata=ToolMetadata(
                name="vector_search",
                description="Useful for semantic search and finding similar content based on meaning"
            )
        )

        summary_tool = QueryEngineTool(
            query_engine=summary_index.as_query_engine(),
            metadata=ToolMetadata(
                name="summary_search",
                description="Useful for getting summaries and overviews of all documents"
            )
        )

        keyword_tool = QueryEngineTool(
            query_engine=keyword_index.as_query_engine(),
            metadata=ToolMetadata(
                name="keyword_search",
                description="Useful for keyword-based search and exact term matching"
            )
        )

        # Router Query Engine 생성
        router_query_engine = RouterQueryEngine(
            selector=LLMSingleSelector.from_defaults(),
            query_engine_tools=[vector_tool, summary_tool, keyword_tool]
        )

        # 인덱스 저장
        index_id = request.index_id
        _indices_storage[index_id] = {
            "router": router_query_engine,
            "vector_index": vector_index,
            "summary_index": summary_index,
            "keyword_index": keyword_index
        }

        end_time = datetime.now()

        return {
            "index_id": index_id,
            "index_types": ["VectorStoreIndex", "SummaryIndex", "KeywordTableIndex"],
            "num_documents": len(documents),
            "execution_time_ms": (end_time - start_time).total_seconds() * 1000,
            "explanation": "Created multiple index types with router for automatic selection"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Example 7: Query Router Index
# ============================================================================


@router.post("/query-router")
async def query_router_index(request: QueryRequest):
    """
    Router Query Engine을 사용한 쿼리

    질의 내용에 따라 자동으로 적절한 인덱스 선택
    """
    try:
        if request.index_id not in _indices_storage:
            raise HTTPException(status_code=404, detail=f"Index {request.index_id} not found")

        storage = _indices_storage[request.index_id]
        if "router" not in storage:
            raise HTTPException(status_code=400, detail="This is not a router index")

        start_time = datetime.now()

        # Router로 쿼리 실행
        router = storage["router"]
        response = router.query(request.query)

        end_time = datetime.now()

        return {
            "query": request.query,
            "response": str(response),
            "selected_tool": getattr(response, "metadata", {}).get("selector_result", "unknown"),
            "execution_time_ms": (end_time - start_time).total_seconds() * 1000,
            "explanation": "Router automatically selected the best index for this query"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Example 8: Recursive Retriever (재귀적 검색)
# ============================================================================


@router.post("/recursive-retriever")
async def query_with_recursive_retriever(request: QueryRequest):
    """
    Recursive Retriever를 사용한 계층적 검색

    작은 청크로 검색하고 -> 부모 청크의 컨텍스트 활용
    """
    try:
        if request.index_id not in _indices_storage:
            raise HTTPException(status_code=404, detail=f"Index {request.index_id} not found")

        storage = _indices_storage[request.index_id]
        if "all_nodes" not in storage:
            raise HTTPException(status_code=400, detail="This index does not support recursive retrieval")

        start_time = datetime.now()

        # Recursive Retriever 생성
        index = storage["index"]
        all_nodes = storage["all_nodes"]

        # node_id -> node 매핑 생성
        node_dict = {node.node_id: node for node in all_nodes}

        # Retriever 생성
        retriever = RecursiveRetriever(
            "vector",
            retriever_dict={"vector": index.as_retriever()},
            node_dict=node_dict
        )

        # Query Engine 생성
        query_engine = RetrieverQueryEngine.from_args(retriever)

        # 쿼리 실행
        response = query_engine.query(request.query)

        end_time = datetime.now()

        return {
            "query": request.query,
            "response": str(response),
            "num_source_nodes": len(response.source_nodes),
            "execution_time_ms": (end_time - start_time).total_seconds() * 1000,
            "explanation": "Used recursive retriever to fetch parent context from hierarchical nodes"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Example 9: Custom Node Creation (커스텀 노드)
# ============================================================================


@router.post("/custom-nodes")
async def create_custom_node_index(request: HierarchicalDocRequest):
    """
    커스텀 노드 관계 설정

    수동으로 Parent-Child 관계를 정의하여 계층 구조 생성
    """
    try:
        start_time = datetime.now()

        all_nodes = []
        parent_nodes = []

        # 각 섹션에 대해 Parent-Child 노드 생성
        for section in request.sections:
            # Parent 노드 (전체 섹션)
            parent_node = TextNode(
                text=section["text"],
                metadata={
                    "doc_id": request.doc_id,
                    "section_title": section.get("title", ""),
                    "node_type": "parent"
                }
            )

            # Child 노드들 (섹션을 작은 청크로 분할)
            splitter = SentenceSplitter(chunk_size=256, chunk_overlap=20)
            child_texts = splitter.split_text(section["text"])

            child_nodes = []
            for i, child_text in enumerate(child_texts):
                child_node = TextNode(
                    text=child_text,
                    metadata={
                        "doc_id": request.doc_id,
                        "section_title": section.get("title", ""),
                        "node_type": "child",
                        "chunk_index": i
                    }
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

            parent_nodes.append(parent_node)
            all_nodes.extend([parent_node] + child_nodes)

        # Child 노드만으로 인덱스 생성 (검색은 작은 청크로)
        child_only_nodes = [n for n in all_nodes if n.metadata.get("node_type") == "child"]
        index = VectorStoreIndex(child_only_nodes)

        # 인덱스 저장
        index_id = f"custom_{request.doc_id}"
        _indices_storage[index_id] = {
            "index": index,
            "all_nodes": all_nodes,
            "parent_nodes": parent_nodes,
            "child_nodes": child_only_nodes
        }

        end_time = datetime.now()

        return {
            "index_id": index_id,
            "index_type": "Custom Hierarchical Index",
            "num_sections": len(request.sections),
            "num_parent_nodes": len(parent_nodes),
            "num_child_nodes": len(child_only_nodes),
            "total_nodes": len(all_nodes),
            "execution_time_ms": (end_time - start_time).total_seconds() * 1000,
            "explanation": "Custom parent-child relationships with manual node creation"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Example 10: List All Indices
# ============================================================================


@router.get("/list-indices")
async def list_indices():
    """
    생성된 모든 인덱스 목록 조회
    """
    indices_info = []

    for index_id, storage in _indices_storage.items():
        if isinstance(storage, dict):
            index_type = "Multi-Index" if "router" in storage else "Hierarchical"
            num_nodes = len(storage.get("all_nodes", [])) if "all_nodes" in storage else "N/A"
        else:
            index_type = type(storage).__name__
            num_nodes = "N/A"

        indices_info.append({
            "index_id": index_id,
            "index_type": index_type,
            "num_nodes": num_nodes,
        })

    return {
        "total_indices": len(_indices_storage),
        "indices": indices_info
    }


# ============================================================================
# Example 11: Delete Index
# ============================================================================


@router.delete("/delete-index/{index_id}")
async def delete_index(index_id: str):
    """
    인덱스 삭제
    """
    if index_id not in _indices_storage:
        raise HTTPException(status_code=404, detail=f"Index {index_id} not found")

    del _indices_storage[index_id]

    return {
        "message": f"Index {index_id} deleted successfully",
        "remaining_indices": len(_indices_storage)
    }
