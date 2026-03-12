import re
from dataclasses import dataclass
from typing import Any


ARXIV_ID_PATTERN = re.compile(
    r"(?:arxiv\.org/(?:abs|pdf|html)/)(?P<id>\d{4}\.\d{4,5}v?\d*)"
)


@dataclass(frozen=True)
class ArxivResource:
    arxiv_id: str
    pdf_url: str


def normalize_arxiv_url(url: Any) -> ArxivResource:
    url_str = str(url)
    match = ARXIV_ID_PATTERN.search(url_str)
    if not match:
        raise ValueError("Invalid arXiv URL. Expected abs/html/pdf URL with a valid arXiv id.")
    arxiv_id = match.group("id")
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    return ArxivResource(arxiv_id=arxiv_id, pdf_url=pdf_url)
