import streamlit as st
import requests
import time
from ui import apply_theme, page_header

API_BASE = "http://localhost:8000"

st.set_page_config(page_title="Workflow Monitor | Nexa AI", page_icon="✦", layout="wide")
apply_theme()
page_header(
    "Workflow monitor",
    "Track execution status and review the steps completed by your AI agents.",
    "OPERATIONS",
)

refresh_col, toggle_col = st.columns([1, 3])
with refresh_col:
    if st.button("Refresh status"):
        st.rerun()
with toggle_col:
    auto_refresh = st.toggle("Refresh automatically every 5 seconds", value=False)

try:
    tasks = requests.get(f"{API_BASE}/tasks/", timeout=5).json()
except Exception as error:
    st.error(f"Cannot connect to the API: {error}")
    st.stop()

if not tasks:
    st.info("No workflows found. Start an analysis from the AI workspace.")
    st.page_link("pages/2_chat.py", label="Open AI workspace")
    st.stop()

completed_count = sum(1 for task in tasks if task["status"] == "completed")
running_count = sum(1 for task in tasks if task["status"] == "running")
failed_count = sum(1 for task in tasks if task["status"] == "failed")

total_col, completed_col, running_col, failed_col = st.columns(4)
total_col.metric("Total workflows", len(tasks))
completed_col.metric("Completed", completed_count)
running_col.metric("In progress", running_count)
failed_col.metric("Failed", failed_count)

filter_col, count_col = st.columns([1, 3])
with filter_col:
    filter_status = st.selectbox(
        "Status",
        ["all", "completed", "running", "pending", "failed"],
        format_func=lambda value: value.title(),
    )
filtered = tasks if filter_status == "all" else [
    task for task in tasks if task["status"] == filter_status
]
with count_col:
    st.caption(f"Showing {len(filtered)} of {len(tasks)} workflows")

for task in filtered:
    task_type = task["task_type"].title()
    instruction = task["user_instruction"]
    label = f"{task_type} · {instruction[:80]}"
    if len(instruction) > 80:
        label += "…"

    with st.expander(label):
        id_col, status_col, created_col = st.columns([2, 1, 1])
        id_col.markdown(f"**Workflow ID**  \n`{task['task_id']}`")
        status_col.markdown(f"**Status**  \n{task['status'].title()}")
        created_col.markdown(f"**Created**  \n{task['created_at'][:19]}")

        try:
            detail = requests.get(
                f"{API_BASE}/tasks/{task['task_id']}", timeout=5
            ).json()
            steps = detail.get("workflow_steps", [])
            if steps:
                st.markdown("**Workflow steps**")
                st.write(" → ".join(str(step) for step in steps))
            if detail.get("error"):
                st.error(f"Workflow error: {detail['error']}")
            if detail["status"] == "completed" and detail.get("result"):
                st.success("Workflow completed successfully.")
                pdf_col, excel_col = st.columns(2)
                with pdf_col:
                    pdf_url = (
                        f"{API_BASE}/analysis/task/{task['task_id']}/download/pdf"
                    )
                    st.link_button("Download PDF report", pdf_url)
                with excel_col:
                    excel_url = (
                        f"{API_BASE}/analysis/task/{task['task_id']}/download/excel"
                    )
                    st.link_button("Download Excel report", excel_url)
        except Exception as error:
            st.warning(f"Could not load workflow details: {error}")

if auto_refresh:
    time.sleep(5)
    st.rerun()
