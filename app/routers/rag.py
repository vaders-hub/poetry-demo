from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime

import bs4
import traceback

from langchain import hub
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import HTMLHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document

from typing import List
from typing_extensions import TypedDict

from app.utils import success_response, error_response
from app.main import chain
from app.main import get_vector_store


class URLInput(BaseModel):
    url: str

router = APIRouter(prefix="/rag", tags=["rag"])

# Lazy-loaded embeddings model
_embeddings_model = None

def get_embeddings_model():
    """Get or create HuggingFace embeddings model (lazy initialization)"""
    global _embeddings_model
    if _embeddings_model is None:
        _embeddings_model = HuggingFaceEmbeddings(
            model_name='jhgan/ko-sroberta-nli',
            model_kwargs={'device':'cpu'},
            encode_kwargs={'normalize_embeddings':True},
        )
    return _embeddings_model

@router.post("/load")
async def process_url(url_input: URLInput):
    """URL에서 문서 로드 및 벡터 스토어 생성"""
    try:
        start_time = datetime.now()

        loader = WebBaseLoader(url_input.url)
        docs = loader.load()

        headers_to_split_on = [
            ("h1", "Header 1"),
            ("h2", "Header 2"),
            ("h3", "Header 3"),
        ]
        html_splitter = HTMLHeaderTextSplitter(headers_to_split_on)
        html_header_splits = html_splitter.split_text_from_url(docs[0])
        html_header_splits_elements = html_splitter.split_text(docs[0])

        for element in html_header_splits[:2]:
            print('html_header_splits ::::::::::::::::::::::::::: ', element)

        chunk_size = 500
        chunk_overlap = 30
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        splits = text_splitter.split_documents(html_header_splits)

        end_time = datetime.now()

        if len(splits) > 0:
            embeddings = get_embeddings_model()
            vectorstore = FAISS.from_documents(documents=splits, embedding=embeddings)

            return success_response(
                data={
                    "url": url_input.url,
                    "document_count": len(splits),
                    "vectorstore_size": vectorstore.index.ntotal,
                },
                message="URL이 성공적으로 처리되었습니다.",
                execution_time_ms=(end_time - start_time).total_seconds() * 1000,
            )
        else:
            return error_response(
                message="URL 처리 실패 - 문서를 추출할 수 없습니다.",
                error="NO_DOCUMENTS_EXTRACTED",
                status_code=400,
            )

    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Error in process_url: {error_trace}")
        return error_response(
            message="URL 처리 중 오류가 발생했습니다.",
            error=str(e),
            status_code=500,
        )

class State(TypedDict):
    question: str
    context: List[Document]
    answer: str

@router.post("/web-retrieve")
async def web_retrieve(url_input: URLInput):
    """웹 문서 검색 및 유사도 검색"""
    state: State = State()
    try:
        start_time = datetime.now()

        loader = WebBaseLoader(
            web_paths=(url_input.url,),
            bs_kwargs=dict(
                parse_only=bs4.SoupStrainer(
                    class_=("post-content", "post-title", "post-header")
                )
            ),
        )
        docs = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        all_splits = text_splitter.split_documents(docs)

        vs = get_vector_store()
        _ = vs.add_documents(documents=all_splits)

        retrieved_docs = vs.similarity_search('Class')

        end_time = datetime.now()

        return success_response(
            data={
                "url": url_input.url,
                "documents": [
                    {
                        "page_content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                        "metadata": doc.metadata,
                    }
                    for doc in retrieved_docs
                ],
            },
            message="웹 문서가 검색되었습니다.",
            execution_time_ms=(end_time - start_time).total_seconds() * 1000,
            metadata={
                "total_splits": len(all_splits),
                "retrieved_count": len(retrieved_docs),
            }
        )

    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Error in web_retrieve: {error_trace}")
        return error_response(
            message="웹 문서 검색 중 오류가 발생했습니다.",
            error=str(e),
            status_code=500,
        )