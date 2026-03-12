import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List
from urllib.parse import quote_plus

import httpx


ARXIV_ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


@dataclass(frozen=True)
class RelatedPaper:
    title: str
    summary: str
    paper_url: str


@dataclass(frozen=True)
class ExternalEvidence:
    novelty_context: str
    fact_check_context: str
    sources: List[str]


def _normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _build_query(title: str, abstract: str) -> str:
    title_terms = re.findall(r"[A-Za-z0-9]{4,}", title.lower())
    abstract_terms = re.findall(r"[A-Za-z0-9]{5,}", abstract.lower())

    keywords = []
    for term in title_terms + abstract_terms:
        if term in keywords:
            continue
        keywords.append(term)
        if len(keywords) == 6:
            break

    if not keywords:
        return quote_plus(title)

    return quote_plus(" AND ".join(f"all:{term}" for term in keywords[:4]))


def _parse_related_papers(feed_xml: str, current_paper_url: str) -> List[RelatedPaper]:
    root = ET.fromstring(feed_xml)
    papers: List[RelatedPaper] = []
    for entry in root.findall("atom:entry", ARXIV_ATOM_NS):
        id_el = entry.find("atom:id", ARXIV_ATOM_NS)
        title_el = entry.find("atom:title", ARXIV_ATOM_NS)
        summary_el = entry.find("atom:summary", ARXIV_ATOM_NS)

        paper_url = _normalize_whitespace(id_el.text if id_el is not None and id_el.text else "")
        if not paper_url or paper_url == current_paper_url:
            continue

        title = _normalize_whitespace(title_el.text if title_el is not None and title_el.text else "")
        summary = _normalize_whitespace(summary_el.text if summary_el is not None and summary_el.text else "")
        if not title or not summary:
            continue

        papers.append(RelatedPaper(title=title, summary=summary[:900], paper_url=paper_url))
    return papers


def _format_related_papers(papers: List[RelatedPaper]) -> str:
    if not papers:
        return "No external literature context could be retrieved."

    lines = []
    for index, paper in enumerate(papers, start=1):
        lines.extend(
            [
                f"[{index}] {paper.title}",
                f"URL: {paper.paper_url}",
                f"Summary: {paper.summary}",
                "",
            ]
        )
    return "\n".join(lines).strip()


def fetch_external_evidence(
    *,
    paper_title: str,
    paper_abstract: str,
    current_paper_url: str,
    max_results: int,
    timeout_seconds: float = 20.0,
) -> ExternalEvidence:
    query = _build_query(paper_title, paper_abstract)
    endpoint = (
        "http://export.arxiv.org/api/query"
        f"?search_query={query}&start=0&max_results={max_results}&sortBy=relevance&sortOrder=descending"
    )

    with httpx.Client(timeout=timeout_seconds, follow_redirects=True) as client:
        response = client.get(endpoint, headers={"User-Agent": "research-paper-analyser/0.1"})
        response.raise_for_status()

    papers = _parse_related_papers(response.text, current_paper_url)
    formatted_context = _format_related_papers(papers)
    return ExternalEvidence(
        novelty_context=formatted_context,
        fact_check_context=formatted_context,
        sources=[paper.paper_url for paper in papers],
    )
