"""
Mistral Doc AI — Azure-hosted OCR + chat service.
Uses the Azure AI Services Mistral OCR endpoint for extraction and the
Mistral chat completions endpoint for LLM summarisation.
Auth: DefaultAzureCredential (key auth disabled on this resource).
"""

import time
import base64
import re
import requests
from urllib.parse import urlparse
from azure.identity import DefaultAzureCredential
from config import MISTRAL_DOC_AI_ENDPOINT, MISTRAL_DOC_AI_KEY, MISTRAL_DOC_AI_MODEL


class MistralVisionService:
    """Analyse documents with Azure-hosted Mistral Document AI (OCR + summary)."""

    def __init__(self):
        self.ocr_endpoint = MISTRAL_DOC_AI_ENDPOINT
        self.api_key = MISTRAL_DOC_AI_KEY
        self.model = MISTRAL_DOC_AI_MODEL

        # Derive the chat completions endpoint from the OCR endpoint base URL
        parsed = urlparse(self.ocr_endpoint)
        self.chat_endpoint = (
            f"{parsed.scheme}://{parsed.netloc}/models/chat/completions"
        )

        # Entra ID auth (key auth is disabled on this resource)
        self.credential = DefaultAzureCredential()
        self._token = self.credential.get_token(
            "https://cognitiveservices.azure.com/.default"
        )

    def _get_bearer_token(self) -> str:
        """Get or refresh Entra ID bearer token."""
        if time.time() > self._token.expires_on - 120:
            self._token = self.credential.get_token(
                "https://cognitiveservices.azure.com/.default"
            )
        return self._token.token

    def _mistral_summarize(self, ocr_text: str, filename: str) -> str:
        """Send OCR-extracted text back to Mistral Doc AI (chat) for a summary."""
        body = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an expert document analysis assistant. "
                        "Given OCR-extracted text from a document, provide a "
                        "concise structured summary."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f'Here is the OCR text extracted from "{filename}":\n\n'
                        f"{ocr_text[:4000]}\n\n"
                        "Provide: document type, issuer, recipient, total amount, "
                        "date, and any key information. Be concise (3-5 sentences)."
                    ),
                },
            ],
            "max_tokens": 400,
            "temperature": 0.3,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._get_bearer_token()}",
        }
        r = requests.post(
            self.chat_endpoint, headers=headers, json=body, timeout=120
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()

    def analyze(
        self,
        file_bytes: bytes,
        filename: str,
        mime: str = "image/jpeg",
    ) -> dict:
        """
        Send the document to Mistral Doc AI OCR, then GPT-5 for summary.
        Returns a result dict consistent with the other services.
        """
        t0 = time.time()
        errors = []
        full_markdown = ""
        fields = {}

        # ── Step 1: Mistral OCR ─────────────────────────────────────────
        try:
            b64 = base64.b64encode(file_bytes).decode("utf-8")

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._get_bearer_token()}",
            }

            body = {
                "model": self.model,
                "document": {
                    "type": "document_url",
                    "document_url": f"data:{mime};base64,{b64}",
                },
            }

            r = requests.post(
                self.ocr_endpoint, headers=headers, json=body, timeout=120
            )
            r.raise_for_status()
            result = r.json()

            # Extract markdown from pages
            pages = result.get("pages", [])
            markdown_parts = [p.get("markdown", "") for p in pages]
            full_markdown = "\n\n".join(markdown_parts)

            # Parse structured fields from the OCR markdown
            fields = self._parse_fields(full_markdown)

        except Exception as e:
            errors.append(f"Mistral OCR: {e}")

        # ── Step 2: Mistral Doc AI LLM Summary ─────────────────────────
        gpt_description = ""
        if full_markdown:
            try:
                gpt_description = self._mistral_summarize(full_markdown, filename)
            except Exception as e:
                errors.append(f"Mistral Summary: {e}")

        dt = round(time.time() - t0, 2)
        return {
            "status": "success" if not errors else ("partial" if full_markdown else "error"),
            "time_seconds": dt,
            "markdown": full_markdown,
            "fields": fields,
            "field_count": len(fields),
            "fields_with_values": len(fields),
            "tables_count": full_markdown.count("<table>") + full_markdown.count("| "),
            "avg_confidence": None,
            "gpt_description": gpt_description,
            "errors": errors if errors else None,
        }

    @staticmethod
    def _parse_fields(text: str) -> dict:
        """
        Best-effort extraction of key-value pairs from OCR markdown.
        """
        fields = {}
        pattern = re.compile(
            r"(?:^|\n)\s*[-•*]*\s*\*{0,2}([A-Za-z /]+?)\*{0,2}\s*:\s*(.+)",
            re.MULTILINE,
        )
        for m in pattern.finditer(text):
            key = m.group(1).strip()
            val = m.group(2).strip()
            if key and val and len(key) < 40:
                fields[key] = val
        return fields
