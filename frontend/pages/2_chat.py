import streamlit as st
import requests
import time
from ui import apply_theme, page_header

API_BASE = "http://localhost:8000"

st.set_page_config(page_title="AI Workspace | Nexa AI", page_icon="✦", layout="wide")
apply_theme()
page_header(
    "AI workspace",
    "Select your source documents and describe the outcome you need.",
    "ANALYSIS",
)

try:
    all_docs = requests.get(f"{API_BASE}/documents/", timeout=5).json()
except Exception as error:
    st.error(f"Could not load documents from the API: {error}")
    st.stop()

if not all_docs:
    st.info("Your document library is empty. Add documents before starting a workflow.")
    st.page_link("pages/1_upload_documents.py", label="Open document library")
    st.stop()

example_instructions = {
    "analysis": "Analyze the document and extract key business insights, risks, and recommendations.",
    "comparison": "Compare the selected proposals on price, features, compliance, and risk. Recommend the best option.",
    "summary": "Provide a concise executive summary of the key points in the selected document.",
    "report": "Generate a structured report with analysis, comparison, and a final recommendation.",
}
task_descriptions = {
    "analysis": "Identify insights, risks, and recommendations.",
    "comparison": "Evaluate selected documents against each other.",
    "summary": "Create a concise executive summary.",
    "report": "Generate a structured business report.",
}

with st.container(border=True):
    st.subheader("Configure your workflow")
    document_col, task_col = st.columns(2)
    with document_col:
        doc_options = {
            f"{doc['filename']} · {doc['doc_id'][:8]}": doc["doc_id"]
            for doc in all_docs
        }
        selected_labels = st.multiselect(
            "Source documents",
            options=list(doc_options.keys()),
            default=list(doc_options.keys())[:1],
            help="Choose one or more documents for the agents to use.",
        )
        selected_ids = [doc_options[label] for label in selected_labels]
    with task_col:
        task_type = st.selectbox(
            "Workflow type",
            options=["analysis", "comparison", "summary", "report"],
            format_func=lambda task: task.title(),
        )
        st.caption(task_descriptions[task_type])

    instruction = st.text_area(
        "Instructions",
        value=example_instructions[task_type],
        height=120,
        placeholder="Describe the question, criteria, or desired output.",
        help="Be specific about the context and decision criteria for better results.",
    )

    run_col, clear_col = st.columns([3, 1])
    with run_col:
        run_clicked = st.button(
            "Run workflow",
            type="primary",
            disabled=not selected_ids or not instruction.strip(),
        )
    with clear_col:
        if st.button("Clear session history"):
            st.session_state.pop("chat_history", None)
            st.rerun()

if run_clicked:
    if not selected_ids:
        st.error("Select at least one source document.")
    elif not instruction.strip():
        st.error("Enter instructions for the workflow.")
    else:
        with st.spinner("Starting workflow…"):
            try:
                response = requests.post(
                    f"{API_BASE}/tasks/",
                    json={
                        "user_instruction": instruction,
                        "task_type": task_type,
                        "document_ids": selected_ids,
                    },
                    timeout=15,
                )
                if response.status_code == 200:
                    task_data = response.json()
                    task_id = task_data["task_id"]
                    st.success(f"Workflow started · `{task_id}`")
                    st.session_state.setdefault("chat_history", []).append(
                        {
                            "task_id": task_id,
                            "task_type": task_type,
                            "instruction": instruction,
                            "docs": selected_labels,
                            "status": "pending",
                        }
                    )

                    progress_message = st.empty()
                    for _ in range(36):
                        time.sleep(5)
                        status_response = requests.get(
                            f"{API_BASE}/tasks/{task_id}", timeout=10
                        ).json()
                        current_status = status_response.get("status", "pending")
                        progress_message.info(
                            f"Workflow status · {current_status.title()}"
                        )

                        if current_status == "completed":
                            progress_message.success(
                                "Workflow completed. Results are ready to review."
                            )
                            st.session_state["last_task_id"] = task_id
                            for entry in st.session_state.get("chat_history", []):
                                if entry["task_id"] == task_id:
                                    entry["status"] = "completed"
                            break
                        if current_status == "failed":
                            progress_message.error(
                                f"Workflow failed: {status_response.get('error', 'Unknown error')}"
                            )
                            break
                    else:
                        progress_message.warning(
                            "Workflow is still running. Check the workflow monitor for updates."
                        )
                else:
                    st.error(f"Could not start workflow: {response.text}")
            except Exception as error:
                st.error(f"Workflow request failed: {error}")

st.subheader("Recent in-session activity")
history = st.session_state.get("chat_history", [])
if not history:
    st.info("Workflows started in this session will appear here.")
else:
    for entry in reversed(history):
        label = f"{entry['task_type'].title()} · {entry['instruction'][:70]}"
        with st.expander(label):
            st.markdown(f"**Workflow ID**  \n`{entry['task_id']}`")
            st.markdown(f"**Documents**  \n{', '.join(entry['docs'])}")
            st.markdown(f"**Status**  \n{entry['status'].title()}")
            if entry["status"] == "completed":
                st.page_link("pages/4_results_reports.py", label="Review results")
