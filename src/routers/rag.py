from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

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

from src.utils.response_wrapper import api_response
from src.main import chain
from src.main import get_vector_store


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
    try:
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

        # for element in html_header_splits_elements[:3]:
        #     print('html_header_splits_elements ::::::::::::::::::::::::::: ', element)

        chunk_size = 500
        chunk_overlap = 30
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        splits = text_splitter.split_documents(html_header_splits)
        # splits[80:85]


        if len(splits) > 0:
            embeddings = get_embeddings_model()
            vectorstore = FAISS.from_documents(documents=splits, embedding=embeddings)
            return {
                "message": "URL processed successfully",
                "document_count": len(splits),
                "vectorstore_size": vectorstore.index.ntotal
            }
        else:
            return {"message": "URL processing failed - no documents extracted"}

    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Error in process_url: {error_trace}")
        raise HTTPException(status_code=500, detail=str(e))

class State(TypedDict):
    question: str
    context: List[Document]
    answer: str

@router.post("/web-retrieve")
async def process_url(url_input: URLInput):
    state: State = State()
    try:
        loader = WebBaseLoader(
            # "https://lilianweng.github.io/posts/2023-06-23-agent/"
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

        return api_response(data=retrieved_docs, message="web documents retrieved")

    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Error in process_url: {error_trace}")
        raise HTTPException(status_code=500, detail=str(e))