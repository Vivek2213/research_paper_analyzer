import os
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

from research_paper_analyser.agents import build_agent_graph
from research_paper_analyser.config import llm_provider_config
from research_paper_analyser.core.arxiv import ArxivResource, normalize_arxiv_url
from research_paper_analyser.core.chunker import chunk_text, estimate_tokens
from research_paper_analyser.core.fetcher import fetch_pdf
from research_paper_analyser.core.grobid import process_pdf
from research_paper_analyser.core.retrieval import ExternalEvidence, fetch_external_evidence
from research_paper_analyser.core.tei_parser import parse_tei
from research_paper_analyser.services.report import aggregate_section_outputs, build_report
from research_paper_analyser.utils import log_handler


@dataclass(frozen=True)
class AnalysisJob:
    job_id: str
    arxiv_resource: ArxivResource
    output_path: str


def prepare_job(arxiv_url: str) -> AnalysisJob:
    resource = normalize_arxiv_url(arxiv_url)
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    job_id = f"{resource.arxiv_id}-{timestamp}"
    output_dir = llm_provider_config.OUTPUT_DIR
    output_path = os.path.join(output_dir, f"{resource.arxiv_id}.md")
    return AnalysisJob(job_id=job_id, arxiv_resource=resource, output_path=output_path)


def _select_sections(sections: Dict[str, str], full_text: str) -> Dict[str, str]:
    preferred = ["abstract", "method", "methodology", "results", "conclusion"]
    selected: Dict[str, str] = {}
    for name, text in sections.items():
        if any(key in name for key in preferred):
            selected[name] = text
    if not selected:
        selected["full_text"] = full_text
    return selected


def _run_agents_on_chunk(
    chunk_text: str,
    section_name: str,
    external_evidence: ExternalEvidence,
) -> Dict[str, Dict[str, Any]]:
    graph = build_agent_graph()
    state = {
        "chunk_text": chunk_text,
        "section_name": section_name,
        "novelty_context": external_evidence.novelty_context,
        "fact_check_context": external_evidence.fact_check_context,
        "results": {},
    }
    result = graph.invoke(state)
    return result["results"]


def execute_job(job: AnalysisJob) -> None:
    start_time = time.time()
    log_handler.info("Starting job %s for %s", job.job_id, job.arxiv_resource.arxiv_id)
    os.makedirs(llm_provider_config.OUTPUT_DIR, exist_ok=True)

    log_handler.info("Fetching PDF from arXiv")
    pdf_bytes = fetch_pdf(job.arxiv_resource.pdf_url)
    log_handler.info("PDF downloaded (%s bytes). Sending to GROBID", len(pdf_bytes))
    tei = process_pdf(pdf_bytes, llm_provider_config.GROBID_URL)
    log_handler.info("GROBID processing complete. Parsing TEI")
    parsed = parse_tei(tei.tei_xml)
    log_handler.info("Parsed paper: %s", parsed.title)
    sections = _select_sections(parsed.sections, parsed.full_text)
    log_handler.info("Selected %s section(s) for analysis", len(sections))
    abstract_text = parsed.sections.get("abstract", "")

    external_evidence = ExternalEvidence(
        novelty_context="No external literature context available.",
        fact_check_context="No external fact-check context available.",
        sources=[],
    )
    if llm_provider_config.EXTERNAL_RETRIEVAL_ENABLED:
        try:
            log_handler.info("Fetching external literature context")
            external_evidence = fetch_external_evidence(
                paper_title=parsed.title,
                paper_abstract=abstract_text,
                current_paper_url=f"https://arxiv.org/abs/{job.arxiv_resource.arxiv_id}",
                max_results=llm_provider_config.EXTERNAL_SEARCH_MAX_RESULTS,
            )
            log_handler.info("Retrieved %s external source(s)", len(external_evidence.sources))
        except Exception as exc:
            log_handler.warning("External retrieval failed: %s", exc)

    section_summaries: Dict[str, Dict[str, Dict[str, Any]]] = {}

    for section_name, section_text in sections.items():
        if not section_text.strip():
            continue
        log_handler.info("Processing section: %s", section_name)
        token_count = estimate_tokens(section_text)
        if token_count <= llm_provider_config.MAX_INPUT_TOKENS:
            chunks = [section_text]
        else:
            chunks = [
                chunk.text
                for chunk in chunk_text(
                    section_text,
                    llm_provider_config.MAX_INPUT_TOKENS,
                    llm_provider_config.CHUNK_OVERLAP_TOKENS,
                )
            ]
        log_handler.info("Section '%s' split into %s chunk(s)", section_name, len(chunks))

        chunk_outputs = []
        for idx, chunk in enumerate(chunks, start=1):
            log_handler.info(
                "Running agents on chunk %s/%s (%s)",
                idx,
                len(chunks),
                section_name,
            )
            chunk_outputs.append(_run_agents_on_chunk(chunk, section_name, external_evidence))
        log_handler.info("Completed agents for section: %s", section_name)

        aggregated = aggregate_section_outputs(chunk_outputs)
        section_summaries[section_name] = aggregated

    merged_global = aggregate_section_outputs(list(section_summaries.values()))
    report_markdown = build_report(parsed.title, section_summaries, merged_global)

    log_handler.info("Writing report to %s", job.output_path)
    with open(job.output_path, "w", encoding="utf-8") as handle:
        handle.write(report_markdown)
    log_handler.info("Job %s complete in %.1fs", job.job_id, time.time() - start_time)


class run_analysis_pipeline:
    prepare_job = staticmethod(prepare_job)
    execute_job = staticmethod(execute_job)
