import streamlit as st
import requests
import pandas as pd
from ui import apply_theme, page_header

API_BASE = "http://localhost:8000"

st.set_page_config(page_title="Results & Reports | Nexa AI", page_icon="✦", layout="wide")
apply_theme()
page_header(
    "Results and reports",
    "Review AI-generated findings, compare options, and export your deliverables.",
    "INSIGHTS",
)

try:
    all_tasks = requests.get(f"{API_BASE}/tasks/", timeout=5).json()
    completed_tasks = [
        task for task in all_tasks if task["status"] == "completed"
    ]
except Exception as error:
    st.error(f"Cannot connect to the API: {error}")
    st.stop()

if not completed_tasks:
    st.info("Completed workflow results will appear here.")
    st.page_link("pages/2_chat.py", label="Start an AI workflow")
    st.stop()

task_options = {
    f"{task['task_type'].title()} · {task['user_instruction'][:60]} · {task['created_at'][:16]}": task[
        "task_id"
    ]
    for task in completed_tasks
}
with st.container(border=True):
    selected_label = st.selectbox(
        "Select a completed workflow", list(task_options.keys())
    )
task_id = task_options[selected_label]

try:
    detail = requests.get(
        f"{API_BASE}/analysis/task/{task_id}/result", timeout=10
    ).json()
except Exception as error:
    st.error(f"Failed to load workflow results: {error}")
    st.stop()

result = detail.get("result", {})
if not result:
    st.warning("No result data is available for this workflow.")
    st.stop()

analysis = result.get("analysis", {})
comparison = result.get("comparison", {})
report = result.get("report", {})

summary_tab, analysis_tab, comparison_tab, downloads_tab = st.tabs(
    ["Executive summary", "Detailed analysis", "Comparison", "Downloads & tools"]
)

with summary_tab:
    st.subheader("Executive summary")
    summary_text = report.get("summary") or analysis.get("summary") or analysis.get("raw", "")
    if summary_text:
        with st.container(border=True):
            st.markdown(summary_text)
    else:
        st.info("No executive summary is available for this workflow.")

    recommendation = report.get("recommendation") or comparison.get("recommendation", "")
    if recommendation:
        st.subheader("Recommendation")
        with st.container(border=True):
            st.markdown(recommendation)

with analysis_tab:
    st.subheader("Detailed analysis")
    analysis_sections = [
        ("Key insights", analysis.get("key_insights"), "info"),
        ("Risks and concerns", analysis.get("risks"), "warning"),
        ("Strengths and trade-offs", analysis.get("pros_cons"), "success"),
        ("Financial and numerical data", analysis.get("numerical_data"), "info"),
    ]
    has_analysis = False
    for title, content, message_type in analysis_sections:
        if content:
            has_analysis = True
            st.markdown(f"#### {title}")
            getattr(st, message_type)(content)

    if analysis.get("raw"):
        with st.expander("View complete analysis output"):
            st.markdown(analysis["raw"])
    if not has_analysis and not analysis.get("raw"):
        st.info("No detailed analysis is available.")

with comparison_tab:
    st.subheader("Comparison")
    comparison_table = comparison.get("comparison_table", [])
    if comparison_table:
        st.dataframe(
            pd.DataFrame(comparison_table),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No comparison table is available for this workflow.")

    if comparison.get("strengths_weaknesses"):
        st.markdown("#### Strengths and weaknesses")
        st.markdown(comparison["strengths_weaknesses"])

    if comparison.get("risk_assessment"):
        st.markdown("#### Risk assessment")
        st.warning(comparison["risk_assessment"])

    documents_compared = comparison.get("documents_compared", [])
    if documents_compared:
        st.caption(f"Documents compared · {', '.join(documents_compared)}")

    if comparison.get("raw"):
        with st.expander("View complete comparison output"):
            st.markdown(comparison["raw"])

with downloads_tab:
    st.subheader("Export reports")
    pdf_col, excel_col = st.columns(2)
    with pdf_col:
        st.markdown("**PDF report**")
        pdf_url = f"{API_BASE}/analysis/task/{task_id}/download/pdf"
        try:
            pdf_check = requests.head(pdf_url, timeout=5)
            if pdf_check.status_code == 200:
                pdf_bytes = requests.get(pdf_url, timeout=15).content
                st.download_button(
                    label="Download PDF",
                    data=pdf_bytes,
                    file_name=f"report_{task_id[:8]}.pdf",
                    mime="application/pdf",
                    type="primary",
                )
            else:
                st.caption("PDF report is not available.")
        except Exception as error:
            st.warning(f"PDF report is not available: {error}")

    with excel_col:
        st.markdown("**Excel report**")
        excel_url = f"{API_BASE}/analysis/task/{task_id}/download/excel"
        try:
            excel_check = requests.head(excel_url, timeout=5)
            if excel_check.status_code == 200:
                excel_bytes = requests.get(excel_url, timeout=15).content
                st.download_button(
                    label="Download Excel",
                    data=excel_bytes,
                    file_name=f"report_{task_id[:8]}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary",
                )
            else:
                st.caption("Excel report is not available.")
        except Exception as error:
            st.warning(f"Excel report is not available: {error}")

    st.subheader("Business calculators")
    with st.expander("Open calculator and total cost of ownership"):
        expression = st.text_input(
            "Expression", placeholder="For example: 1200 * 3 + 500", key="calc_expr"
        )
        if st.button("Calculate"):
            try:
                response = requests.post(
                    f"{API_BASE}/analysis/calculate",
                    json={"expression": expression},
                    timeout=5,
                ).json()
                st.success(f"Result: {response['result']}")
            except Exception as error:
                st.error(str(error))

        st.markdown("**Total cost of ownership**")
        cost_col, maintenance_col, years_col = st.columns(3)
        initial_cost = cost_col.number_input(
            "Initial cost ($)", min_value=0.0, value=10000.0
        )
        annual_maintenance = maintenance_col.number_input(
            "Annual maintenance ($)", min_value=0.0, value=2000.0
        )
        years = years_col.number_input("Years", min_value=1, max_value=20, value=3)
        if st.button("Calculate total cost"):
            try:
                response = requests.post(
                    f"{API_BASE}/analysis/tco",
                    json={
                        "initial": initial_cost,
                        "annual_maintenance": annual_maintenance,
                        "years": int(years),
                        "other_costs": 0,
                    },
                    timeout=5,
                ).json()
                st.success(
                    f"Total cost · ${response['total_tco']:,.2f} over {years} year(s)"
                )
            except Exception as error:
                st.error(str(error))
