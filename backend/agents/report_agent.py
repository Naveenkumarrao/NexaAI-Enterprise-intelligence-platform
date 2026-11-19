from backend.agents.state import AgentState
from backend.tools.report_exporter import export_pdf, export_excel
from langchain_core.messages import HumanMessage, SystemMessage
from backend.llm_factory import get_llm
import uuid


def report_agent(state: AgentState) -> AgentState:
    """Summarises findings, gives final recommendation, generates well-formatted PDF/Excel report."""
    steps = state.get("workflow_steps", [])
    steps.append("report_agent: started")

    analysis = state.get("analysis_result", {})
    comparison = state.get("comparison_result", {})
    instruction = state.get("user_instruction", "")
    task_type = state.get("task_type", "analysis")

    llm = get_llm(temperature=0.2)

    system_prompt = (
        "You are a senior report writer. Based on the analysis and comparison results provided, "
        "write a professional executive summary and final recommendation. "
        "Be concise, clear, and actionable."
    )

    context_for_report = f"Analysis:\n{analysis.get('raw', '')}\n\nComparison:\n{comparison.get('raw', '')}"

    user_prompt = (
        f"User Instruction: {instruction}\n\n"
        f"Results:\n{context_for_report}\n\n"
        "Write: FINAL SUMMARY and FINAL RECOMMENDATION (with reasoning)."
    )

    final_summary = ""
    final_recommendation = ""
    try:
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        response = llm.invoke(messages)
        raw = response.content
        import re
        def extract(text, section):
            pattern = rf"{section}[:\n]+(.*?)(?=\nFINAL [A-Z]+[:\n]|$)"
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            return match.group(1).strip() if match else text[:500]
        final_summary = extract(raw, "FINAL SUMMARY")
        final_recommendation = extract(raw, "FINAL RECOMMENDATION")
        steps.append("report_agent: LLM final report completed")
    except Exception as e:
        final_summary = analysis.get("summary", "See analysis results.")
        final_recommendation = comparison.get("recommendation", "See comparison results.")
        steps.append(f"report_agent: LLM error -> {e}")

    report_data = {
        "title": f"Enterprise Analysis Report — {task_type.capitalize()}",
        "summary": final_summary or analysis.get("summary", ""),
        "analysis": analysis.get("key_insights", ""),
        "key_insights": [l.strip("•- ") for l in analysis.get("key_insights", "").split("\n") if l.strip()],
        "risks": analysis.get("risks", "") or comparison.get("risk_assessment", ""),
        "pros_cons": analysis.get("pros_cons", ""),
        "numerical_data": analysis.get("numerical_data", ""),
        "recommendation": final_recommendation or comparison.get("recommendation", ""),
        "comparison_strengths_weaknesses": comparison.get("strengths_weaknesses", ""),
        "comparison_risk_assessment": comparison.get("risk_assessment", ""),
        "analysis_raw": analysis.get("raw", ""),
        "comparison_raw": comparison.get("raw", ""),
        "comparison_table": comparison.get("comparison_table", []),
    }

    file_id = str(uuid.uuid4())[:8]
    pdf_path, excel_path = "", ""
    try:
        pdf_path = export_pdf(report_data, f"report_{file_id}")
        steps.append(f"report_agent: PDF exported -> {pdf_path}")
    except Exception as e:
        steps.append(f"report_agent: PDF export error -> {e}")

    try:
        excel_path = export_excel(report_data, f"report_{file_id}")
        steps.append(f"report_agent: Excel exported -> {excel_path}")
    except Exception as e:
        steps.append(f"report_agent: Excel export error -> {e}")

    steps.append("report_agent: completed")
    return {
        **state,
        "report_data": report_data,
        "pdf_path": pdf_path,
        "excel_path": excel_path,
        "workflow_steps": steps,
        "next": "END",
    }
