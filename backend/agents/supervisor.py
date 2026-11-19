from backend.agents.state import AgentState


TASK_TYPE_MAP = {
    "comparison": "comparison",
    "compare": "comparison",
    "vendor": "comparison",
    "proposal": "comparison",
    "analysis": "analysis",
    "analyse": "analysis",
    "analyze": "analysis",
    "summary": "summary",
    "summarize": "summary",
    "summarise": "summary",
    "report": "report",
}


def detect_task_type(instruction: str) -> str:
    lower = instruction.lower()
    for keyword, task in TASK_TYPE_MAP.items():
        if keyword in lower:
            return task
    return "analysis"


def supervisor_agent(state: AgentState) -> AgentState:
    """
    Preserve the requested workflow type and route into document ingestion.
    """
    steps = list(state.get("workflow_steps", []))
    steps.append("supervisor: started")

    instruction = state.get("user_instruction", "")
    task_type = state.get("task_type")
    if task_type not in {"analysis", "comparison", "summary", "report"}:
        task_type = detect_task_type(instruction)

    steps.append(f"supervisor: selected workflow -> {task_type}")
    steps.append("supervisor: routing to ingestion_agent")
    steps.append("supervisor: completed")
    return {
        **state,
        "task_type": task_type,
        "workflow_steps": steps,
        "next": "ingestion_agent",
    }
