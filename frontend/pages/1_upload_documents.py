import streamlit as st
import requests
from ui import apply_theme, page_header

API_BASE = "http://localhost:8000"

st.set_page_config(page_title="Document Library | Nexa AI", page_icon="✦", layout="wide")
apply_theme()
page_header(
    "Document library",
    "Upload and manage the source files used in your AI workflows.",
    "KNOWLEDGE BASE",
)

st.subheader("Add documents")
st.caption("Supported formats: PDF, Word, text, and common image files.")

with st.container(border=True):
    uploaded_files = st.file_uploader(
        "Select files to upload",
        type=["pdf", "docx", "doc", "txt", "png", "jpg", "jpeg", "tiff"],
        accept_multiple_files=True,
        label_visibility="visible",
    )
    if uploaded_files:
        st.caption(f"{len(uploaded_files)} file(s) selected")
        if st.button("Upload selected files", type="primary"):
            progress = st.progress(0)
            uploaded_ids = []
            for index, file in enumerate(uploaded_files):
                try:
                    response = requests.post(
                        f"{API_BASE}/documents/upload",
                        files={"file": (file.name, file.getvalue(), file.type)},
                        timeout=30,
                    )
                    if response.status_code == 200:
                        data = response.json()
                        uploaded_ids.append(data["doc_id"])
                        st.success(f"{file.name} uploaded successfully.")
                    else:
                        st.error(f"{file.name} could not be uploaded: {response.text}")
                except Exception as error:
                    st.error(f"{file.name} could not be uploaded: {error}")
                progress.progress((index + 1) / len(uploaded_files))

            if uploaded_ids:
                st.session_state["last_uploaded_ids"] = uploaded_ids
                st.info(
                    f"{len(uploaded_ids)} file(s) added. "
                    "Open the AI workspace to start an analysis."
                )

st.subheader("Your documents")
try:
    docs = requests.get(f"{API_BASE}/documents/", timeout=5).json()
    if not docs:
        st.info("Your library is empty. Upload documents to get started.")
    else:
        st.caption(f"{len(docs)} document(s) in your library")
        for doc in docs:
            file_type = doc["file_type"].strip(".").upper()
            with st.expander(f"{doc['filename']}  ·  {file_type}"):
                details_col, status_col, date_col = st.columns(3)
                details_col.markdown(f"**Document ID**  \n`{doc['doc_id']}`")
                status_col.markdown(f"**Status**  \n{doc['status'].title()}")
                date_col.markdown(f"**Uploaded**  \n{doc['created_at'][:19]}")
                if st.button("Delete document", key=f"del_{doc['doc_id']}"):
                    response = requests.delete(
                        f"{API_BASE}/documents/{doc['doc_id']}", timeout=5
                    )
                    if response.status_code == 200:
                        st.success("Document deleted.")
                        st.rerun()
                    else:
                        st.error("Document could not be deleted.")
except Exception as error:
    st.error(f"Could not load the document library: {error}")
