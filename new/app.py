# embed_documents.py
from langchain_core.documents import Document
from langchain_milvus import Milvus
from langchain_community.embeddings import LlamaCppEmbeddings  # of andere embeddings

import json

# Lees JSON
with open("lion.json") as f:
    doc = json.load(f)

documents = [
    Document(
        page_content=doc["text"],
        metadata={"id": doc["id"], "file_name": doc.get("file-name", "")}
    )
]

# Embed model
embeddings = LlamaCppEmbeddings(model_path="nomic-embed-text-v2-moe.f32.gguf")

# Milvus URI
URI = "http://localhost:19530"

# Vector store opslaan
vectorstore = Milvus.from_documents(
    documents,
    embedding=embeddings,
    collection_name="documents",
    connection_args={"uri": URI},
    index_params={"index_type": "FLAT", "metric_type": "L2"},
    drop_old=False  # verwijder oude collectie, handig bij testen
)

print("Opslaan gelukt!")


