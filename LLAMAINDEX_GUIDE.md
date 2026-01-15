# LlamaIndex 계층적 인덱싱 완벽 가이드

LlamaIndex를 활용하여 복잡한 문서 구조(Table, JSON)를 계층적으로 인덱싱하는 방법을 학습합니다.

---

## 📚 목차

1. [LlamaIndex란?](#1-llamaindex란)
2. [왜 계층적 인덱싱인가?](#2-왜-계층적-인덱싱인가)
3. [핵심 개념](#3-핵심-개념)
4. [인덱스 타입](#4-인덱스-타입)
5. [실습 예제](#5-실습-예제)
6. [FastAPI 엔드포인트](#6-fastapi-엔드포인트)
7. [고급 패턴](#7-고급-패턴)
8. [성능 최적화](#8-성능-최적화)
9. [문제 해결](#9-문제-해결)

---

## 1. LlamaIndex란?

**LlamaIndex**는 LLM 애플리케이션을 위한 데이터 프레임워크입니다.

### 주요 기능

- **데이터 연결**: 다양한 소스(파일, DB, API)에서 데이터 로드
- **데이터 인덱싱**: 효율적인 검색을 위한 구조화
- **쿼리 엔진**: 자연어 질의 처리
- **RAG (Retrieval Augmented Generation)**: 검색 기반 생성

### LangChain vs LlamaIndex

| 기능 | LangChain | LlamaIndex |
|-----|-----------|-----------|
| 주 목적 | 체인 구성, 워크플로우 | 데이터 인덱싱, 검색 |
| 강점 | 유연한 파이프라인 | 계층적 인덱싱 |
| 사용 사례 | 복잡한 LLM 워크플로우 | RAG, 문서 검색 |

---

## 2. 왜 계층적 인덱싱인가?

### 문제점: Flat Indexing의 한계

```
전체 문서 (10,000 단어)
  → 하나의 큰 임베딩
  → 검색 시 정확도 낮음
  → 컨텍스트 손실
```

### 해결책: 계층적 인덱싱

```
전체 문서
  ├── 섹션 1 (Parent Node)
  │   ├── 청크 1-1 (Child Node)
  │   ├── 청크 1-2
  │   └── 청크 1-3
  ├── 섹션 2 (Parent Node)
  │   ├── 청크 2-1
  │   └── 청크 2-2
```

### 장점

1. **정확한 검색**: 작은 청크로 세밀한 매칭
2. **풍부한 컨텍스트**: 필요 시 부모 노드 참조
3. **효율적인 메모리**: 필요한 부분만 로드
4. **유연한 쿼리**: 여러 레벨에서 검색 가능

---

## 3. 핵심 개념

### Document

문서의 기본 단위입니다.

```python
from llama_index.core import Document

doc = Document(
    text="LlamaIndex is awesome!",
    metadata={"source": "blog", "date": "2024-01-01"}
)
```

### Node

인덱싱의 최소 단위입니다.

```python
from llama_index.core.schema import TextNode

node = TextNode(
    text="Chunk of text",
    metadata={"chunk_id": 1}
)
```

### Node 관계

```python
from llama_index.core.schema import NodeRelationship, RelatedNodeInfo

# Child -> Parent 관계
child_node.relationships[NodeRelationship.PARENT] = RelatedNodeInfo(
    node_id=parent_node.node_id
)

# Parent -> Children 관계
parent_node.relationships[NodeRelationship.CHILD] = [
    RelatedNodeInfo(node_id=child.node_id) for child in children
]
```

### Index

검색 가능한 데이터 구조입니다.

```python
from llama_index.core import VectorStoreIndex

index = VectorStoreIndex.from_documents([doc1, doc2])
```

### Query Engine

인덱스에 대한 질의를 처리합니다.

```python
query_engine = index.as_query_engine()
response = query_engine.query("What is LlamaIndex?")
```

---

## 4. 인덱스 타입

### 1. VectorStoreIndex

**임베딩 기반 의미 검색**

```python
index = VectorStoreIndex.from_documents(documents)
```

- **언제 사용?**: 의미 기반 검색, 유사 문서 찾기
- **장점**: 정확한 의미 매칭
- **단점**: 임베딩 생성 비용

### 2. SummaryIndex

**모든 노드를 순회하며 요약 생성**

```python
index = SummaryIndex.from_documents(documents)
```

- **언제 사용?**: 전체 문서 요약, 개요 파악
- **장점**: 모든 정보 활용
- **단점**: 느림, 비용 높음

### 3. TreeIndex

**트리 구조로 계층적 요약**

```python
index = TreeIndex.from_documents(documents)
```

- **언제 사용?**: 계층적 요약, Top-down 검색
- **장점**: 효율적인 요약
- **단점**: 구조 생성 복잡

### 4. KeywordTableIndex

**키워드 기반 검색**

```python
index = KeywordTableIndex.from_documents(documents)
```

- **언제 사용?**: 정확한 키워드 매칭
- **장점**: 빠름, 정확한 단어 매칭
- **단점**: 의미 검색 불가

---

## 5. 실습 예제

### 예제 1: 기본 벡터 인덱싱

```python
from llama_index.core import Document, VectorStoreIndex, Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

# 설정
Settings.llm = OpenAI(model="gpt-4o-mini")
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")

# 문서 생성
doc = Document(text="LlamaIndex is a data framework for LLM applications.")

# 인덱스 생성
index = VectorStoreIndex.from_documents([doc])

# 쿼리
query_engine = index.as_query_engine()
response = query_engine.query("What is LlamaIndex?")
print(response)
```

### 예제 2: 계층적 노드 파싱

```python
from llama_index.core.node_parser import HierarchicalNodeParser

# 계층적 파서 (3 레벨)
node_parser = HierarchicalNodeParser.from_defaults(
    chunk_sizes=[2048, 512, 128]  # 큰 청크 -> 중간 -> 작은 청크
)

# 노드 파싱
nodes = node_parser.get_nodes_from_documents([long_document])
leaf_nodes = node_parser.get_leaf_nodes(nodes)

# Leaf 노드로 인덱스 생성
index = VectorStoreIndex(leaf_nodes)
```

**계층 구조:**

```
Level 1: 2048자 청크 (섹션 레벨)
  └─ Level 2: 512자 청크 (단락 레벨)
      └─ Level 3: 128자 청크 (문장 레벨)
```

### 예제 3: JSON 문서 인덱싱

```python
import json
from llama_index.core.schema import TextNode

# JSON 데이터
json_data = {
    "product": {
        "name": "Laptop",
        "specs": {
            "cpu": "Intel i7",
            "ram": "16GB"
        }
    }
}

# 평탄화 함수
def flatten_json(data, prefix=""):
    texts = []
    if isinstance(data, dict):
        for key, value in data.items():
            new_prefix = f"{prefix}.{key}" if prefix else key
            if isinstance(value, (dict, list)):
                texts.extend(flatten_json(value, new_prefix))
            else:
                texts.append(f"{new_prefix}: {value}")
    elif isinstance(data, list):
        for i, item in enumerate(data):
            texts.extend(flatten_json(item, f"{prefix}[{i}]"))
    return texts

# 노드 생성
text_lines = flatten_json(json_data)
nodes = [TextNode(text=line) for line in text_lines]

# 인덱스
index = VectorStoreIndex(nodes)
```

**결과:**

```
product.name: Laptop
product.specs.cpu: Intel i7
product.specs.ram: 16GB
```

### 예제 4: 테이블 데이터 인덱싱

```python
import pandas as pd
from llama_index.core.schema import TextNode

# CSV 로드
df = pd.read_csv("employees.csv")

# 각 행을 노드로
row_nodes = []
for idx, row in df.iterrows():
    text = " | ".join([f"{col}: {row[col]}" for col in df.columns])
    node = TextNode(text=text, metadata={"row": idx})
    row_nodes.append(node)

# 열 통계 노드
column_nodes = []
for col in df.columns:
    if df[col].dtype in ['int64', 'float64']:
        stats = df[col].describe()
        text = f"{col}: mean={stats['mean']}, min={stats['min']}, max={stats['max']}"
    else:
        text = f"{col}: {', '.join(df[col].unique())}"
    column_nodes.append(TextNode(text=text, metadata={"column": col}))

# 인덱스 생성
all_nodes = row_nodes + column_nodes
index = VectorStoreIndex(all_nodes)
```

### 예제 5: Router Query Engine

```python
from llama_index.core.query_engine import RouterQueryEngine
from llama_index.core.selectors import LLMSingleSelector
from llama_index.core.tools import QueryEngineTool, ToolMetadata

# 여러 인덱스 생성
vector_index = VectorStoreIndex.from_documents(docs)
summary_index = SummaryIndex.from_documents(docs)
keyword_index = KeywordTableIndex.from_documents(docs)

# Tools 정의
vector_tool = QueryEngineTool(
    query_engine=vector_index.as_query_engine(),
    metadata=ToolMetadata(
        name="vector_search",
        description="Use for semantic search"
    )
)

summary_tool = QueryEngineTool(
    query_engine=summary_index.as_query_engine(),
    metadata=ToolMetadata(
        name="summary",
        description="Use for summaries"
    )
)

keyword_tool = QueryEngineTool(
    query_engine=keyword_index.as_query_engine(),
    metadata=ToolMetadata(
        name="keyword",
        description="Use for keyword search"
    )
)

# Router 생성
router = RouterQueryEngine(
    selector=LLMSingleSelector.from_defaults(),
    query_engine_tools=[vector_tool, summary_tool, keyword_tool]
)

# 자동 선택
response = router.query("What is the main topic?")  # → summary_tool
response = router.query("Find documents about AI")  # → vector_tool
```

### 예제 6: 커스텀 Parent-Child 노드

```python
from llama_index.core.schema import NodeRelationship, RelatedNodeInfo
from llama_index.core.node_parser import SentenceSplitter

# Parent 노드
parent_node = TextNode(
    text="This is a long section of text...",
    metadata={"type": "parent"}
)

# Child 노드 생성
splitter = SentenceSplitter(chunk_size=200)
child_texts = splitter.split_text(parent_node.text)

child_nodes = []
for i, text in enumerate(child_texts):
    child = TextNode(
        text=text,
        metadata={"type": "child", "chunk": i}
    )

    # 관계 설정
    child.relationships[NodeRelationship.PARENT] = RelatedNodeInfo(
        node_id=parent_node.node_id
    )
    child_nodes.append(child)

# Parent에 Children 연결
parent_node.relationships[NodeRelationship.CHILD] = [
    RelatedNodeInfo(node_id=child.node_id) for child in child_nodes
]

# Child만으로 인덱스 (검색은 작은 청크로, 컨텍스트는 부모에서)
index = VectorStoreIndex(child_nodes)
```

### 예제 7: Recursive Retriever

```python
from llama_index.core.retrievers import RecursiveRetriever
from llama_index.core.query_engine import RetrieverQueryEngine

# 계층적 인덱스 (예제 2의 결과 사용)
# nodes: 모든 노드, leaf_nodes: 리프 노드만

# node_id -> node 매핑
node_dict = {node.node_id: node for node in nodes}

# Recursive Retriever
retriever = RecursiveRetriever(
    "vector",
    retriever_dict={"vector": index.as_retriever()},
    node_dict=node_dict
)

# Query Engine
query_engine = RetrieverQueryEngine.from_args(retriever)

# 쿼리 (작은 청크로 검색 → 부모 컨텍스트 자동 로드)
response = query_engine.query("What is machine learning?")
```

---

## 6. FastAPI 엔드포인트

### 서버 시작

```bash
poetry install
poetry run start
```

Swagger UI: http://localhost:8001/docs

### 엔드포인트 목록

| 엔드포인트 | 설명 |
|----------|------|
| `POST /llamaindex/basic-vector-index` | 기본 벡터 인덱스 생성 |
| `POST /llamaindex/query-vector-index` | 벡터 인덱스 쿼리 |
| `POST /llamaindex/hierarchical-index` | 계층적 인덱스 생성 |
| `POST /llamaindex/json-index` | JSON 문서 인덱싱 |
| `POST /llamaindex/table-index` | 테이블 데이터 인덱싱 |
| `POST /llamaindex/multi-index` | 다중 인덱스 + Router |
| `POST /llamaindex/query-router` | Router로 쿼리 |
| `POST /llamaindex/recursive-retriever` | 재귀적 검색 |
| `POST /llamaindex/custom-nodes` | 커스텀 노드 생성 |
| `GET /llamaindex/list-indices` | 인덱스 목록 |
| `DELETE /llamaindex/delete-index/{id}` | 인덱스 삭제 |

### 사용 예시

#### 1. 기본 벡터 인덱스 생성

```bash
curl -X POST "http://localhost:8001/llamaindex/basic-vector-index" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "LlamaIndex is a data framework for LLM applications.",
    "doc_id": "doc1"
  }'
```

#### 2. 쿼리 실행

```bash
curl -X POST "http://localhost:8001/llamaindex/query-vector-index" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is LlamaIndex?",
    "index_id": "vector_doc1"
  }'
```

---

## 7. 고급 패턴

### 패턴 1: 메타데이터 필터링

```python
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter

# 특정 카테고리만 검색
filtered_query_engine = index.as_query_engine(
    filters=MetadataFilters(
        filters=[ExactMatchFilter(key="category", value="ai")]
    )
)

response = filtered_query_engine.query("Tell me about AI")
```

### 패턴 2: 하이브리드 검색

```python
from llama_index.core.retrievers import VectorIndexRetriever, KeywordTableRetriever
from llama_index.core.retrievers import QueryFusionRetriever

# 벡터 + 키워드 결합
vector_retriever = VectorIndexRetriever(index=vector_index)
keyword_retriever = KeywordTableRetriever(index=keyword_index)

fusion_retriever = QueryFusionRetriever(
    [vector_retriever, keyword_retriever],
    similarity_top_k=5
)

response = fusion_retriever.retrieve("AI and machine learning")
```

### 패턴 3: Re-ranking

```python
from llama_index.core.postprocessor import SimilarityPostprocessor

# 유사도 기준으로 재정렬
postprocessor = SimilarityPostprocessor(similarity_cutoff=0.7)

query_engine = index.as_query_engine(
    node_postprocessors=[postprocessor]
)
```

### 패턴 4: 스트리밍 응답

```python
# 스트리밍 쿼리
streaming_response = query_engine.query("Explain AI")

for text in streaming_response.response_gen:
    print(text, end="")
```

---

## 8. 성능 최적화

### 1. 청크 크기 최적화

```python
# 작은 청크: 정확하지만 느림
Settings.chunk_size = 256

# 큰 청크: 빠르지만 덜 정확
Settings.chunk_size = 1024

# 추천: 512 (균형)
Settings.chunk_size = 512
```

### 2. Top-K 조정

```python
# 더 많은 결과 (정확하지만 느림)
query_engine = index.as_query_engine(similarity_top_k=10)

# 적은 결과 (빠르지만 덜 정확)
query_engine = index.as_query_engine(similarity_top_k=3)
```

### 3. 캐싱

```python
from llama_index.core.storage.storage_context import StorageContext

# 인덱스 저장
storage_context = StorageContext.from_defaults()
index.storage_context = storage_context
index.storage_context.persist(persist_dir="./storage")

# 인덱스 로드
from llama_index.core import load_index_from_storage

storage_context = StorageContext.from_defaults(persist_dir="./storage")
index = load_index_from_storage(storage_context)
```

### 4. 배치 처리

```python
# 여러 문서 한 번에 인덱싱
documents = [doc1, doc2, doc3, ...]  # 100개
index = VectorStoreIndex.from_documents(documents)  # 한 번에
```

---

## 9. 문제 해결

### 문제 1: 임베딩 API 비용이 너무 높음

**해결책:**

```python
# 1. 로컬 임베딩 모델 사용
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

Settings.embed_model = HuggingFaceEmbedding(
    model_name="BAAI/bge-small-en-v1.5"
)

# 2. 청크 크기 증가
Settings.chunk_size = 1024

# 3. 캐싱 활용
```

### 문제 2: 검색 결과가 부정확함

**해결책:**

```python
# 1. 청크 크기 감소
Settings.chunk_size = 256

# 2. Top-K 증가
query_engine = index.as_query_engine(similarity_top_k=10)

# 3. Re-ranking 추가
from llama_index.core.postprocessor import SimilarityPostprocessor
postprocessor = SimilarityPostprocessor(similarity_cutoff=0.75)
query_engine = index.as_query_engine(node_postprocessors=[postprocessor])
```

### 문제 3: 메모리 부족

**해결책:**

```python
# 1. 스트리밍 처리
for doc in large_doc_iterator:
    nodes = parser.get_nodes_from_documents([doc])
    index.insert_nodes(nodes)

# 2. 배치 크기 제한
batch_size = 100
for i in range(0, len(docs), batch_size):
    batch = docs[i:i+batch_size]
    # 처리
```

### 문제 4: 쿼리가 너무 느림

**해결책:**

```python
# 1. 인덱스 타입 변경 (Vector → Keyword)
keyword_index = KeywordTableIndex.from_documents(docs)

# 2. 캐싱
# (위의 캐싱 섹션 참조)

# 3. 비동기 쿼리
response = await query_engine.aquery("question")
```

---

## 🎯 학습 로드맵

### 초급 (1주)
1. ✅ 기본 벡터 인덱스 생성 및 쿼리
2. ✅ 메타데이터 활용
3. ✅ 간단한 JSON/CSV 인덱싱

### 중급 (2주)
4. ✅ 계층적 노드 파싱
5. ✅ Router Query Engine
6. ✅ 커스텀 노드 관계

### 고급 (3주)
7. ✅ Recursive Retriever
8. ✅ 하이브리드 검색
9. ✅ 성능 최적화
10. ✅ 프로덕션 배포

---

## 📖 추가 학습 자료

- [LlamaIndex 공식 문서](https://docs.llamaindex.ai/)
- [LlamaIndex GitHub](https://github.com/run-llama/llama_index)
- [LlamaIndex Discord](https://discord.gg/dGcwcsnxhU)

---

## 🔧 유용한 도구

### 1. LlamaHub

다양한 데이터 로더 모음

```python
from llama_index.core import download_loader

PDFReader = download_loader("PDFReader")
docs = PDFReader().load_data("document.pdf")
```

### 2. LlamaIndex CLI

```bash
# 인덱스 생성
llamaindex-cli create-index --data-dir ./data

# 쿼리
llamaindex-cli query "What is AI?"
```

### 3. Observability

```python
import llama_index.core
llama_index.core.set_global_handler("simple")

# 디버그 정보 자동 출력
```

---

**작성일**: 2024-01-14
**버전**: 1.0
**문의**: hyunbae.jeon@example.com
