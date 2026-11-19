from backend.agents.state import AgentState
from backend.tools.document_processor import extract_text_from_file
from backend.tools.ocr_tool import extract_with_ocr


def ingestion_agent(state: AgentState) -> AgentState:
    """Reads & parses files, extracts text (PDF/OCR), cleans & structures data."""
    steps = state.get("workflow_steps", [])
    steps.append("ingestion_agent: started")

    extracted_texts = {}
    chunks = {}

    for doc_id, file_path in zip(state["document_ids"], state["document_paths"]):
        try:
            result = extract_text_from_file(file_path)
            text = result["text"]

            # Fallback to OCR if extraction yielded too little text
            if len(text.strip()) < 100:
                steps.append(f"ingestion_agent: OCR fallback for {doc_id}")
                text = extract_with_ocr(file_path)
                result["text"] = text
                result["chunks"] = [text[i:i+500] for i in range(0, len(text), 450)]

            extracted_texts[doc_id] = text
            chunks[doc_id] = result["chunks"]
            steps.append(f"ingestion_agent: extracted {len(text)} chars from {doc_id}")
        except Exception as e:
            steps.append(f"ingestion_agent: error on {doc_id} -> {e}")
            raise RuntimeError(f"Could not extract text from document {doc_id}: {e}") from e

        if not text.strip():
            raise RuntimeError(f"No text could be extracted from document {doc_id}")

    steps.append("ingestion_agent: completed")
    return {
        **state,
        "extracted_texts": extracted_texts,
        "chunks": chunks,
        "workflow_steps": steps,
        "next": "retrieval_agent",
    }
