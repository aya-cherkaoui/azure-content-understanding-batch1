"""
Comparison & metrics utilities for benchmark results.
"""

import json


def build_comparison_table(results: dict) -> list[dict]:
    """
    Build a comparison table from the results of all pipelines.

    Args:
        results: {"Content Understanding": {...}, "DocIntel + GPT": {...}, "Mistral AI": {...}}

    Returns:
        List of dicts suitable for display in a Streamlit dataframe.
    """
    rows = []
    for pipeline_name, res in results.items():
        if res is None:
            continue
        row = {
            "Pipeline": pipeline_name,
            "Status": res.get("status", "N/A"),
            "Time (s)": res.get("time_seconds", "N/A"),
            "Fields Extracted": res.get("fields_with_values", 0),
            "Total Fields": res.get("field_count", 0),
            "Tables Detected": res.get("tables_count", 0),
            "Avg Confidence": res.get("avg_confidence", "N/A"),
            "Markdown Length": len(res.get("markdown", "")),
        }
        rows.append(row)
    return rows


def build_field_comparison(results: dict) -> dict:
    """
    Build a field-by-field comparison across pipelines.

    Returns:
        { field_name: { pipeline_name: value, ... }, ... }
    """
    all_fields = set()
    for res in results.values():
        if res and "fields" in res:
            all_fields.update(res["fields"].keys())

    comparison = {}
    for field in sorted(all_fields):
        comparison[field] = {}
        for pipeline_name, res in results.items():
            if res and "fields" in res:
                val = res["fields"].get(field, "—")
                # Truncate long values for display
                if isinstance(val, str) and len(val) > 100:
                    val = val[:100] + "…"
                elif isinstance(val, (dict, list)):
                    val = json.dumps(val, ensure_ascii=False)[:100] + "…"
                comparison[field][pipeline_name] = val
            else:
                comparison[field][pipeline_name] = "—"
    return comparison


def compute_summary_stats(all_results: list[dict]) -> dict:
    """
    Compute aggregate stats across multiple documents for each pipeline.

    Args:
        all_results: List of {filename: str, results: {pipeline: result_dict}}

    Returns:
        { pipeline_name: { avg_time, total_fields, success_rate, ... } }
    """
    pipeline_stats = {}
    for doc_result in all_results:
        for pipeline, res in doc_result.get("results", {}).items():
            if pipeline not in pipeline_stats:
                pipeline_stats[pipeline] = {
                    "times": [],
                    "fields": [],
                    "successes": 0,
                    "total": 0,
                    "confidences": [],
                }
            stats = pipeline_stats[pipeline]
            stats["total"] += 1
            if res and res.get("status") in ("success", "partial"):
                stats["successes"] += 1
                stats["times"].append(res.get("time_seconds", 0))
                stats["fields"].append(res.get("fields_with_values", 0))
                if res.get("avg_confidence") is not None:
                    stats["confidences"].append(res["avg_confidence"])

    summary = {}
    for pipeline, s in pipeline_stats.items():
        summary[pipeline] = {
            "success_rate": f"{s['successes']}/{s['total']}",
            "avg_time_s": round(sum(s["times"]) / len(s["times"]), 2) if s["times"] else 0,
            "avg_fields": round(sum(s["fields"]) / len(s["fields"]), 1) if s["fields"] else 0,
            "avg_confidence": (
                round(sum(s["confidences"]) / len(s["confidences"]), 4)
                if s["confidences"]
                else "N/A"
            ),
        }
    return summary


def get_mime_type(filename: str) -> str:
    """Return MIME type based on file extension."""
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    mime_map = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "bmp": "image/bmp",
        "tiff": "image/tiff",
        "tif": "image/tiff",
        "pdf": "application/pdf",
    }
    return mime_map.get(ext, "application/octet-stream")
