import faiss
import numpy as np
import pickle
from pathlib import Path
from typing import List, Dict, Tuple
from sentence_transformers import SentenceTransformer
from backend.config import settings

_model: SentenceTransformer = None


def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _model


def embed_texts(texts: List[str]) -> np.ndarray:
    model = get_embedding_model()
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    return embeddings.astype("float32")


def build_faiss_index(chunks: List[str], doc_id: str) -> Dict:
    embeddings = embed_texts(chunks)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    index_path = settings.VECTOR_STORE_DIR / f"{doc_id}.index"
    meta_path = settings.VECTOR_STORE_DIR / f"{doc_id}.meta"

    faiss.write_index(index, str(index_path))
    with open(meta_path, "wb") as f:
        pickle.dump({"chunks": chunks, "doc_id": doc_id}, f)

    return {"doc_id": doc_id, "num_vectors": len(chunks), "dim": dim}


def load_faiss_index(doc_id: str) -> Tuple[faiss.Index, List[str]]:
    index_path = settings.VECTOR_STORE_DIR / f"{doc_id}.index"
    meta_path = settings.VECTOR_STORE_DIR / f"{doc_id}.meta"

    if not index_path.exists():
        raise FileNotFoundError(f"No FAISS index for doc_id: {doc_id}")

    index = faiss.read_index(str(index_path))
    with open(meta_path, "rb") as f:
        meta = pickle.load(f)
    return index, meta["chunks"]


def semantic_search(query: str, doc_ids: List[str], top_k: int = 5) -> List[Dict]:
    query_vec = embed_texts([query])
    results = []

    for doc_id in doc_ids:
        try:
            index, chunks = load_faiss_index(doc_id)
            k = min(top_k, len(chunks))
            distances, indices = index.search(query_vec, k)
            for dist, idx in zip(distances[0], indices[0]):
                if idx != -1:
                    results.append({
                        "doc_id": doc_id,
                        "chunk": chunks[idx],
                        "score": float(dist),
                    })
        except FileNotFoundError:
            continue

    results.sort(key=lambda x: x["score"])
    return results[:top_k]


def build_combined_index(all_chunks: Dict[str, List[str]]) -> str:
    """Build a merged index from multiple documents."""
    combined_id = "combined_" + "_".join(sorted(all_chunks.keys()))[:40]
    merged_chunks = []
    for doc_id, chunks in all_chunks.items():
        for chunk in chunks:
            merged_chunks.append(f"[{doc_id}] {chunk}")
    build_faiss_index(merged_chunks, combined_id)
    return combined_id
