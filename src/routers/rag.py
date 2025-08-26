from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import bs4
import traceback

from langchain import hub
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import HTMLHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain import hub
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document

from typing_extensions import List, TypedDict

from src.main import chain
from src.main import vector_store

class Query(BaseModel):
    prompt: str
    min_length: int = 3
    max_tokens: int = 50

class URLInput(BaseModel):
    url: str

router = APIRouter(prefix="/rag", tags=["rag"])
embeddings_model = HuggingFaceEmbeddings(
    model_name='jhgan/ko-sroberta-nli',
    model_kwargs={'device':'cpu'},
    encode_kwargs={'normalize_embeddings':True},
)

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
            vectorstore = FAISS.from_documents(documents=splits, embedding=embeddings_model)
            retriever = vectorstore.as_retriever()
            prompt = hub.pull("rlm/rag-prompt")

            def format_docs(docs):
                return "\n\n".join(doc.page_content for doc in docs)

            rag_chain = (
                {
                    "context": retriever | format_docs,
                    "question": RunnablePassthrough(),
                }
                | prompt
                | chain
                | StrOutputParser()
            )
            return {"message": "URL processed successfully"}
        else:
            return {"message": "URL processed failed"}

    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Error in process_url: {error_trace}")
        raise HTTPException(status_code=500, detail=str(e))

class State(TypedDict):
    question: str
    context: List[Document]
    answer: str

@router.post("/web-retrieve")
async def process_url(state: State):
    try:
        loader = WebBaseLoader(
            web_paths=("https://lilianweng.github.io/posts/2023-06-23-agent/",),
            bs_kwargs=dict(
                parse_only=bs4.SoupStrainer(
                    class_=("post-content", "post-title", "post-header")
                )
            ),
        )
        docs = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        all_splits = text_splitter.split_documents(docs)

        _ = vector_store.add_documents(documents=all_splits)

        prompt = hub.pull("rlm/rag-prompt")

        retrieved_docs = vector_store.similarity_search(state["question"])
        return {"context": retrieved_docs}

    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Error in process_url: {error_trace}")
        raise HTTPException(status_code=500, detail=str(e))