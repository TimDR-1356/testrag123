import os
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List
from langchain_milvus import Milvus
from langchain_community.embeddings import LlamaCppEmbeddings
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="RAG Retriever API",
    version="1.0.0",
    description="Retrieval-Only API: Queries to vectorstore using LangChain, FAISS, and sentence-transformers.",
)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RetrievalQueryInput(BaseModel):
    queries: List[str] = Field(
        ..., description="List of queries to retrieve from the vectorstore"
    )
    k: int = Field(3, description="Number of results per query", example=3)


class RetrievedDoc(BaseModel):
    query: str
    results: List[str]


class RetrievalResponse(BaseModel):
    responses: List[RetrievedDoc]


# --------- Initialize Retriever (on app startup) --------
URI = "http://localhost:19530"  # Path to your FAISS vector store
EMBEDDING_MODEL_NAME = "nomic-embed-text-v2-moe.f32.gguf"  # Widely used, fast


def get_retriever():
    embeddings = LlamaCppEmbeddings(model_path=EMBEDDING_MODEL_NAME)
    retriever = Milvus(
        embedding_function=embeddings,
        collection_name="documents",
        connection_args={"uri": URI},
        index_params={"index_type": "FLAT", "metric_type": "L2"},
    )
    return retriever


retriever = get_retriever()
# --------------------------------------------------------


@app.post(
    "/retrieve",
    response_model=RetrievalResponse,
    summary="Retrieve top-k docs for each query",
)
def retrieve_docs(input: RetrievalQueryInput):
    """
    Given a list of user queries, returns top-k retrieved documents per query.
    """
    try:
        out = []
        for q in input.queries:
            docs = retriever.similarity_search(q, k=input.k)
            results = [doc.page_content for doc in docs]
            out.append(RetrievedDoc(query=q, results=results))
            print(docs)
        return RetrievalResponse(responses=out)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
