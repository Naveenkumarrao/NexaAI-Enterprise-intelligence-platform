from langgraph.graph import StateGraph, END
from backend.agents.state import AgentState
from backend.agents.supervisor import supervisor_agent
from backend.agents.ingestion_agent import ingestion_agent
from backend.agents.retrieval_agent import retrieval_agent
from backend.agents.analysis_agent import analysis_agent
from backend.agents.comparison_agent import comparison_agent
from backend.agents.report_agent import report_agent
from collections.abc import Awaitable, Callable
from typing import Any


def route_after_supervisor(state: AgentState) -> str:
    return state.get("next", "ingestion_agent")


def route_after_ingestion(state: AgentState) -> str:
    return state.get("next", "retrieval_agent")


def route_after_retrieval(state: AgentState) -> str:
    return state.get("next", "analysis_agent")


def route_after_analysis(state: AgentState) -> str:
    return state.get("next", "report_agent")


def route_after_comparison(state: AgentState) -> str:
    return state.get("next", "report_agent")


def build_workflow() -> StateGraph:
    graph = StateGraph(AgentState)

    # Register nodes
    graph.add_node("supervisor", supervisor_agent)
    graph.add_node("ingestion_agent", ingestion_agent)
    graph.add_node("retrieval_agent", retrieval_agent)
    graph.add_node("analysis_agent", analysis_agent)
    graph.add_node("comparison_agent", comparison_agent)
    graph.add_node("report_agent", report_agent)

    # Entry point
    graph.set_entry_point("supervisor")

    # Conditional edges
    graph.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {"ingestion_agent": "ingestion_agent"},
    )
    graph.add_conditional_edges(
        "ingestion_agent",
        route_after_ingestion,
        {"retrieval_agent": "retrieval_agent"},
    )
    graph.add_conditional_edges(
        "retrieval_agent",
        route_after_retrieval,
        {"analysis_agent": "analysis_agent"},
    )
    graph.add_conditional_edges(
        "analysis_agent",
        route_after_analysis,
        {
            "comparison_agent": "comparison_agent",
            "report_agent": "report_agent",
        },
    )
    graph.add_conditional_edges(
        "comparison_agent",
        route_after_comparison,
        {"report_agent": "report_agent"},
    )
    graph.add_edge("report_agent", END)

    return graph.compile()


# Singleton compiled graph
workflow_app = build_workflow()


async def run_workflow(
    initial_state: AgentState,
    progress_callback: Callable[[AgentState], Awaitable[None]] | None = None,
) -> AgentState:
    """Run the workflow and publish each completed agent state when requested."""
    final_state: dict[str, Any] = initial_state
    async for state in workflow_app.astream(initial_state, stream_mode="values"):
        final_state = state
        if progress_callback:
            await progress_callback(state)
    return final_state
