# query_documents.py
from langchain_milvus import Milvus
from langchain_community.embeddings import LlamaCppEmbeddings

# Embed model
embeddings = LlamaCppEmbeddings(model_path="nomic-embed-text-v2-moe.f32.gguf")

# Milvus URI
URI = "http://localhost:19530"

# Vector store laden
vectorstore = Milvus(
    embedding_function=embeddings,
    collection_name="documents",
    connection_args={"uri": URI},
    index_params={"index_type": "FLAT", "metric_type": "L2"},
)

# Query
query = "Leg uit hoe Milvus werkt"
docs = vectorstore.similarity_search(query, k=5)

for doc in docs:
    print(f"---\n{doc.page_content}\n")
