"""
LlamaIndex Patterns - Standalone Examples

LlamaIndex를 사용한 계층적 인덱싱 패턴들의 독립 실행 예제
FastAPI 없이 순수 LlamaIndex 기능을 학습할 수 있습니다.
"""

import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any
import pandas as pd
from io import StringIO

from llama_index.core import (
    Document,
    VectorStoreIndex,
    SummaryIndex,
    KeywordTableIndex,
    Settings,
)
from llama_index.core.node_parser import (
    HierarchicalNodeParser,
    SentenceSplitter,
)
from llama_index.core.schema import TextNode, NodeRelationship, RelatedNodeInfo
from llama_index.core.query_engine import RouterQueryEngine
from llama_index.core.selectors import LLMSingleSelector
from llama_index.core.tools import QueryEngineTool, ToolMetadata

from app.configs.llama_index import init_llama_index_settings


# LlamaIndex 전역 설정 초기화
init_llama_index_settings()
Settings.chunk_size = 512
Settings.chunk_overlap = 50


def print_section(title: str):
    """섹션 헤더 출력"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


# ============================================================================
# Pattern 1: Basic Vector Index
# ============================================================================


async def pattern_1_basic_vector_index():
    """
    패턴 1: 기본 벡터 인덱스

    단일 문서를 벡터화하여 인덱싱하고 의미 기반 검색 수행
    """
    print_section("Pattern 1: Basic Vector Index")

    # 샘플 문서
    text = """
    LlamaIndex is a data framework for LLM applications to ingest, structure,
    and access private or domain-specific data. It provides tools for data loading,
    indexing, querying, and retrieval augmented generation (RAG).

    Key features include:
    - Data connectors to various sources
    - Data indexing and structuring
    - Query engines for natural language queries
    - Composable architecture
    """

    # Document 생성
    document = Document(text=text, metadata={"source": "intro"})

    # Vector Index 생성
    start = datetime.now()
    index = VectorStoreIndex.from_documents([document])
    print(f"✓ Index created in {(datetime.now() - start).total_seconds():.2f}s")

    # 쿼리 실행
    query_engine = index.as_query_engine()

    query = "What is LlamaIndex?"
    print(f"\nQuery: {query}")
    response = query_engine.query(query)
    print(f"Response: {response}\n")

    return index


# ============================================================================
# Pattern 2: Hierarchical Node Parsing
# ============================================================================


async def pattern_2_hierarchical_nodes():
    """
    패턴 2: 계층적 노드 파싱

    큰 문서를 여러 레벨의 청크로 나누어 계층 구조 생성
    """
    print_section("Pattern 2: Hierarchical Node Parsing")

    # 긴 문서 샘플
    long_text = (
        """
    # Introduction to Machine Learning

    Machine learning is a subset of artificial intelligence that focuses on building
    systems that learn from data. Instead of being explicitly programmed, these systems
    improve their performance through experience.

    ## Supervised Learning

    Supervised learning involves training models on labeled data. The algorithm learns
    to map inputs to outputs based on example input-output pairs. Common applications
    include classification and regression tasks.

    ### Classification

    Classification tasks involve predicting discrete categories. For example, determining
    whether an email is spam or not spam. Popular algorithms include decision trees,
    random forests, and neural networks.

    ### Regression

    Regression tasks predict continuous values. For instance, predicting house prices
    based on features like size, location, and age. Linear regression and polynomial
    regression are common approaches.

    ## Unsupervised Learning

    Unsupervised learning works with unlabeled data to discover patterns and structures.
    Clustering and dimensionality reduction are primary use cases.
    """
        * 3
    )  # 반복하여 충분한 길이 확보

    # Document 생성
    document = Document(text=long_text, metadata={"source": "ml_guide"})

    # 계층적 파서 생성 (3레벨)
    node_parser = HierarchicalNodeParser.from_defaults(chunk_sizes=[2048, 512, 128])

    # 노드 파싱
    start = datetime.now()
    nodes = node_parser.get_nodes_from_documents([document])

    # Leaf nodes 필터링 (자식 노드가 없는 노드들)
    from llama_index.core.schema import NodeRelationship

    leaf_nodes = [
        node for node in nodes if not node.relationships.get(NodeRelationship.CHILD)
    ]

    print(f"✓ Parsed into {len(nodes)} total nodes, {len(leaf_nodes)} leaf nodes")
    print(f"  Execution time: {(datetime.now() - start).total_seconds():.2f}s")

    # Leaf 노드로 인덱스 생성
    index = VectorStoreIndex(leaf_nodes)

    # 쿼리
    query_engine = index.as_query_engine()
    query = "What is the difference between classification and regression?"
    print(f"\nQuery: {query}")
    response = query_engine.query(query)
    print(f"Response: {response}\n")

    return {"index": index, "nodes": nodes, "leaf_nodes": leaf_nodes}


# ============================================================================
# Pattern 3: JSON Document Indexing
# ============================================================================


async def pattern_3_json_indexing():
    """
    패턴 3: JSON 문서 인덱싱

    구조화된 JSON 데이터를 평탄화하여 인덱싱
    """
    print_section("Pattern 3: JSON Document Indexing")

    # 샘플 JSON 데이터
    json_data = {
        "product": {
            "id": "P123",
            "name": "Wireless Headphones",
            "category": "Electronics",
            "specs": {
                "battery_life": "30 hours",
                "connectivity": "Bluetooth 5.0",
                "noise_cancellation": True,
            },
            "reviews": [
                {"rating": 5, "comment": "Great sound quality!"},
                {"rating": 4, "comment": "Good but expensive"},
            ],
        }
    }

    # JSON을 계층적 텍스트로 변환
    def json_to_hierarchical_text(data: Any, prefix: str = "") -> List[str]:
        texts = []
        if isinstance(data, dict):
            for key, value in data.items():
                new_prefix = f"{prefix}.{key}" if prefix else key
                if isinstance(value, (dict, list)):
                    texts.extend(json_to_hierarchical_text(value, new_prefix))
                else:
                    texts.append(f"{new_prefix}: {value}")
        elif isinstance(data, list):
            for i, item in enumerate(data):
                new_prefix = f"{prefix}[{i}]"
                if isinstance(item, (dict, list)):
                    texts.extend(json_to_hierarchical_text(item, new_prefix))
                else:
                    texts.append(f"{new_prefix}: {item}")
        return texts

    # 노드 생성
    text_lines = json_to_hierarchical_text(json_data)
    nodes = [
        TextNode(text=line, metadata={"source": "json", "type": "field"})
        for line in text_lines
    ]

    # 전체 JSON 요약 노드 추가
    summary_text = f"Product: {json_data['product']['name']}, Category: {json_data['product']['category']}"
    nodes.append(
        TextNode(text=summary_text, metadata={"source": "json", "type": "summary"})
    )

    print(f"✓ Created {len(nodes)} nodes from JSON")
    print(f"  Sample fields: {text_lines[:3]}")

    # 인덱스 생성
    index = VectorStoreIndex(nodes)

    # 쿼리
    query_engine = index.as_query_engine()
    query = "What is the battery life of the product?"
    print(f"\nQuery: {query}")
    response = query_engine.query(query)
    print(f"Response: {response}\n")

    return index


# ============================================================================
# Pattern 4: Table/CSV Indexing
# ============================================================================


async def pattern_4_table_indexing():
    """
    패턴 4: 테이블 데이터 인덱싱

    CSV 데이터를 행/열 기반으로 구조화하여 인덱싱
    """
    print_section("Pattern 4: Table/CSV Indexing")

    # 샘플 CSV 데이터
    csv_data = """name,age,city,occupation,salary
John Smith,35,New York,Engineer,95000
Jane Doe,28,San Francisco,Designer,85000
Bob Johnson,42,Seattle,Manager,110000
Alice Williams,31,Boston,Analyst,75000
"""

    # DataFrame으로 변환
    df = pd.read_csv(StringIO(csv_data))
    print(f"✓ Loaded table with {len(df)} rows and {len(df.columns)} columns")
    print(f"  Columns: {list(df.columns)}\n")

    # 각 행을 노드로 생성
    row_nodes = []
    for idx, row in df.iterrows():
        row_text = " | ".join([f"{col}: {row[col]}" for col in df.columns])
        node = TextNode(text=row_text, metadata={"row_index": idx, "type": "row"})
        row_nodes.append(node)

    # 각 열의 통계 노드 생성
    column_nodes = []
    for col in df.columns:
        if df[col].dtype in ["int64", "float64"]:
            stats = df[col].describe()
            col_text = f"Column '{col}' statistics: mean={stats['mean']:.2f}, min={stats['min']}, max={stats['max']}"
        else:
            col_text = f"Column '{col}' values: {', '.join(df[col].unique())}"

        node = TextNode(text=col_text, metadata={"column": col, "type": "column_stats"})
        column_nodes.append(node)

    # 테이블 요약 노드
    summary_text = f"Employee table with {len(df)} employees. Average age: {df['age'].mean():.1f}, Average salary: ${df['salary'].mean():,.0f}"
    summary_node = TextNode(text=summary_text, metadata={"type": "summary"})

    # 모든 노드 결합
    all_nodes = row_nodes + column_nodes + [summary_node]
    print(
        f"✓ Created {len(all_nodes)} nodes ({len(row_nodes)} rows + {len(column_nodes)} columns + 1 summary)"
    )

    # 인덱스 생성
    index = VectorStoreIndex(all_nodes)

    # 쿼리
    query_engine = index.as_query_engine()
    query = "What is the average salary?"
    print(f"\nQuery: {query}")
    response = query_engine.query(query)
    print(f"Response: {response}\n")

    return index


# ============================================================================
# Pattern 5: Router Query Engine (Multiple Indices)
# ============================================================================


async def pattern_5_router_query_engine():
    """
    패턴 5: Router Query Engine

    여러 인덱스 타입을 생성하고 쿼리에 따라 자동 선택
    """
    print_section("Pattern 5: Router Query Engine")

    # 여러 문서 생성
    docs = [
        Document(
            text="LlamaIndex provides data connectors for various sources like databases, APIs, and files.",
            metadata={"category": "technical"},
        ),
        Document(
            text="The company was founded in 2023 and has 50 employees across 3 offices.",
            metadata={"category": "business"},
        ),
        Document(
            text="Our product features include real-time indexing, semantic search, and RAG capabilities.",
            metadata={"category": "features"},
        ),
    ]

    print(f"✓ Created {len(docs)} documents")

    # 여러 인덱스 타입 생성
    vector_index = VectorStoreIndex.from_documents(docs)
    summary_index = SummaryIndex.from_documents(docs)
    keyword_index = KeywordTableIndex.from_documents(docs)

    print("✓ Created 3 index types: Vector, Summary, Keyword")

    # Query Engine Tools
    vector_tool = QueryEngineTool(
        query_engine=vector_index.as_query_engine(),
        metadata=ToolMetadata(
            name="vector_search",
            description="Use for semantic search and finding similar content",
        ),
    )

    summary_tool = QueryEngineTool(
        query_engine=summary_index.as_query_engine(),
        metadata=ToolMetadata(
            name="summary_search", description="Use for getting summaries and overviews"
        ),
    )

    keyword_tool = QueryEngineTool(
        query_engine=keyword_index.as_query_engine(),
        metadata=ToolMetadata(
            name="keyword_search", description="Use for exact keyword matching"
        ),
    )

    # Router 생성
    router_query_engine = RouterQueryEngine(
        selector=LLMSingleSelector.from_defaults(),
        query_engine_tools=[vector_tool, summary_tool, keyword_tool],
    )

    print("✓ Created Router Query Engine")

    # 다양한 쿼리 테스트
    queries = [
        "What data sources are supported?",  # Vector search
        "Give me an overview of everything",  # Summary
        "employees offices",  # Keyword
    ]

    for query in queries:
        print(f"\nQuery: {query}")
        response = router_query_engine.query(query)
        print(f"Response: {response}")

    return router_query_engine


# ============================================================================
# Pattern 6: Custom Parent-Child Nodes
# ============================================================================


async def pattern_6_custom_hierarchical_nodes():
    """
    패턴 6: 커스텀 계층적 노드

    수동으로 Parent-Child 관계를 정의
    """
    print_section("Pattern 6: Custom Parent-Child Nodes")

    # 샘플 섹션 데이터
    sections = [
        {
            "title": "Introduction",
            "text": "This is an introduction to our product. " * 20,
        },
        {
            "title": "Features",
            "text": "Our product has many great features including AI, automation, and analytics. "
            * 20,
        },
    ]

    all_nodes = []

    for section in sections:
        # Parent 노드 (전체 섹션)
        parent_node = TextNode(
            text=section["text"], metadata={"title": section["title"], "type": "parent"}
        )

        # Child 노드들 (작은 청크로 분할)
        splitter = SentenceSplitter(chunk_size=100, chunk_overlap=10)
        child_texts = splitter.split_text(section["text"])

        child_nodes = []
        for i, child_text in enumerate(child_texts):
            child_node = TextNode(
                text=child_text,
                metadata={"title": section["title"], "type": "child", "chunk": i},
            )

            # Child -> Parent 관계
            child_node.relationships[NodeRelationship.PARENT] = RelatedNodeInfo(
                node_id=parent_node.node_id
            )

            child_nodes.append(child_node)

        # Parent -> Children 관계
        parent_node.relationships[NodeRelationship.CHILD] = [
            RelatedNodeInfo(node_id=child.node_id) for child in child_nodes
        ]

        all_nodes.extend([parent_node] + child_nodes)

    print(f"✓ Created custom hierarchy:")
    print(f"  - {len(sections)} parent nodes")
    print(
        f"  - {len([n for n in all_nodes if n.metadata.get('type') == 'child'])} child nodes"
    )
    print(f"  - Total: {len(all_nodes)} nodes")

    # Child 노드만으로 인덱스 생성
    child_nodes = [n for n in all_nodes if n.metadata.get("type") == "child"]
    index = VectorStoreIndex(child_nodes)

    # 쿼리
    query_engine = index.as_query_engine()
    query = "What are the main features?"
    print(f"\nQuery: {query}")
    response = query_engine.query(query)
    print(f"Response: {response}\n")

    return {"index": index, "all_nodes": all_nodes}


# ============================================================================
# Pattern 7: Metadata Filtering
# ============================================================================


async def pattern_7_metadata_filtering():
    """
    패턴 7: 메타데이터 필터링

    메타데이터를 사용하여 검색 범위 제한
    """
    print_section("Pattern 7: Metadata Filtering")

    # 여러 카테고리의 문서
    docs = [
        Document(
            text="Python is a versatile programming language.",
            metadata={"category": "programming", "language": "python"},
        ),
        Document(
            text="JavaScript is widely used for web development.",
            metadata={"category": "programming", "language": "javascript"},
        ),
        Document(
            text="Machine learning models require training data.",
            metadata={"category": "ai", "topic": "ml"},
        ),
        Document(
            text="Deep learning uses neural networks.",
            metadata={"category": "ai", "topic": "dl"},
        ),
    ]

    print(f"✓ Created {len(docs)} documents with categories")

    # 인덱스 생성
    index = VectorStoreIndex.from_documents(docs)

    # 일반 쿼리
    query_engine = index.as_query_engine()
    query = "Tell me about programming"
    print(f"\nQuery (no filter): {query}")
    response = query_engine.query(query)
    print(f"Response: {response}")

    # 메타데이터 필터 쿼리
    from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter

    filtered_query_engine = index.as_query_engine(
        filters=MetadataFilters(filters=[ExactMatchFilter(key="category", value="ai")])
    )

    print(f"\nQuery (filtered to 'ai' category): {query}")
    response = filtered_query_engine.query(query)
    print(f"Response: {response}\n")

    return index


# ============================================================================
# Main Execution
# ============================================================================


async def main():
    """모든 패턴 실행"""
    print("\n" + "█" * 80)
    print("  LlamaIndex Patterns - Standalone Examples")
    print("█" * 80)

    patterns = [
        ("Basic Vector Index", pattern_1_basic_vector_index),
        ("Hierarchical Node Parsing", pattern_2_hierarchical_nodes),
        ("JSON Document Indexing", pattern_3_json_indexing),
        ("Table/CSV Indexing", pattern_4_table_indexing),
        ("Router Query Engine", pattern_5_router_query_engine),
        ("Custom Hierarchical Nodes", pattern_6_custom_hierarchical_nodes),
        ("Metadata Filtering", pattern_7_metadata_filtering),
    ]

    for i, (name, pattern_func) in enumerate(patterns, 1):
        try:
            await pattern_func()
        except Exception as e:
            print(f"❌ Error in {name}: {e}")

    print("\n" + "█" * 80)
    print("  All patterns completed!")
    print("█" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
