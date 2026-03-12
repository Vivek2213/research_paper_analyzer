import httpx


def fetch_pdf(pdf_url: str) -> bytes:
    with httpx.Client(timeout=60.0, follow_redirects=True) as client:
        response = client.get(pdf_url)
        response.raise_for_status()
        return response.content
