from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class GrobidResult:
    tei_xml: str


def process_pdf(pdf_bytes: bytes, grobid_url: str) -> GrobidResult:
    endpoint = f"{grobid_url.rstrip('/')}/api/processFulltextDocument"
    files = {"input": ("paper.pdf", pdf_bytes, "application/pdf")}
    data = {"consolidateCitations": "1"}
    with httpx.Client(timeout=120.0) as client:
        response = client.post(endpoint, files=files, data=data)
        response.raise_for_status()
    return GrobidResult(tei_xml=response.text)
