"""
Azure Document Intelligence + GPT-5-chat Vision pipeline.
Step 1: Extract document with Doc Intelligence SDK.
Step 2: Send image to GPT-5-chat Vision for a rich LLM summary.
Auth: Doc Intelligence uses API key; GPT-5 uses DefaultAzureCredential
      (key auth is disabled on the content-understanding resource).
"""

import io
import time
import base64
import requests
from azure.identity import DefaultAzureCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from config import (
    DOC_INTEL_ENDPOINT,
    DOC_INTEL_KEY,
    GPT_ENDPOINT,
)


class DocIntelGPTService:
    """Document Intelligence extraction + GPT-5-chat Vision description."""

    def __init__(self):
        self.di_client = DocumentIntelligenceClient(
            endpoint=DOC_INTEL_ENDPOINT,
            credential=AzureKeyCredential(DOC_INTEL_KEY),
        )
        # Entra ID auth for GPT-5 (key auth disabled on this resource)
        self.credential = DefaultAzureCredential()
        self._token = self.credential.get_token(
            "https://cognitiveservices.azure.com/.default"
        )

    def _get_bearer_token(self) -> str:
        if time.time() > self._token.expires_on - 120:
            self._token = self.credential.get_token(
                "https://cognitiveservices.azure.com/.default"
            )
        return self._token.token

    # ── GPT-5-chat Vision call ──────────────────────────────────────────
    def _gpt_describe(self, file_bytes: bytes, filename: str, mime: str) -> str:
        b64 = base64.b64encode(file_bytes).decode("utf-8")
        body = {
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an expert document analysis assistant. "
                        "You analyse scanned documents (invoices, quotes, purchase orders, etc.) "
                        "and provide a concise structured description."
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                f'Analyse this document image "{filename}". '
                                "Provide: document type, issuer, recipient, total amount, "
                                "date, and any key information. Be concise (3-5 sentences)."
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime};base64,{b64}",
                                "detail": "high",
                            },
                        },
                    ],
                },
            ],
            "max_tokens": 400,
            "temperature": 0.3,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._get_bearer_token()}",
        }
        r = requests.post(GPT_ENDPOINT, headers=headers, json=body, timeout=120)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()

    # ── Public API ──────────────────────────────────────────────────────
    def analyze(
        self,
        file_bytes: bytes,
        filename: str,
        model_id: str = "prebuilt-invoice",
        mime: str = "image/jpeg",
    ) -> dict:
        """
        Run Doc Intelligence + GPT-5 Vision on a document.
        Returns a result dict similar to Content Understanding's output.
        """
        t0 = time.time()
        errors = []

        # ── Step 1: Document Intelligence ───────────────────────────────
        di_result = {}
        di_fields = {}
        di_markdown = ""
        di_tables = 0
        di_confidence = None
        try:
            poller = self.di_client.begin_analyze_document(
                model_id,
                body=io.BytesIO(file_bytes),
                content_type="application/octet-stream",
            )
            result = poller.result()

            # Extract markdown / content
            di_markdown = result.content or ""

            # Extract fields
            if result.documents:
                for doc in result.documents:
                    if doc.fields:
                        for k, v in doc.fields.items():
                            if v and v.content:
                                di_fields[k] = v.content
                            elif v and v.value:
                                di_fields[k] = v.value

            # Tables
            di_tables = len(result.tables) if result.tables else 0

            # Average confidence
            confs = []
            if result.documents:
                for doc in result.documents:
                    if doc.confidence is not None:
                        confs.append(doc.confidence)
                    if doc.fields:
                        for v in doc.fields.values():
                            if v and v.confidence is not None:
                                confs.append(v.confidence)
            di_confidence = round(sum(confs) / len(confs), 4) if confs else None

            di_result = {
                "content": di_markdown[:2000],
                "fields": di_fields,
                "tables_count": di_tables,
                "avg_confidence": di_confidence,
            }
        except Exception as e:
            errors.append(f"DocIntel: {e}")

        # ── Step 2: GPT-5-chat Vision ───────────────────────────────────
        gpt_description = ""
        try:
            gpt_description = self._gpt_describe(file_bytes, filename, mime)
        except Exception as e:
            errors.append(f"GPT Vision: {e}")

        dt = round(time.time() - t0, 2)
        return {
            "status": "success" if not errors else "partial",
            "time_seconds": dt,
            "markdown": di_markdown,
            "fields": di_fields,
            "field_count": len(di_fields),
            "fields_with_values": len(di_fields),
            "tables_count": di_tables,
            "avg_confidence": di_confidence,
            "gpt_description": gpt_description,
            "errors": errors if errors else None,
            "di_detail": di_result,
        }
