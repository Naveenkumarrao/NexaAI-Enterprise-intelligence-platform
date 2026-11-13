from backend.agents.state import AgentState
from backend.tools.search_tool import build_faiss_index, semantic_search, build_combined_index


def retrieval_agent(state: AgentState) -> AgentState:
    """Creates embeddings, indexes in FAISS, retrieves relevant context (RAG)."""
    steps = state.get("workflow_steps", [])
    steps.append("retrieval_agent: started")

    chunks = state.get("chunks", {})

    # Build per-document FAISS indexes
    for doc_id, doc_chunks in chunks.items():
        if doc_chunks:
            try:
                info = build_faiss_index(doc_chunks, doc_id)
                steps.append(f"retrieval_agent: indexed {info['num_vectors']} chunks for {doc_id}")
            except Exception as e:
                steps.append(f"retrieval_agent: index error for {doc_id} -> {e}")

    # Build combined index for cross-document retrieval
    combined_id = ""
    try:
        combined_id = build_combined_index(chunks)
        steps.append(f"retrieval_agent: combined index built -> {combined_id}")
    except Exception as e:
        steps.append(f"retrieval_agent: combined index error -> {e}")

    # Retrieve relevant context using user instruction as query
    query = state.get("user_instruction", "Summarize the key points of these documents.")
    doc_ids = list(chunks.keys())
    retrieved_context = ""

    try:
        results = semantic_search(query, doc_ids, top_k=6)
        retrieved_context = "\n\n---\n\n".join(
            [f"[Source: {r['doc_id']}]\n{r['chunk']}" for r in results]
        )
        steps.append(f"retrieval_agent: retrieved {len(results)} relevant chunks")
    except Exception as e:
        # Fallback: concatenate first 2000 chars of each doc
        parts = []
        for doc_id, text in state.get("extracted_texts", {}).items():
            parts.append(f"[Source: {doc_id}]\n{text[:2000]}")
        retrieved_context = "\n\n---\n\n".join(parts)
        steps.append(f"retrieval_agent: semantic search failed, using fallback -> {e}")

    steps.append("retrieval_agent: completed")
    return {
        **state,
        "embeddings_ready": True,
        "combined_index_id": combined_id,
        "retrieved_context": retrieved_context,
        "workflow_steps": steps,
        "next": "analysis_agent",
    }
