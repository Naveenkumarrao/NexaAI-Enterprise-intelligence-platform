import os
from datetime import datetime

import pandas as pd
import requests
import streamlit as st


API_BASE = os.getenv("API_BASE", "http://localhost:8000").rstrip("/")
REQUEST_TIMEOUT = 60
WORKFLOW_TYPES = ["analysis", "comparison", "summary", "report"]
AGENTS = [
    ("supervisor", "Orchestration Agent", "Plans and coordinates the workflow"),
    ("ingestion_agent", "Document Ingestion Agent", "Extracts text from uploaded PDFs"),
    ("retrieval_agent", "Knowledge Retrieval Agent", "Finds relevant document context"),
    ("analysis_agent", "Analysis Agent", "Identifies findings, risks, and numbers"),
    ("comparison_agent", "Comparison Agent", "Compares source documents"),
    ("report_agent", "Report Generation Agent", "Creates the report and exports"),
]

st.set_page_config(
    page_title="NexaAI | Document Intelligence",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    .stApp { background: #f5f7fb; }
    [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"] { display: none; }
    .block-container { max-width: 1120px; padding-top: 2rem; }
    .brand { font: 800 24px Manrope, sans-serif; letter-spacing: -1px; color: #17243b; }
    .brand span { color: #5478e5; }
    .eyebrow { color: #69809f; font-size: 12px; font-weight: 700; letter-spacing: 1.4px; text-transform: uppercase; }
    .page-title { color: #17243b; font: 800 32px Manrope, sans-serif; letter-spacing: -1px; margin: 0; }
    .page-subtitle { color: #748198; font-size: 15px; margin: 5px 0 22px; }
    div[data-testid="stMetric"] { background: white; border: 1px solid #e8edf5; border-radius: 14px; padding: 18px 20px; }
    div.stButton > button, div.stFormSubmitButton > button { border-radius: 9px; font-weight: 600; }
    </style>
    """,
    unsafe_allow_html=True,
)


def api_request(method, path, **kwargs):
    try:
        response = requests.request(
            method,
            f"{API_BASE}{path}",
            timeout=REQUEST_TIMEOUT,
            **kwargs,
        )
    except requests.RequestException as exc:
        raise RuntimeError(
            f"Could not connect to the API at {API_BASE}. Start the FastAPI backend and try again. ({exc})"
        ) from exc

    if not response.ok:
        try:
            detail = response.json().get("detail", response.text)
        except (ValueError, AttributeError):
            detail = response.text
        raise RuntimeError(f"API error ({response.status_code}): {detail}")

    if response.status_code == 204 or not response.content:
        return None
    return response


def get_json(path):
    return api_request("GET", path).json()


def format_time(value):
    if not value:
        return "—"
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime(
            "%b %d, %Y · %H:%M"
        )
    except (ValueError, TypeError):
        return str(value)


def show_api_error(exc):
    st.error(str(exc))


def render_agent_flow(task):
    steps = task.get("workflow_steps") or []
    task_type = task.get("task_type", "analysis")
    task_status = task.get("status", "unknown")
    statuses = []
    completed_count = 0

    for agent_id, label, description in AGENTS:
        if agent_id == "comparison_agent" and task_type != "comparison":
            statuses.append((label, description, "Skipped"))
            continue

        agent_steps = [
            str(step).lower()
            for step in steps
            if str(step).lower().startswith(f"{agent_id}:")
        ]
        if any(step.startswith(f"{agent_id}: completed") for step in agent_steps):
            status = "Completed"
            completed_count += 1
        elif any(step.startswith(f"{agent_id}: running") for step in agent_steps):
            status = "Failed" if task_status == "failed" else "Running"
        elif any("error" in step for step in agent_steps) and task_status == "failed":
            status = "Failed"
        else:
            status = "Waiting"
        statuses.append((label, description, status))

    human_approved = (task.get("result") or {}).get("human_approved", False)
    statuses.append(
        (
            "Human Review",
            "Edit and approve the report before downloads",
            "Completed" if human_approved else "Waiting",
        )
    )
    active_count = sum(status != "Skipped" for _, _, status in statuses)
    if active_count:
        st.progress(
            completed_count / active_count,
            text=f"{completed_count} of {active_count} agents completed",
        )

    columns = st.columns(3)
    for index, (label, description, status) in enumerate(statuses):
        with columns[index % len(columns)].container(border=True):
            icon = {
                "Completed": "✓",
                "Running": "↻",
                "Failed": "!",
                "Skipped": "—",
                "Waiting": "○",
            }[status]
            st.markdown(f"**{icon} {label}**")
            st.caption(description)
            st.caption(status)

    if steps:
        with st.expander("Execution log", expanded=task_status in {"running", "failed"}):
            for step in steps:
                st.markdown(f"- {step}")


def render_downloads(task):
    task_id = task["task_id"]
    result = task.get("result") or {}
    if not result.get("human_approved"):
        st.info("Review and approve the report above to enable downloads.")
        return

    exports = (
        ("pdf", "PDF report", "application/pdf", result.get("pdf_path")),
        (
            "excel",
            "Excel report",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            result.get("excel_path"),
        ),
    )
    columns = st.columns(len(exports))
    for column, (file_type, label, mime, path) in zip(columns, exports):
        if not path:
            column.warning(f"{label} was not generated.")
            continue
        try:
            response = api_request(
                "GET", f"/analysis/task/{task_id}/download/{file_type}"
            )
        except RuntimeError as exc:
            column.warning(f"{label} is unavailable: {exc}")
            continue
        column.download_button(
            f"Download {file_type.upper()}",
            data=response.content,
            file_name=f"nexa-{task_id[:8]}.{file_type if file_type == 'pdf' else 'xlsx'}",
            mime=mime,
            key=f"download-{file_type}-{task_id}",
        )


def render_agent_outputs(task):
    result = task.get("result") or {}
    analysis = result.get("analysis") or {}
    comparison = result.get("comparison") or {}

    if analysis:
        with st.expander("Analysis Agent output", expanded=True):
            for key, label in (
                ("summary", "Summary"),
                ("key_insights", "Key insights"),
                ("risks", "Risks"),
                ("pros_cons", "Pros and cons"),
                ("numerical_data", "Numerical data"),
            ):
                value = analysis.get(key)
                if value:
                    st.markdown(f"**{label}**")
                    st.markdown(str(value))
            if analysis.get("raw"):
                st.markdown("**Full analysis response**")
                st.markdown(str(analysis["raw"]))

    if comparison:
        with st.expander("Comparison Agent output", expanded=True):
            comparison_table = comparison.get("comparison_table") or []
            if comparison_table:
                st.dataframe(
                    pd.DataFrame(comparison_table),
                    use_container_width=True,
                    hide_index=True,
                )
            for key, label in (
                ("strengths_weaknesses", "Strengths and weaknesses"),
                ("risk_assessment", "Risk assessment"),
                ("recommendation", "Recommendation"),
            ):
                value = comparison.get(key)
                if value:
                    st.markdown(f"**{label}**")
                    st.markdown(str(value))
            if comparison.get("raw"):
                st.markdown("**Full comparison response**")
                st.markdown(str(comparison["raw"]))


def render_report_review(task):
    result = task.get("result") or {}
    report = result.get("report") or {}
    comparison = result.get("comparison") or {}
    task_id = task["task_id"]
    if not report:
        st.warning("The workflow completed without report content.")
        return

    documents = result.get("documents") or []
    if documents:
        st.markdown("#### Source documents")
        st.write(", ".join(document.get("filename", "Untitled") for document in documents))

    st.markdown("#### Human review and report editing")
    st.caption(
        "Review or edit the generated sections. Approval saves your changes and regenerates both reports."
    )
    approved = st.checkbox(
        "I have reviewed this report and approve the final downloadable version.",
        key=f"approve-report-{task_id}",
    )

    insights = report.get("key_insights") or []
    if isinstance(insights, str):
        insights = [line.strip(" •-\t") for line in insights.splitlines() if line.strip()]
    table = report.get("comparison_table") or comparison.get("comparison_table") or []

    with st.form(f"report-review-{task_id}"):
        summary = st.text_area(
            "Executive summary",
            value=report.get("summary", ""),
            height=130,
            key=f"report-summary-{task_id}",
        )
        key_insights_text = st.text_area(
            "Key insights (one per line)",
            value="\n".join(str(item) for item in insights),
            key=f"report-insights-{task_id}",
        )
        risks = st.text_area(
            "Risks and concerns",
            value=report.get("risks", ""),
            key=f"report-risks-{task_id}",
        )
        pros_cons = st.text_area(
            "Pros and cons",
            value=report.get("pros_cons", ""),
            key=f"report-pros-cons-{task_id}",
        )
        numerical_data = st.text_area(
            "Numerical findings",
            value=report.get("numerical_data", ""),
            key=f"report-numerical-data-{task_id}",
        )
        recommendation = st.text_area(
            "Final recommendation",
            value=report.get("recommendation", ""),
            key=f"report-recommendation-{task_id}",
        )
        comparison_strengths = st.text_area(
            "Comparison strengths and weaknesses",
            value=report.get("comparison_strengths_weaknesses", ""),
            key=f"report-comparison-strengths-{task_id}",
        )
        comparison_risks = st.text_area(
            "Comparison risk assessment",
            value=report.get("comparison_risk_assessment", ""),
            key=f"report-comparison-risks-{task_id}",
        )
        edited_table = (
            st.data_editor(
                pd.DataFrame(table),
                num_rows="dynamic",
                use_container_width=True,
                key=f"report-comparison-table-{task_id}",
            )
            if table
            else pd.DataFrame()
        )
        save_report = st.form_submit_button(
            "Approve, save edits, and regenerate reports",
            type="primary",
            disabled=not approved,
        )

    if save_report:
        report_data = {
            "summary": summary,
            "key_insights": [
                line.strip(" •-\t")
                for line in key_insights_text.splitlines()
                if line.strip()
            ],
            "risks": risks,
            "pros_cons": pros_cons,
            "numerical_data": numerical_data,
            "recommendation": recommendation,
            "comparison_strengths_weaknesses": comparison_strengths,
            "comparison_risk_assessment": comparison_risks,
            "comparison_table": edited_table.fillna("").to_dict(orient="records"),
        }
        try:
            api_request(
                "PUT",
                f"/analysis/task/{task_id}/report",
                json=report_data,
            )
        except RuntimeError as exc:
            show_api_error(exc)
        else:
            st.success("Report approved. Updated PDF and Excel files are ready.")
            st.rerun()

    render_downloads(task)


def render_task_details(task):
    st.markdown("### Agent execution")
    st.caption(
        f"{task.get('task_type', 'analysis').title()} · "
        f"Started {format_time(task.get('created_at'))}"
    )
    render_agent_flow(task)

    status = task.get("status", "unknown")
    if status == "failed":
        st.error(task.get("error") or "The workflow failed.")
        return
    if status != "completed":
        st.info("The orchestration agent is coordinating the document workflow.")
        return

    st.success("All required agents completed the workflow.")
    render_agent_outputs(task)
    st.divider()
    render_report_review(task)


def render_task(task_id):
    try:
        task = get_json(f"/tasks/{task_id}")
    except (RuntimeError, ValueError) as exc:
        show_api_error(exc)
        return

    fragment = getattr(st, "fragment", None)
    if task.get("status") in {"pending", "running"} and fragment:
        @fragment(run_every="2s")
        def live_execution():
            try:
                current_task = get_json(f"/tasks/{task_id}")
            except (RuntimeError, ValueError) as exc:
                show_api_error(exc)
                return
            render_task_details(current_task)
            if current_task.get("status") not in {"pending", "running"}:
                st.rerun()

        live_execution()
        return

    render_task_details(task)
    if task.get("status") in {"pending", "running"}:
        if st.button("Refresh agent progress"):
            st.rerun()


def run_workflow(uploaded_files, task_type, instruction):
    document_ids = []
    try:
        with st.status("Preparing your documents...", expanded=True) as progress:
            for uploaded_file in uploaded_files:
                response = api_request(
                    "POST",
                    "/documents/upload",
                    files={
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            uploaded_file.type or "application/pdf",
                        )
                    },
                )
                document_ids.append(response.json()["doc_id"])
                progress.write(f"Uploaded {uploaded_file.name}")

            task = api_request(
                "POST",
                "/tasks/",
                json={
                    "user_instruction": instruction.strip(),
                    "task_type": task_type,
                    "document_ids": document_ids,
                },
            ).json()
            st.session_state["selected_task_id"] = task["task_id"]
            progress.update(
                label="Documents ready. Starting the agent workflow...",
                state="complete",
                expanded=False,
            )
    except (RuntimeError, ValueError, KeyError) as exc:
        show_api_error(exc)
        return
    st.rerun()


st.markdown('<div class="brand">Nexa<span>AI</span></div>', unsafe_allow_html=True)
st.markdown('<div class="eyebrow">DOCUMENT INTELLIGENCE · MULTI-AGENT WORKFLOW</div>', unsafe_allow_html=True)
st.markdown('<h1 class="page-title">Analyze your documents</h1>', unsafe_allow_html=True)
st.markdown(
    '<div class="page-subtitle">Upload PDFs, describe what you need, and let the orchestration agent coordinate the work.</div>',
    unsafe_allow_html=True,
)

uploaded_files = st.file_uploader(
    "Upload PDF documents",
    type=["pdf"],
    accept_multiple_files=True,
    help="Upload one or more PDFs. Comparisons require at least two documents.",
)
task_type = st.selectbox(
    "What should the agents do?",
    WORKFLOW_TYPES,
    format_func=lambda value: {
        "analysis": "Analyze",
        "comparison": "Compare documents",
        "summary": "Summarize",
        "report": "Generate a report",
    }[value],
)

if task_type == "comparison" and len(uploaded_files or []) < 2:
    st.info("Upload at least two PDFs to compare documents.")

with st.form("workflow-request"):
    instruction = st.text_area(
        "What do you need?",
        placeholder="For example: Compare the proposals, identify pricing and delivery risks, and recommend the best option.",
        height=120,
    )
    start_workflow = st.form_submit_button(
        "Run agent workflow",
        type="primary",
        disabled=(
            not uploaded_files
            or (task_type == "comparison" and len(uploaded_files or []) < 2)
        ),
    )

if start_workflow:
    if not instruction.strip():
        st.warning("Enter a prompt describing what you need.")
    else:
        run_workflow(uploaded_files, task_type, instruction)

selected_task_id = st.session_state.get("selected_task_id")
if selected_task_id:
    st.divider()
    render_task(selected_task_id)
