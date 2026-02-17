"""
🏁 Document Processing Benchmark — Streamlit App

Compare Azure Content Understanding vs Document Intelligence + GPT vs Mistral AI
on your own documents. Upload, pick a model, and get side-by-side results.
"""

import os
import sys
import json
import time
import streamlit as st
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── Make sure our package is importable ────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

from config import PREBUILT_ANALYZERS, SUPPORTED_EXTENSIONS
from utils.comparison import (
    build_comparison_table,
    build_field_comparison,
    compute_summary_stats,
    get_mime_type,
)

# ═══════════════════════════════════════════════════════════════════════
# Page config
# ═══════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="📄 Doc Processing Benchmark",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ──────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    .main .block-container { max-width: 1400px; padding-top: 2rem; }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px; padding: 1.2rem; color: white;
        text-align: center; margin-bottom: 0.5rem;
    }
    .metric-card h3 { margin: 0; font-size: 1.8rem; }
    .metric-card p  { margin: 0; font-size: 0.85rem; opacity: 0.85; }
    .pipeline-header {
        padding: 0.6rem 1rem; border-radius: 8px; font-weight: 600;
        margin-bottom: 0.8rem; font-size: 1.1rem;
    }
    .cu-header  { background: #e3f2fd; color: #1565c0; }
    .di-header  { background: #e8f5e9; color: #2e7d32; }
    .mis-header { background: #fff3e0; color: #e65100; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ═══════════════════════════════════════════════════════════════════════
# Sidebar
# ═══════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.image(
        "https://img.icons8.com/fluency/96/compare.png",
        width=64,
    )
    st.title("⚙️ Settings")

    st.subheader("1️⃣  Prebuilt Model")
    analyzer_id = st.selectbox(
        "Content Understanding analyzer",
        options=list(PREBUILT_ANALYZERS.keys()),
        format_func=lambda x: PREBUILT_ANALYZERS[x],
        help="This model is used by **Azure Content Understanding** and **Document Intelligence**.",
    )

    st.subheader("2️⃣  Pipelines to Run")
    run_cu = st.checkbox("🔵 Azure Content Understanding", value=True)
    run_di = st.checkbox("🟢 Document Intelligence + GPT-5", value=True)
    run_mi = st.checkbox("🟠 Mistral Doc AI (OCR)", value=True)

    st.divider()
    st.caption(
        "All three pipelines run **in parallel** for maximum speed. "
        "Results are compared side-by-side."
    )
    st.divider()
    st.caption("Built for the Azure Content Understanding benchmark project.")

# ═══════════════════════════════════════════════════════════════════════
# Lazy-load services (cached so they're only initialized once)
# ═══════════════════════════════════════════════════════════════════════
@st.cache_resource(show_spinner="🔌 Connecting to Azure Content Understanding…")
def get_cu_service():
    from services.content_understanding import ContentUnderstandingService
    return ContentUnderstandingService()


@st.cache_resource(show_spinner="🔌 Connecting to Document Intelligence + GPT…")
def get_di_service():
    from services.doc_intel_gpt import DocIntelGPTService
    return DocIntelGPTService()


@st.cache_resource(show_spinner="🔌 Connecting to Mistral Doc AI…")
def get_mi_service():
    from services.mistral_vision import MistralVisionService
    return MistralVisionService()


# ═══════════════════════════════════════════════════════════════════════
# Header
# ═══════════════════════════════════════════════════════════════════════
st.title("📄 Document Processing Benchmark")
st.markdown(
    "Compare **Azure Content Understanding**, **Document Intelligence + GPT-5**, "
    "and **Mistral Doc AI** on your documents — all at once."
)

# ═══════════════════════════════════════════════════════════════════════
# File Upload
# ═══════════════════════════════════════════════════════════════════════
uploaded_files = st.file_uploader(
    "📂  Upload one or more documents",
    type=[e.lstrip(".") for e in SUPPORTED_EXTENSIONS],
    accept_multiple_files=True,
    help="Supported: JPG, PNG, BMP, TIFF, PDF",
)

if not uploaded_files:
    st.info("👆 Upload documents to get started.")
    st.stop()

# ═══════════════════════════════════════════════════════════════════════
# Preview uploaded docs
# ═══════════════════════════════════════════════════════════════════════
with st.expander(f"📎 Uploaded documents ({len(uploaded_files)})", expanded=False):
    cols = st.columns(min(len(uploaded_files), 5))
    for idx, f in enumerate(uploaded_files):
        with cols[idx % len(cols)]:
            if f.type and f.type.startswith("image"):
                st.image(f, caption=f.name, use_container_width=True)
            else:
                st.write(f"📄 {f.name} ({f.size / 1024:.0f} KB)")

# ═══════════════════════════════════════════════════════════════════════
# 🚀 Run Benchmark
# ═══════════════════════════════════════════════════════════════════════
if st.button("🚀  Run Benchmark", type="primary", use_container_width=True):
    if not any([run_cu, run_di, run_mi]):
        st.error("Please select at least one pipeline in the sidebar.")
        st.stop()

    all_doc_results = []
    progress = st.progress(0, text="Starting benchmark…")
    total_tasks = len(uploaded_files)

    for file_idx, uploaded_file in enumerate(uploaded_files):
        file_bytes = uploaded_file.getvalue()
        filename = uploaded_file.name
        mime = get_mime_type(filename)

        st.divider()
        st.subheader(f"📄 {filename}")

        # Show document preview
        preview_col, results_col = st.columns([1, 3])
        with preview_col:
            if mime.startswith("image"):
                st.image(file_bytes, caption=filename, use_container_width=True)
            else:
                st.write(f"📄 {filename} ({len(file_bytes) / 1024:.0f} KB)")

        # ── Run pipelines in parallel ───────────────────────────────────
        results = {}
        futures = {}
        with ThreadPoolExecutor(max_workers=3) as executor:
            if run_cu:
                svc = get_cu_service()
                futures[
                    executor.submit(svc.analyze, file_bytes, filename, analyzer_id, mime)
                ] = "🔵 Content Understanding"
            if run_di:
                svc = get_di_service()
                futures[
                    executor.submit(svc.analyze, file_bytes, filename, analyzer_id, mime)
                ] = "🟢 DocIntel + GPT-5"
            if run_mi:
                svc = get_mi_service()
                futures[
                    executor.submit(svc.analyze, file_bytes, filename, mime)
                ] = "🟠 Mistral Doc AI"

            with results_col:
                status_placeholder = st.empty()
                status_placeholder.info(
                    f"⏳ Running {len(futures)} pipeline(s) in parallel…"
                )

            for future in as_completed(futures):
                pipeline_name = futures[future]
                try:
                    results[pipeline_name] = future.result()
                except Exception as e:
                    results[pipeline_name] = {
                        "status": "error",
                        "error": str(e),
                        "time_seconds": 0,
                    }

        with results_col:
            status_placeholder.success(
                f"✅ All pipelines completed for {filename}"
            )

        # ── Metric cards ────────────────────────────────────────────────
        metric_cols = st.columns(len(results))
        for col, (pname, res) in zip(metric_cols, results.items()):
            with col:
                t = res.get("time_seconds", "—")
                fv = res.get("fields_with_values", 0)
                conf = res.get("avg_confidence")
                conf_str = f"{conf:.1%}" if conf else "N/A"
                st.markdown(
                    f"""<div class="metric-card">
                    <p>{pname}</p>
                    <h3>{t}s</h3>
                    <p>⏱ Time</p>
                    </div>""",
                    unsafe_allow_html=True,
                )
                st.metric("Fields extracted", fv)
                st.metric("Avg confidence", conf_str)

        # ── Comparison table ────────────────────────────────────────────
        st.markdown("#### 📊 Pipeline Comparison")
        comp_rows = build_comparison_table(results)
        if comp_rows:
            st.dataframe(pd.DataFrame(comp_rows), use_container_width=True, hide_index=True)

        # ── Field-by-field comparison ───────────────────────────────────
        field_comp = build_field_comparison(results)
        if field_comp:
            st.markdown("#### 🔍 Field-by-Field Comparison")
            df_fields = pd.DataFrame(field_comp).T
            df_fields.index.name = "Field"
            st.dataframe(df_fields, use_container_width=True)

        # ── Detailed outputs (tabs) ─────────────────────────────────────
        st.markdown("#### 📝 Detailed Outputs")
        tabs = st.tabs(list(results.keys()))
        for tab, (pname, res) in zip(tabs, results.items()):
            with tab:
                if res.get("status") == "error":
                    st.error(f"❌ Error: {res.get('error', 'Unknown error')}")
                    continue

                # GPT / Mistral description
                desc = res.get("gpt_description") or res.get("mistral_description")
                if desc:
                    st.markdown("**🤖 AI Description:**")
                    st.info(desc)

                # Markdown output
                md = res.get("markdown", "")
                if md:
                    with st.expander("📄 Markdown output", expanded=False):
                        st.code(md[:3000], language="markdown")

                # Raw fields
                fields = res.get("fields", {})
                if fields:
                    with st.expander(f"📋 Extracted fields ({len(fields)})", expanded=False):
                        st.json(fields)

                # Errors / warnings
                errs = res.get("errors")
                if errs:
                    for e in errs:
                        st.warning(e)

        # Store for batch summary
        all_doc_results.append({"filename": filename, "results": results})
        progress.progress(
            (file_idx + 1) / total_tasks,
            text=f"Processed {file_idx + 1}/{total_tasks} documents",
        )

    # ═══════════════════════════════════════════════════════════════════
    # 📈 Batch Summary (if multiple docs)
    # ═══════════════════════════════════════════════════════════════════
    if len(all_doc_results) > 1:
        st.divider()
        st.header("📈 Batch Summary")
        summary = compute_summary_stats(all_doc_results)
        if summary:
            st.dataframe(
                pd.DataFrame(summary).T.rename_axis("Pipeline"),
                use_container_width=True,
            )

        # Chart: time comparison
        st.markdown("#### ⏱ Processing Time per Document")
        chart_data = []
        for doc in all_doc_results:
            for pipeline, res in doc["results"].items():
                chart_data.append(
                    {
                        "Document": doc["filename"],
                        "Pipeline": pipeline,
                        "Time (s)": res.get("time_seconds", 0),
                    }
                )
        if chart_data:
            df_chart = pd.DataFrame(chart_data)
            st.bar_chart(
                df_chart.pivot(index="Document", columns="Pipeline", values="Time (s)")
            )

    # ── Download results ────────────────────────────────────────────────
    st.divider()
    results_json = json.dumps(all_doc_results, indent=2, ensure_ascii=False, default=str)
    st.download_button(
        "📥 Download Full Results (JSON)",
        data=results_json,
        file_name="benchmark_results.json",
        mime="application/json",
        use_container_width=True,
    )

    st.balloons()
