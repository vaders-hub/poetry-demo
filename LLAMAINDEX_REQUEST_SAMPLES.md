# LlamaIndex API Request Samples

LlamaIndex 엔드포인트 테스트를 위한 샘플 Request Body 모음입니다.
Swagger UI(http://localhost:8001/docs)에서 바로 복사하여 사용할 수 있습니다.

---

## 📋 목차

1. [기본 벡터 인덱스](#1-기본-벡터-인덱스)
2. [벡터 인덱스 쿼리](#2-벡터-인덱스-쿼리)
3. [계층적 인덱스](#3-계층적-인덱스)
4. [JSON 문서 인덱싱](#4-json-문서-인덱싱)
5. [테이블 데이터 인덱싱](#5-테이블-데이터-인덱싱)
6. [다중 인덱스 Router](#6-다중-인덱스-router)
7. [Router 쿼리](#7-router-쿼리)
8. [재귀적 검색](#8-재귀적-검색)
9. [커스텀 노드](#9-커스텀-노드)
10. [인덱스 관리](#10-인덱스-관리)

---

## 1. 기본 벡터 인덱스

### Endpoint: `POST /llamaindex/basic-vector-index`

#### 샘플 1: 짧은 문서

```json
{
  "text": "LlamaIndex is a data framework for LLM applications to ingest, structure, and access private or domain-specific data.",
  "doc_id": "intro_doc"
}
```

#### 샘플 2: 기술 문서

```json
{
  "text": "FastAPI is a modern, fast web framework for building APIs with Python 3.7+. It is based on standard Python type hints and provides automatic API documentation, data validation, and async support.",
  "doc_id": "fastapi_doc"
}
```

#### 샘플 3: 긴 문서

```json
{
  "text": "Machine learning is a subset of artificial intelligence that focuses on building systems that learn from data. The field encompasses supervised learning (classification, regression), unsupervised learning (clustering, dimensionality reduction), and reinforcement learning. Deep learning, a subset of machine learning, uses neural networks with multiple layers to model complex patterns. Popular frameworks include TensorFlow, PyTorch, and scikit-learn.",
  "doc_id": "ml_overview"
}
```

---

## 2. 벡터 인덱스 쿼리

### Endpoint: `POST /llamaindex/query-vector-index`

#### 샘플 1: 기본 질문

```json
{
  "query": "What is LlamaIndex?",
  "index_id": "vector_intro_doc"
}
```

#### 샘플 2: 구체적 질문

```json
{
  "query": "What are the key features of FastAPI?",
  "index_id": "vector_fastapi_doc"
}
```

#### 샘플 3: 비교 질문

```json
{
  "query": "What is the difference between supervised and unsupervised learning?",
  "index_id": "vector_ml_overview"
}
```

---

## 3. 계층적 인덱스

### Endpoint: `POST /llamaindex/hierarchical-index`

#### 샘플 1: 기술 문서 섹션

```json
{
  "sections": [
    {
      "title": "Introduction",
      "text": "LlamaIndex is a powerful data framework designed specifically for Large Language Model (LLM) applications. It provides comprehensive tools for data ingestion, indexing, and retrieval. The framework supports various data sources including documents, databases, and APIs. With LlamaIndex, developers can build sophisticated RAG (Retrieval Augmented Generation) systems that combine the power of LLMs with private or domain-specific data.",
      "level": 1
    },
    {
      "title": "Core Features",
      "text": "The core features of LlamaIndex include data connectors for over 100 data sources, flexible indexing strategies including vector stores and hierarchical indices, advanced query engines with support for semantic search, and composable architecture that allows mixing and matching different components. The framework also provides built-in observability, caching mechanisms, and optimization tools for production deployments.",
      "level": 1
    },
    {
      "title": "Use Cases",
      "text": "Common use cases for LlamaIndex include building chatbots over private documents, creating question-answering systems for enterprise knowledge bases, developing semantic search engines, implementing document summarization pipelines, and constructing multi-modal search systems. The framework is particularly useful in domains like legal tech, healthcare, finance, and customer support where access to specialized knowledge is crucial.",
      "level": 1
    }
  ],
  "doc_id": "llamaindex_guide"
}
```

#### 샘플 2: 제품 매뉴얼

```json
{
  "sections": [
    {
      "title": "Getting Started",
      "text": "To get started with our product, first install the required dependencies using pip install. Then configure your API keys in the environment variables. Create a new project using our CLI tool and initialize the configuration file. The setup process typically takes 5-10 minutes for first-time users.",
      "level": 1
    },
    {
      "title": "Configuration",
      "text": "Configuration options include model selection (choose from GPT-4, GPT-3.5, or custom models), embedding model settings (OpenAI or local models), chunk size and overlap parameters (recommended: 512 with 50 overlap), and retrieval settings such as top-k values and similarity thresholds.",
      "level": 1
    },
    {
      "title": "Advanced Usage",
      "text": "Advanced features include custom node parsers for specialized document structures, hybrid search combining vector and keyword approaches, re-ranking with cross-encoders for improved accuracy, and streaming responses for real-time user feedback. Enterprise users can also leverage distributed indexing and GPU acceleration.",
      "level": 1
    }
  ],
  "doc_id": "product_manual"
}
```

---

## 4. JSON 문서 인덱싱

### Endpoint: `POST /llamaindex/json-index`

#### 샘플 1: 제품 정보

```json
{
  "json_data": {
    "product": {
      "id": "PROD-001",
      "name": "Wireless Noise-Cancelling Headphones",
      "category": "Electronics",
      "brand": "TechAudio",
      "specs": {
        "battery_life": "30 hours",
        "connectivity": "Bluetooth 5.0",
        "noise_cancellation": true,
        "weight": "250g",
        "drivers": "40mm"
      },
      "price": {
        "amount": 299.99,
        "currency": "USD"
      },
      "reviews": [
        {
          "rating": 5,
          "comment": "Excellent sound quality and comfort!",
          "date": "2024-01-10"
        },
        {
          "rating": 4,
          "comment": "Great product but a bit pricey",
          "date": "2024-01-12"
        }
      ]
    }
  },
  "doc_id": "product_headphones"
}
```

#### 샘플 2: 사용자 프로필

```json
{
  "json_data": {
    "user": {
      "id": "USR-456",
      "name": "Jane Smith",
      "email": "jane.smith@example.com",
      "profile": {
        "age": 28,
        "location": "San Francisco, CA",
        "occupation": "Software Engineer",
        "interests": ["AI", "Machine Learning", "Web Development"]
      },
      "settings": {
        "notifications": true,
        "theme": "dark",
        "language": "en"
      },
      "activity": {
        "last_login": "2024-01-14T10:30:00Z",
        "total_queries": 1523,
        "favorite_topics": ["Python", "FastAPI", "LlamaIndex"]
      }
    }
  },
  "doc_id": "user_jane"
}
```

#### 샘플 3: API 응답 데이터

```json
{
  "json_data": {
    "api_response": {
      "status": "success",
      "data": {
        "employees": [
          {
            "id": 1,
            "name": "John Doe",
            "department": "Engineering",
            "position": "Senior Developer",
            "skills": ["Python", "JavaScript", "Docker"]
          },
          {
            "id": 2,
            "name": "Alice Brown",
            "department": "Data Science",
            "position": "ML Engineer",
            "skills": ["Python", "TensorFlow", "SQL"]
          }
        ],
        "metadata": {
          "total_count": 2,
          "page": 1,
          "timestamp": "2024-01-14T15:00:00Z"
        }
      }
    }
  },
  "doc_id": "api_employees"
}
```

---

## 5. 테이블 데이터 인덱싱

### Endpoint: `POST /llamaindex/table-index`

#### 샘플 1: 직원 데이터

```json
{
  "csv_data": "name,age,city,department,salary\nJohn Smith,35,New York,Engineering,95000\nJane Doe,28,San Francisco,Design,85000\nBob Johnson,42,Seattle,Management,110000\nAlice Williams,31,Boston,Data Science,92000\nCharlie Brown,29,Austin,Marketing,78000",
  "doc_id": "employees_table"
}
```

#### 샘플 2: 제품 재고

```json
{
  "csv_data": "product_id,product_name,category,quantity,price,supplier\nP001,Laptop,Electronics,45,1299.99,TechCorp\nP002,Mouse,Accessories,150,29.99,PeriphCo\nP003,Keyboard,Accessories,89,79.99,PeriphCo\nP004,Monitor,Electronics,32,399.99,ScreenPro\nP005,USB Cable,Accessories,200,9.99,CableTech",
  "doc_id": "inventory_table"
}
```

#### 샘플 3: 판매 데이터

```json
{
  "csv_data": "date,product,quantity,revenue,region\n2024-01-01,Widget A,120,12000,North\n2024-01-01,Widget B,85,8500,South\n2024-01-02,Widget A,95,9500,East\n2024-01-02,Widget C,150,22500,West\n2024-01-03,Widget B,110,11000,North",
  "doc_id": "sales_table"
}
```

---

## 6. 다중 인덱스 Router

### Endpoint: `POST /llamaindex/multi-index`

#### 샘플 1: 혼합 문서 세트

```json
{
  "documents": [
    {
      "id": "tech_1",
      "text": "LlamaIndex provides powerful data connectors that can ingest data from various sources including APIs, databases, PDFs, and web pages. The framework automatically handles parsing and chunking.",
      "category": "technical"
    },
    {
      "id": "business_1",
      "text": "Our company was founded in 2020 and has grown to 150 employees across 5 offices worldwide. We serve over 1000 enterprise clients in the tech industry.",
      "category": "business"
    },
    {
      "id": "feature_1",
      "text": "Key features include hierarchical indexing, metadata filtering, recursive retrieval, hybrid search, and streaming responses. All features are production-ready and battle-tested.",
      "category": "features"
    }
  ],
  "index_id": "multi_idx_1"
}
```

#### 샘플 2: 제품 문서

```json
{
  "documents": [
    {
      "id": "overview",
      "text": "Our AI-powered analytics platform helps businesses make data-driven decisions. The platform integrates with all major data sources and provides real-time insights.",
      "category": "overview"
    },
    {
      "id": "pricing",
      "text": "Pricing tiers include Starter ($49/month for up to 10 users), Professional ($199/month for up to 50 users), and Enterprise (custom pricing for unlimited users).",
      "category": "pricing"
    },
    {
      "id": "technical",
      "text": "Built on a microservices architecture using Python, FastAPI, and PostgreSQL. Deployed on AWS with automatic scaling and 99.9% uptime SLA. RESTful APIs with OpenAPI documentation.",
      "category": "technical"
    },
    {
      "id": "support",
      "text": "24/7 customer support via email and chat. Premium customers get dedicated account managers and phone support. Average response time under 2 hours.",
      "category": "support"
    }
  ],
  "index_id": "product_docs"
}
```

---

## 7. Router 쿼리

### Endpoint: `POST /llamaindex/query-router`

#### 샘플 1: 의미 검색 쿼리

```json
{
  "query": "How does the data ingestion process work?",
  "index_id": "multi_idx_1"
}
```

#### 샘플 2: 요약 쿼리

```json
{
  "query": "Give me an overview of the entire product",
  "index_id": "product_docs"
}
```

#### 샘플 3: 키워드 쿼리

```json
{
  "query": "pricing tiers Enterprise",
  "index_id": "product_docs"
}
```

---

## 8. 재귀적 검색

### Endpoint: `POST /llamaindex/recursive-retriever`

#### 샘플 1: 기본 질문

```json
{
  "query": "What are the main features of hierarchical indexing?",
  "index_id": "hierarchical_llamaindex_guide"
}
```

#### 샘플 2: 상세 질문

```json
{
  "query": "Explain the configuration options in detail",
  "index_id": "hierarchical_product_manual"
}
```

---

## 9. 커스텀 노드

### Endpoint: `POST /llamaindex/custom-nodes`

#### 샘플 1: 블로그 포스트

```json
{
  "sections": [
    {
      "title": "Introduction to RAG",
      "text": "Retrieval Augmented Generation (RAG) is a technique that enhances Large Language Models by providing them with relevant context from external knowledge sources. Unlike traditional LLMs that rely solely on their training data, RAG systems can access up-to-date information and domain-specific knowledge. This approach significantly improves accuracy and reduces hallucinations. RAG has become essential for enterprise AI applications where accuracy and factual correctness are critical.",
      "level": 1
    },
    {
      "title": "How RAG Works",
      "text": "The RAG process involves three main steps: retrieval, augmentation, and generation. First, when a user asks a question, the system searches a knowledge base (usually a vector database) to find relevant documents or passages. Second, these retrieved documents are combined with the user's question to create an augmented prompt. Finally, the LLM generates a response based on both the question and the retrieved context. This process ensures that responses are grounded in factual information rather than generated from the model's parametric memory alone.",
      "level": 1
    },
    {
      "title": "Benefits and Challenges",
      "text": "RAG offers several key benefits including improved accuracy through grounding in factual sources, ability to cite sources for transparency, easy updates to knowledge without retraining models, and reduced computational costs compared to fine-tuning. However, challenges include ensuring retrieval quality (garbage in, garbage out), managing latency from multiple API calls, handling contradictory information in retrieved documents, and determining optimal chunk sizes for different use cases.",
      "level": 1
    }
  ],
  "doc_id": "rag_blog_post"
}
```

#### 샘플 2: 튜토리얼

```json
{
  "sections": [
    {
      "title": "Step 1: Installation",
      "text": "Begin by installing the required packages using pip. You'll need llama-index, openai, and faiss-cpu. Create a virtual environment first to avoid dependency conflicts. Run 'pip install llama-index llama-index-llms-openai llama-index-embeddings-openai'. This will install the core framework and OpenAI integrations. Installation typically takes 2-3 minutes depending on your internet connection.",
      "level": 1
    },
    {
      "title": "Step 2: Setup",
      "text": "Configure your OpenAI API key by setting the OPENAI_API_KEY environment variable. Import the necessary modules from llama_index.core including Document, VectorStoreIndex, and Settings. Set global configurations such as the LLM model (gpt-4o-mini recommended for cost-effectiveness), embedding model (text-embedding-3-small), chunk size (512 is a good default), and chunk overlap (50 tokens). These settings will apply to all indices you create.",
      "level": 1
    },
    {
      "title": "Step 3: Create Index",
      "text": "Load your documents using Document objects with text and metadata. Create a VectorStoreIndex by calling VectorStoreIndex.from_documents() and passing your document list. The framework will automatically chunk the documents, generate embeddings, and build the vector index. For large document sets, this may take several minutes. Monitor the progress and check for any errors. Once complete, you can persist the index to disk for future use.",
      "level": 1
    },
    {
      "title": "Step 4: Query",
      "text": "Create a query engine from your index using index.as_query_engine(). You can customize the query engine with parameters like similarity_top_k (number of similar chunks to retrieve), response_mode (compact, tree_summarize, etc.), and streaming (enable real-time responses). Execute queries by calling query_engine.query() with your question string. The engine will retrieve relevant chunks, send them to the LLM with your question, and return a comprehensive answer. Examine the source_nodes in the response to see which chunks were used.",
      "level": 1
    }
  ],
  "doc_id": "tutorial_quickstart"
}
```

---

## 10. 인덱스 관리

### Endpoint: `GET /llamaindex/list-indices`

No request body needed. Just send a GET request.

### Endpoint: `DELETE /llamaindex/delete-index/{index_id}`

No request body needed. Specify the index_id in the URL path.

**예시:**
```
DELETE /llamaindex/delete-index/vector_intro_doc
```

---

## 💡 사용 팁

### 1. 인덱스 ID 패턴

- `vector_{doc_id}`: 기본 벡터 인덱스
- `hierarchical_{doc_id}`: 계층적 인덱스
- `json_{doc_id}`: JSON 인덱스
- `table_{doc_id}`: 테이블 인덱스
- `custom_{doc_id}`: 커스텀 노드 인덱스
- 임의 ID: 다중 인덱스

### 2. 최적의 청크 크기

- **짧은 문서 (< 1000자)**: 전체를 하나의 인덱스로
- **중간 문서 (1000-10000자)**: chunk_size=512
- **긴 문서 (> 10000자)**: 계층적 인덱싱 사용

### 3. 쿼리 전략

- **간단한 팩트 검색**: 벡터 검색
- **전체 요약**: Summary Index + Router
- **정확한 키워드**: Keyword Index + Router
- **복잡한 질문**: Hierarchical + Recursive Retriever

### 4. 테스트 순서

1. `basic-vector-index` → `query-vector-index` (기본 흐름 익히기)
2. `hierarchical-index` → `recursive-retriever` (계층 구조 이해)
3. `json-index` / `table-index` (구조화된 데이터)
4. `multi-index` → `query-router` (자동 선택)
5. `custom-nodes` (고급 커스터마이징)

---

## 🔗 관련 문서

- [LlamaIndex 완벽 가이드](./LLAMAINDEX_GUIDE.md)
- [독립 실행 예제](./src/examples/llamaindex_patterns.py)
- [API 문서](http://localhost:8001/docs)

---

**작성일**: 2024-01-14
**버전**: 1.0
