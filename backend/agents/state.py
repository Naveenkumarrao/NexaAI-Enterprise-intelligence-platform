from typing import TypedDict, List, Dict, Optional, Any


class AgentState(TypedDict):
    task_id: str
    task_type: str                      # analysis | comparison | summary | report
    user_instruction: str
    document_ids: List[str]             # doc IDs from DB
    document_names: Dict[str, str]      # doc ID -> original filename
    document_paths: List[str]           # file paths on disk
    extracted_texts: Dict[str, str]     # doc_id -> raw text
    chunks: Dict[str, List[str]]        # doc_id -> chunks
    embeddings_ready: bool
    combined_index_id: str
    retrieved_context: str
    analysis_result: Dict[str, Any]
    comparison_result: Dict[str, Any]
    report_data: Dict[str, Any]
    pdf_path: str
    excel_path: str
    workflow_steps: List[str]
    next: str                           # LangGraph router key
    error: Optional[str]
