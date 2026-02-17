"""
Azure Content Understanding service — prebuilt analyzers.
Uses Azure AD (DefaultAzureCredential) + Blob Storage for URL-based input.
After extraction, sends image to GPT-4 for a structured LLM summary.
"""

import os
import time
import json
import base64
import requests
from datetime import datetime, timedelta, timezone
from azure.identity import DefaultAzureCredential
from azure.storage.blob import (
    BlobServiceClient,
    generate_blob_sas,
    BlobSasPermissions,
)
from config import CU_ENDPOINT, CU_API_VERSION, STORAGE_ACCOUNT, STORAGE_CONTAINER
from config import GPT4_ENDPOINT


class ContentUnderstandingService:
    """Wraps Azure Content Understanding REST API with blob-based input."""

    def __init__(self):
        self.endpoint = CU_ENDPOINT
        self.api_version = CU_API_VERSION
        self.credential = DefaultAzureCredential()
        self._token = self.credential.get_token(
            "https://cognitiveservices.azure.com/.default"
        )

        # Blob storage for temp uploads
        self.blob_service = BlobServiceClient(
            f"https://{STORAGE_ACCOUNT}.blob.core.windows.net",
            credential=self.credential,
        )
        udk_start = datetime.now(timezone.utc)
        udk_expiry = udk_start + timedelta(hours=2)
        self._udk = self.blob_service.get_user_delegation_key(udk_start, udk_expiry)
        self._udk_expiry = udk_expiry

    # ── Auth header (auto-refresh) ──────────────────────────────────────
    def _auth(self):
        if time.time() > self._token.expires_on - 120:
            self._token = self.credential.get_token(
                "https://cognitiveservices.azure.com/.default"
            )
        return {"Authorization": f"Bearer {self._token.token}"}

    # ── Upload to blob and return SAS URL ───────────────────────────────
    def _upload_blob(self, file_bytes: bytes, filename: str) -> str:
        blob_client = self.blob_service.get_blob_client(STORAGE_CONTAINER, filename)
        blob_client.upload_blob(file_bytes, overwrite=True)
        sas = generate_blob_sas(
            account_name=STORAGE_ACCOUNT,
            container_name=STORAGE_CONTAINER,
            blob_name=filename,
            user_delegation_key=self._udk,
            permission=BlobSasPermissions(read=True),
            expiry=self._udk_expiry,
        )
        return f"https://{STORAGE_ACCOUNT}.blob.core.windows.net/{STORAGE_CONTAINER}/{filename}?{sas}"

    # ── Submit analysis ─────────────────────────────────────────────────
    def _submit(self, file_bytes: bytes, filename: str, analyzer_id: str) -> str:
        blob_url = self._upload_blob(file_bytes, filename)
        url = f"{self.endpoint}/contentunderstanding/analyzers/{analyzer_id}:analyze?api-version={self.api_version}"
        r = requests.post(
            url,
            headers={**self._auth(), "Content-Type": "application/json"},
            json={"inputs": [{"url": blob_url}]},
        )
        if r.status_code != 202:
            raise RuntimeError(f"{r.status_code}: {r.text[:500]}")
        return r.headers["Operation-Location"]

    # ── Poll for result ─────────────────────────────────────────────────
    def _poll(self, op_url: str, timeout: int = 300) -> dict:
        for i in range(timeout // 5):
            time.sleep(5)
            r = requests.get(op_url, headers=self._auth())
            r.raise_for_status()
            res = r.json()
            status = res.get("status", "")
            if status == "Succeeded":
                return res
            if status in ("Failed", "Canceled"):
                raise RuntimeError(json.dumps(res.get("error", res), indent=2))
        raise TimeoutError("Content Understanding timed out")

    # ── GPT-4 LLM summary (vision) ─────────────────────────────────────
    def _gpt4_describe(self, file_bytes: bytes, filename: str, mime: str) -> str:
        """Send the document image to GPT-4 Vision for a structured summary."""
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
            "Authorization": f"Bearer {self._auth()['Authorization'].split(' ')[1]}",
        }
        r = requests.post(GPT4_ENDPOINT, headers=headers, json=body, timeout=120)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()

    # ── Public API ──────────────────────────────────────────────────────
    def analyze(self, file_bytes: bytes, filename: str, analyzer_id: str,
                mime: str = "image/jpeg") -> dict:
        """
        Full pipeline: upload → submit → poll → return result dict.
        Returns:
            {
                "status": "success" | "error",
                "time_seconds": float,
                "raw_result": {...},
                "markdown": str,
                "fields": dict,           # flat extracted field values
                "field_count": int,
                "tables_count": int,
                "avg_confidence": float | None,
            }
        """
        t0 = time.time()
        try:
            op_url = self._submit(file_bytes, filename, analyzer_id)
            raw = self._poll(op_url)

            contents = raw.get("result", {}).get("contents", [])
            block = contents[0] if contents else {}
            fields = block.get("fields", {})
            md = block.get("markdown", "")

            # Flatten field values
            flat = self._extract_field_values(fields)

            # Compute average confidence
            confs = []
            self._collect_confidences(fields, confs)
            avg_conf = round(sum(confs) / len(confs), 4) if confs else None

            # GPT-4 LLM summary
            gpt_description = ""
            gpt_errors = []
            try:
                gpt_description = self._gpt4_describe(file_bytes, filename, mime)
            except Exception as e:
                gpt_errors.append(f"GPT-4 Summary: {e}")

            dt = round(time.time() - t0, 2)
            return {
                "status": "success" if not gpt_errors else "partial",
                "time_seconds": dt,
                "raw_result": raw,
                "markdown": md,
                "fields": flat,
                "field_count": len(fields),
                "fields_with_values": len(flat),
                "tables_count": len(block.get("tables", [])),
                "avg_confidence": avg_conf,
                "gpt_description": gpt_description,
                "errors": gpt_errors if gpt_errors else None,
            }
        except Exception as e:
            return {
                "status": "error",
                "time_seconds": round(time.time() - t0, 2),
                "error": str(e),
            }

    # ── Helpers ──────────────────────────────────────────────────────────
    @staticmethod
    def _extract_field_values(fields_dict: dict) -> dict:
        result = {}
        for name, obj in fields_dict.items():
            if not isinstance(obj, dict):
                continue
            if set(obj.keys()) <= {"type", "valueObject"} and "valueObject" in obj:
                sub = ContentUnderstandingService._extract_field_values(obj["valueObject"])
                if sub:
                    result[name] = sub
            elif set(obj.keys()) <= {"type"}:
                continue
            else:
                val = (
                    obj.get("valueString")
                    or obj.get("valueNumber")
                    or obj.get("valueDate")
                    or obj.get("content")
                    or obj.get("value")
                )
                if val is not None:
                    result[name] = val
                elif "valueObject" in obj:
                    sub = ContentUnderstandingService._extract_field_values(
                        obj["valueObject"]
                    )
                    if sub:
                        result[name] = sub
                elif "valueArray" in obj:
                    arr = []
                    for item in obj["valueArray"]:
                        if isinstance(item, dict) and "valueObject" in item:
                            sub = ContentUnderstandingService._extract_field_values(
                                item["valueObject"]
                            )
                            if sub:
                                arr.append(sub)
                        elif isinstance(item, dict):
                            v = (
                                item.get("valueString")
                                or item.get("content")
                                or item.get("value")
                            )
                            if v:
                                arr.append(v)
                    if arr:
                        result[name] = arr
        return result

    @staticmethod
    def _collect_confidences(obj, confs: list):
        if isinstance(obj, dict):
            if "confidence" in obj:
                confs.append(obj["confidence"])
            for v in obj.values():
                ContentUnderstandingService._collect_confidences(v, confs)
        elif isinstance(obj, list):
            for x in obj:
                ContentUnderstandingService._collect_confidences(x, confs)
