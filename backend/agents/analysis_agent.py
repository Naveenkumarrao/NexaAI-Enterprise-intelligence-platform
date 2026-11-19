from backend.agents.state import AgentState
from langchain_core.messages import HumanMessage, SystemMessage
from backend.llm_factory import get_llm


def analysis_agent(state: AgentState) -> AgentState:
    """Analyses extracted data, identifies key points, finds risks/pros/cons, extracts business insights."""
    steps = state.get("workflow_steps", [])
    steps.append("analysis_agent: started")

    context = state.get("retrieved_context", "")
    instruction = state.get("user_instruction", "Analyse the documents.")
    task_type = state.get("task_type", "analysis")

    llm = get_llm(temperature=0.1)

    system_prompt = (
        "You are a senior business analyst specialising in document intelligence. "
        "Your task is to analyse provided document context thoroughly and extract:\n"
        "1. A concise executive summary\n"
        "2. Key business insights and findings\n"
        "3. Identified risks, challenges, or concerns\n"
        "4. Pros and cons (if applicable)\n"
        "5. Any numerical data, pricing, or cost information found\n\n"
        "Be precise, factual, and structure your response clearly."
    )

    user_prompt = (
        f"User Instruction: {instruction}\n\n"
        f"Document Context:\n{context}\n\n"
        "Provide a structured analysis with sections: "
        "SUMMARY, KEY INSIGHTS, RISKS, PROS & CONS, NUMERICAL DATA."
    )

    analysis_text = ""
    try:
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        response = llm.invoke(messages)
        analysis_text = response.content
        if not analysis_text or not analysis_text.strip():
            raise RuntimeError("The language model returned an empty analysis")
        steps.append("analysis_agent: LLM analysis completed")
    except Exception as e:
        steps.append(f"analysis_agent: LLM error -> {e}")
        raise RuntimeError(f"Analysis agent failed: {e}") from e

    # Parse structured sections
    def extract_section(text: str, section: str) -> str:
        import re
        pattern = rf"{section}[:\n]+(.*?)(?=\n[A-Z &]+[:\n]|$)"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else ""

    analysis_result = {
        "raw": analysis_text,
        "summary": extract_section(analysis_text, "SUMMARY"),
        "key_insights": extract_section(analysis_text, "KEY INSIGHTS"),
        "risks": extract_section(analysis_text, "RISKS"),
        "pros_cons": extract_section(analysis_text, "PROS"),
        "numerical_data": extract_section(analysis_text, "NUMERICAL DATA"),
        "task_type": task_type,
    }

    steps.append("analysis_agent: completed")
    next_node = "comparison_agent" if task_type == "comparison" else "report_agent"
    return {
        **state,
        "analysis_result": analysis_result,
        "workflow_steps": steps,
        "next": next_node,
    }
