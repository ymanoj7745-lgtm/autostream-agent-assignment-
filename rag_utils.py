from pathlib import Path

import numpy as np
from google import genai
from langchain_text_splitters import RecursiveCharacterTextSplitter


def build_vectorstore(kb_path: str):
    raw_text = Path(kb_path).read_text(encoding="utf-8")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=250,
        chunk_overlap=40,
        separators=["\n## ", "\n### ", "\n- ", "\n", " "],
    )
    chunks = splitter.split_text(raw_text)
    client = genai.Client()
    embeddings = []

    for chunk in chunks:
        response = client.models.embed_content(
            model="gemini-embedding-001",
            contents=chunk,
        )
        embeddings.append(np.array(response.embeddings[0].values, dtype=np.float32))

    return {
        "chunks": chunks,
        "embeddings": embeddings,
    }


def retrieve_context(vectorstore, query: str, k: int = 3) -> str:
    client = genai.Client()
    query_response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=query,
    )
    query_embedding = np.array(query_response.embeddings[0].values, dtype=np.float32)

    scored_chunks = []
    for chunk, embedding in zip(vectorstore["chunks"], vectorstore["embeddings"]):
        score = _cosine_similarity(query_embedding, embedding)
        scored_chunks.append((score, chunk))

    scored_chunks.sort(key=lambda item: item[0], reverse=True)
    return "\n\n".join(chunk for _, chunk in scored_chunks[:k])


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denominator = np.linalg.norm(a) * np.linalg.norm(b)
    if denominator == 0:
        return 0.0
    return float(np.dot(a, b) / denominator)
