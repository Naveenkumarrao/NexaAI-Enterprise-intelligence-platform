import streamlit as st
import requests
from datetime import datetime
from ui import apply_theme, page_header

API_BASE = "http://localhost:8000"

st.set_page_config(
    page_title="Nexa AI | Dashboard",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_theme()
page_header(
    "Intelligence dashboard",
    "Monitor documents, AI workflows, and business-ready outputs in one place.",
    "OVERVIEW",
)

col_health, col_time = st.columns([2, 1])
with col_health:
    try:
        resp = requests.get(f"{API_BASE}/health", timeout=3)
        if resp.status_code == 200:
            st.success("Platform status · API connected")
        else:
            st.error("Platform status · API returned an error")
    except Exception:
        st.error("Platform status · API offline — start the FastAPI server")

with col_time:
    st.caption(f"Last checked · {datetime.now().strftime('%b %d, %Y at %H:%M:%S')}")

col1, col2, col3, col4 = st.columns(4)
try:
    tasks_resp = requests.get(f"{API_BASE}/tasks/", timeout=3).json()
    docs_resp = requests.get(f"{API_BASE}/documents/", timeout=3).json()

    total_tasks = len(tasks_resp)
    completed_tasks = sum(1 for task in tasks_resp if task["status"] == "completed")
    running_tasks = sum(1 for task in tasks_resp if task["status"] == "running")
    total_docs = len(docs_resp)
except Exception:
    total_tasks = completed_tasks = running_tasks = total_docs = 0

col1.metric("Documents", total_docs)
col2.metric("Total workflows", total_tasks)
col3.metric("Completed", completed_tasks)
col4.metric("In progress", running_tasks)

st.subheader("Recent workflows")
st.caption("Latest activity across document analysis and reporting.")
try:
    tasks_resp = requests.get(f"{API_BASE}/tasks/", timeout=3).json()
    if tasks_resp:
        for task in tasks_resp[:8]:
            instruction = task["user_instruction"]
            label = f"{task['task_type'].title()} · {instruction[:80]}"
            if len(instruction) > 80:
                label += "…"
            with st.expander(label):
                detail_col, status_col = st.columns([3, 1])
                detail_col.markdown(f"**Workflow ID**  \n`{task['task_id']}`")
                status_col.markdown(f"**Status**  \n{task['status'].title()}")
                st.caption(f"Created · {task['created_at'][:19]}")
    else:
        st.info("No workflows yet. Upload documents to begin your first analysis.")
except Exception:
    st.warning("Could not fetch workflows. Check that the API is running.")

st.subheader("Get started")
q1, q2, q3 = st.columns(3)
with q1:
    with st.container(border=True):
        st.markdown("**Add your source documents**")
        st.caption("Upload proposals, reports, and other business files.")
        st.page_link("pages/1_upload_documents.py", label="Open document library")
with q2:
    with st.container(border=True):
        st.markdown("**Start an AI workflow**")
        st.caption("Ask the agents to analyze, summarize, or compare.")
        st.page_link("pages/2_chat.py", label="Open AI workspace")
with q3:
    with st.container(border=True):
        st.markdown("**Review completed work**")
        st.caption("Explore findings and download polished reports.")
        st.page_link("pages/4_results_reports.py", label="View results")
