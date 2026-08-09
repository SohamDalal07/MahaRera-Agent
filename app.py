import sys
import re
sys.modules['regex'] = re

import json
import streamlit as st
from project.analyze import analyze_agreement, save_report, save_markdown_report

st.set_page_config(
    page_title="MahaRERA Compliance Dashboard",
)

st.title("MahaRERA Compliance Dashboard")
st.write("Upload an agreement PDF and analyze it for MahaRERA compliance.")

uploaded_file = st.file_uploader("Upload Builder Agreement PDF", type=["pdf"])

if uploaded_file is not None:
    with open("uploads/agreement.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())

    if st.button("Analyze"):
        with st.spinner("Analyzing agreement..."):
            results = analyze_agreement("uploads/agreement.pdf")

        compliant = sum(1 for r in results if r.get("status") == "Compliant")
        non_compliant = sum(1 for r in results if r.get("status") == "Non-Compliant")
        needs_review = sum(1 for r in results if r.get("status") == "Needs Review")

        st.success("Analysis complete")
        st.markdown(f"- ✅ {compliant} Clauses Compliant")
        st.markdown(f"- ❌ {non_compliant} Clauses Non-Compliant")
        st.markdown(f"- ⚠️ {needs_review} Clauses Need Review")

        json_report = json.dumps(results, indent=2, ensure_ascii=False)
        markdown_report = save_markdown_report(results, path="uploads/report.md")
        save_report(results, path="uploads/report.json")

        st.download_button(
            label="Download JSON report",
            data=json_report,
            file_name="maharera_report.json",
            mime="application/json",
        )

        st.download_button(
            label="Download Markdown report",
            data=markdown_report,
            file_name="maharera_report.md",
            mime="text/markdown",
        )

        st.markdown("---")

        for idx, item in enumerate(results, start=1):
            title = f"Clause {idx}: {item.get('status', 'Unknown')} ({item.get('confidence', 0)}%)"
            with st.expander(title):
                st.markdown("**Clause**")
                st.write(item.get("clause", ""))
                st.markdown("**Reason**")
                st.write(item.get("reason", ""))
                st.markdown("**Recommendation**")
                st.write(item.get("recommendation", ""))
                st.markdown("**Citations**")
                for cite in item.get("citations", []):
                    st.markdown(
                        f"- {cite.get('document', 'Unknown')} (Page {cite.get('page', 'N/A')})"
                    )
