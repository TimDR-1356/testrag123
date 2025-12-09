
from langchain_milvus import Milvus
from langchain_community.embeddings import LlamaCppEmbeddings
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List

app = FastAPI(title="Simple FastAPI Example", description="Een eenvoudige FastAPI met Swagger", version="1.0.0")


# --- Setup Milvus vector store ---
embeddings = LlamaCppEmbeddings(model_path="nomic-embed-text-v2-moe.f32.gguf")
URI = "http://localhost:19530"

vectorstore = Milvus(
    embedding_function=embeddings,
    collection_name="documents",
    connection_args={"uri": URI},
    index_params={"index_type": "FLAT", "metric_type": "L2"},
)

# --- Pydantic model voor de request ---
class QueryRequest(BaseModel):
    query: str
    k: int = 5  # default aantal documenten


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

# --- Endpoint voor retrieval ---
@app.post("/query")
def query_documents(req: QueryRequest):
    docs = vectorstore.similarity_search(req.query, k=req.k)
    results = [{"page_content": doc.page_content, "metadata": doc.metadata} for doc in docs]
    return {"results": results}

@app.post(
    "/retrieve",
    response_model=RetrievalResponse,
    summary="Retrieve top-k docs for each query",
)
def retrieve_docs(input: RetrievalQueryInput):
    try:
        out = []
        for q in input.queries:
            docs = vectorstore.similarity_search(q, k=input.k)
            results = [doc.page_content for doc in docs]
            out.append(RetrievedDoc(query=q, results=results))
        return RetrievalResponse(responses=out)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
