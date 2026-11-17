from backend.agents.state import AgentState
from langchain_core.messages import HumanMessage, SystemMessage
from backend.llm_factory import get_llm


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
    Understands user goal, plans the workflow and coordinates all agents.
    Determines task_type and sets the initial routing.
    """
    steps = state.get("workflow_steps", [])
    steps.append("supervisor: started")

    instruction = state.get("user_instruction", "")
    task_type = state.get("task_type") or detect_task_type(instruction)

    llm = get_llm(temperature=0)

    system_prompt = (
        "You are the supervisor of a multi-agent document intelligence platform. "
        "Given the user instruction and task type, confirm the execution plan. "
        "Respond with ONLY the task type as one word: analysis | comparison | summary | report"
    )
    user_prompt = f"User Instruction: {instruction}\nDetected Task Type: {task_type}\nConfirm task type:"

    try:
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        response = llm.invoke(messages)
        confirmed = response.content.strip().lower().split()[0]
        if confirmed in ["analysis", "comparison", "summary", "report"]:
            task_type = confirmed
        steps.append(f"supervisor: task_type confirmed -> {task_type}")
    except Exception as e:
        steps.append(f"supervisor: LLM confirmation failed, using detected -> {task_type}: {e}")

    steps.append("supervisor: routing to ingestion_agent")
    return {
        **state,
        "task_type": task_type,
        "workflow_steps": steps,
        "next": "ingestion_agent",
    }
