from backend.agents.state import AgentState
from langchain_core.messages import HumanMessage, SystemMessage
from backend.llm_factory import get_llm


def comparison_agent(state: AgentState) -> AgentState:
    """Compares multiple documents, evaluates pricing/features/compliance/risks, generates comparison table."""
    steps = state.get("workflow_steps", [])
    steps.append("comparison_agent: started")

    extracted_texts = state.get("extracted_texts", {})
    instruction = state.get("user_instruction", "Compare these documents.")

    if len(extracted_texts) < 2:
        raise ValueError("Comparison requires at least two documents")

    llm = get_llm(temperature=0.1)

    # Build multi-doc context (truncated per doc to fit context window)
    doc_summaries = ""
    for doc_id, text in extracted_texts.items():
        doc_summaries += f"\n\n=== Document: {doc_id} ===\n{text[:3000]}"

    system_prompt = (
        "You are an expert procurement and contract analyst. "
        "Your task is to compare multiple business documents (e.g., vendor proposals, contracts, invoices). "
        "Provide:\n"
        "1. A side-by-side feature/pricing/compliance comparison\n"
        "2. Strengths and weaknesses of each document/vendor\n"
        "3. Risk assessment per document\n"
        "4. A clear recommendation on the best option with justification\n\n"
        "Format comparison as a markdown table where possible."
    )

    user_prompt = (
        f"User Instruction: {instruction}\n\n"
        f"Documents to compare:{doc_summaries}\n\n"
        "Provide: COMPARISON TABLE (markdown), STRENGTHS & WEAKNESSES, RISK ASSESSMENT, RECOMMENDATION."
    )

    comparison_text = ""
    try:
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        response = llm.invoke(messages)
        comparison_text = response.content
        if not comparison_text or not comparison_text.strip():
            raise RuntimeError("The language model returned an empty comparison")
        steps.append("comparison_agent: LLM comparison completed")
    except Exception as e:
        steps.append(f"comparison_agent: LLM error -> {e}")
        raise RuntimeError(f"Comparison agent failed: {e}") from e

    def extract_section(text: str, section: str) -> str:
        import re
        pattern = rf"{section}[:\n]+(.*?)(?=\n[A-Z &]+[:\n]|$)"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else ""

    # Parse markdown table rows into list of dicts
    def parse_markdown_table(text: str):
        import re
        lines = text.split("\n")
        table_lines = [l for l in lines if l.strip().startswith("|")]
        if len(table_lines) < 2:
            return []
        headers = [h.strip() for h in table_lines[0].split("|") if h.strip()]
        rows = []
        for line in table_lines[2:]:
            cols = [c.strip() for c in line.split("|") if c.strip()]
            if len(cols) == len(headers):
                rows.append(dict(zip(headers, cols)))
        return rows

    comparison_result = {
        "raw": comparison_text,
        "comparison_table": parse_markdown_table(comparison_text),
        "strengths_weaknesses": extract_section(comparison_text, "STRENGTHS"),
        "risk_assessment": extract_section(comparison_text, "RISK ASSESSMENT"),
        "recommendation": extract_section(comparison_text, "RECOMMENDATION"),
        "documents_compared": list(extracted_texts.keys()),
    }

    steps.append("comparison_agent: completed")
    return {
        **state,
        "comparison_result": comparison_result,
        "workflow_steps": steps,
        "next": "report_agent",
    }
