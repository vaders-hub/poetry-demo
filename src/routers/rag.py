import faiss
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import bs4
import traceback

from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain import hub
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

from src.main import chain

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
        loader = WebBaseLoader(
            web_paths=(url_input.url,),
            bs_kwargs=dict(
                parse_only=bs4.SoupStrainer(
                    # url의 클래스
                    class_=("newsct_article _article_body",)
                )
            ),
        )

        docs = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000000, chunk_overlap=20000
        )
        splits = text_splitter.split_documents(docs)
        print('vectorstore ::::::::::::::::::::::::::::::::::::::::: ', docs)

        if len(splits) > 0:
            # 스플릿 된 문서들을 벡터 스토어에 임베딩 해서 저장
            vectorstore = FAISS.from_documents(documents=splits, embedding=embeddings_model)

            # 벡터 임베딩의 추출기
            retriever = vectorstore.as_retriever()

            prompt = hub.pull("rlm/rag-prompt")

            # 다큐먼트 객체들이 갖고 있는 페이지 컨텐츠들이 하나의 텍스트로 붙는다.
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
            print('rag_chain', rag_chain)
        return {"message": "URL processed successfully"}

    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Error in process_url: {error_trace}")
        raise HTTPException(status_code=500, detail=str(e))