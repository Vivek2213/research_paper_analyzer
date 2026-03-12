from dataclasses import dataclass
from typing import Any, Dict, List

from research_paper_analyser.schemas import (
    AuthenticityResult,
    ConsistencyResult,
    FactCheckResult,
    GrammarResult,
    NoveltyResult,
    SectionAgentOutputs,
)


@dataclass(frozen=True)
class SectionAnalysis:
    section_name: str
    results: Dict[str, List[Dict[str, Any]]]


GRAMMAR_RANK = {"Low": 0, "Medium": 1, "High": 2}
UNAVAILABLE_MARKERS = (
    "assessment unavailable",
    "no evidence captured",
    "no limitations captured",
    "no claims captured",
    "no verification items captured",
)


def _unique_strings(values: List[str]) -> List[str]:
    seen = set()
    items = []
    for value in values:
        normalized = value.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        items.append(normalized)
    return items


def _average_int(values: List[int], default: int) -> int:
    if not values:
        return default
    return int(round(sum(values) / len(values)))


def _is_unavailable(text: str) -> bool:
    lowered = text.strip().lower()
    return any(marker in lowered for marker in UNAVAILABLE_MARKERS)


def _select_best_summary(outputs: List[Dict[str, Any]], default: str) -> str:
    summaries = _unique_strings([str(output.get("summary", "")).strip() for output in outputs])
    informative = [summary for summary in summaries if summary and not _is_unavailable(summary)]
    if informative:
        return informative[0]
    return informative[0] if informative else (summaries[0] if summaries else default)


def _summarize_fact_check(outputs: List[Dict[str, Any]], claims: List[str], items: List[str]) -> str:
    informative = [
        str(output.get("summary", "")).strip()
        for output in outputs
        if str(output.get("summary", "")).strip() and not _is_unavailable(str(output.get("summary", "")))
    ]
    if informative:
        return informative[0]
    if claims or items:
        return (
            f"Collected {len(claims)} claim(s) and {len(items)} verification item(s) "
            "from the analyzed sections."
        )
    return "Fact-check assessment unavailable."


def _normalize_text(value: Any) -> str:
    text = str(value).strip()
    replacements = {
        "âˆ†": "∆",
        "â‰ƒ": "≃",
        "â‰¥": "≥",
        "â‰¤": "≤",
        "âˆ¼": "∼",
        "âˆ’": "−",
        "Ã—": "×",
        "âŠ™": "⊙",
        "MâŠ™": "M⊙",
        "Î±": "α",
        "Î²": "β",
        "Î»": "λ",
        "Ï€": "π",
        "Î¸": "θ",
        "Î›": "Λ",
    }
    for broken, fixed in replacements.items():
        text = text.replace(broken, fixed)
    return text


def _section_has_unavailable_data(section_outputs: Dict[str, Dict[str, Any]]) -> bool:
    novelty_summary = _normalize_text(section_outputs.get("novelty", {}).get("summary", ""))
    fact_check_summary = _normalize_text(section_outputs.get("fact_check", {}).get("summary", ""))
    return _is_unavailable(novelty_summary) or _is_unavailable(fact_check_summary)


def _merge_consistency(outputs: List[Dict[str, Any]]) -> Dict[str, Any]:
    return ConsistencyResult.model_validate({
        "score": _average_int([int(output["score"]) for output in outputs], 50),
        "summary": _select_best_summary(outputs, "Consistency assessment unavailable."),
        "strengths": _unique_strings(
            [item for output in outputs for item in output.get("strengths", [])]
        ),
        "concerns": _unique_strings(
            [item for output in outputs for item in output.get("concerns", [])]
        ),
    }).model_dump()


def _merge_grammar(outputs: List[Dict[str, Any]]) -> Dict[str, Any]:
    ratings = [str(output.get("rating", "Medium")).title() for output in outputs]
    rating = min(ratings, key=lambda value: GRAMMAR_RANK.get(value, 1)) if ratings else "Medium"
    return GrammarResult.model_validate({
        "rating": rating,
        "summary": _select_best_summary(outputs, "Grammar assessment unavailable."),
        "strengths": _unique_strings(
            [item for output in outputs for item in output.get("strengths", [])]
        ),
        "issues": _unique_strings([item for output in outputs for item in output.get("issues", [])]),
    }).model_dump()


def _merge_novelty(outputs: List[Dict[str, Any]]) -> Dict[str, Any]:
    novelty_indexes = _unique_strings([str(output.get("novelty_index", "")).strip() for output in outputs])
    novelty_index = novelty_indexes[0] if novelty_indexes else "Undetermined"
    return NoveltyResult.model_validate({
        "novelty_index": novelty_index,
        "summary": _select_best_summary(outputs, "Novelty assessment unavailable."),
        "evidence": _unique_strings([item for output in outputs for item in output.get("evidence", [])]),
        "limitations": _unique_strings(
            [item for output in outputs for item in output.get("limitations", [])]
        ),
    }).model_dump()


def _merge_fact_check(outputs: List[Dict[str, Any]]) -> Dict[str, Any]:
    claims = _unique_strings(
        [item for output in outputs for item in output.get("claims_to_verify", [])]
    )
    items = _unique_strings(
        [item for output in outputs for item in output.get("items_to_verify", [])]
    )
    return FactCheckResult.model_validate({
        "summary": _summarize_fact_check(outputs, claims, items),
        "claims_to_verify": claims,
        "items_to_verify": items,
    }).model_dump()


def _merge_authenticity(outputs: List[Dict[str, Any]]) -> Dict[str, Any]:
    return AuthenticityResult.model_validate({
        "risk_percent": _average_int([int(output["risk_percent"]) for output in outputs], 35),
        "summary": _select_best_summary(outputs, "Authenticity assessment unavailable."),
        "signals": _unique_strings([item for output in outputs for item in output.get("signals", [])]),
        "concerns": _unique_strings([item for output in outputs for item in output.get("concerns", [])]),
    }).model_dump()


def _format_list(items: List[str], empty_message: str) -> List[str]:
    if not items:
        return [empty_message]
    return [f"- {_normalize_text(item)}" for item in items]


def _format_consistency(outputs: Dict[str, Any]) -> List[str]:
    return [
        f"Score: {outputs.get('score', 50)}",
        _normalize_text(outputs.get("summary", "No notes.")),
        "",
        "Strengths",
        *_format_list(outputs.get("strengths", []), "No strengths captured."),
        "",
        "Concerns",
        *_format_list(outputs.get("concerns", []), "No concerns captured."),
    ]


def _format_grammar(outputs: Dict[str, Any]) -> List[str]:
    return [
        f"Rating: {outputs.get('rating', 'Medium')}",
        _normalize_text(outputs.get("summary", "No notes.")),
        "",
        "Strengths",
        *_format_list(outputs.get("strengths", []), "No strengths captured."),
        "",
        "Issues",
        *_format_list(outputs.get("issues", []), "No issues captured."),
    ]


def _format_novelty(outputs: Dict[str, Any]) -> List[str]:
    return [
        f"Novelty Index: {outputs.get('novelty_index', 'Undetermined')}",
        _normalize_text(outputs.get("summary", "No notes.")),
        "",
        "Evidence",
        *_format_list(outputs.get("evidence", []), "No evidence captured."),
        "",
        "Limitations",
        *_format_list(outputs.get("limitations", []), "No limitations captured."),
    ]


def _format_fact_check(outputs: Dict[str, Any]) -> List[str]:
    return [
        _normalize_text(outputs.get("summary", "No notes.")),
        "",
        "Claims To Verify",
        *_format_list(outputs.get("claims_to_verify", []), "No claims captured."),
        "",
        "Items To Verify",
        *_format_list(outputs.get("items_to_verify", []), "No verification items captured."),
    ]


def _format_authenticity(outputs: Dict[str, Any]) -> List[str]:
    return [
        f"Risk Percent: {outputs.get('risk_percent', 35)}%",
        _normalize_text(outputs.get("summary", "No notes.")),
        "",
        "Signals",
        *_format_list(outputs.get("signals", []), "No signals captured."),
        "",
        "Concerns",
        *_format_list(outputs.get("concerns", []), "No concerns captured."),
    ]


def aggregate_section_outputs(section_outputs: List[Dict[str, Dict[str, Any]]]) -> Dict[str, Dict[str, Any]]:
    aggregated: Dict[str, List[Dict[str, Any]]] = {}
    for output in section_outputs:
        for key, value in output.items():
            aggregated.setdefault(key, []).append(value)

    return SectionAgentOutputs.model_validate({
        "consistency": _merge_consistency(aggregated.get("consistency", [])),
        "grammar": _merge_grammar(aggregated.get("grammar", [])),
        "novelty": _merge_novelty(aggregated.get("novelty", [])),
        "fact_check": _merge_fact_check(aggregated.get("fact_check", [])),
        "authenticity": _merge_authenticity(aggregated.get("authenticity", [])),
    }).model_dump()


def build_report(
    title: str,
    section_summaries: Dict[str, Dict[str, Dict[str, Any]]],
    global_outputs: Dict[str, Dict[str, Any]],
) -> str:
    consistency_score = int(global_outputs.get("consistency", {}).get("score", 60))
    authenticity_score = int(global_outputs.get("authenticity", {}).get("risk_percent", 35))
    grammar_rating = _normalize_text(global_outputs.get("grammar", {}).get("rating", "Medium"))
    novelty_index = _normalize_text(global_outputs.get("novelty", {}).get("novelty_index", "Undetermined"))
    incomplete_sections = [
        section_name
        for section_name, outputs in section_summaries.items()
        if _section_has_unavailable_data(outputs)
    ]

    executive_summary = (
        "Pass"
        if consistency_score >= 60 and authenticity_score < 50 and not incomplete_sections
        else "Review"
    )
    if incomplete_sections:
        consistency_score = max(0, min(consistency_score, 55))
        authenticity_score = max(authenticity_score, 35)

    lines = [
        f"# Judgement Report: {_normalize_text(title)}",
        "",
        "## Executive Summary",
        f"Recommendation: **{executive_summary}**",
        *(
            [
                "",
                "Report Confidence Note: One or more sections contain unavailable novelty or fact-check outputs, so the recommendation is conservative.",
                f"Affected Sections: {', '.join(section.title() for section in incomplete_sections)}",
            ]
            if incomplete_sections
            else []
        ),
        "",
        "## Detailed Scores",
        f"- Consistency Score: {consistency_score}",
        f"- Grammar Rating: {grammar_rating}",
        f"- Novelty Index: {novelty_index}",
        f"- Accuracy/Fabrication Score: {authenticity_score}%",
        "",
        "## Fact Check Log",
        _normalize_text(global_outputs.get("fact_check", {}).get("summary", "No fact check notes available.")),
        "",
        "Claims To Verify",
        *_format_list(global_outputs.get("fact_check", {}).get("claims_to_verify", []), "No claims captured."),
        "",
        "Items To Verify",
        *_format_list(global_outputs.get("fact_check", {}).get("items_to_verify", []), "No verification items captured."),
        "",
        "## Section Notes",
    ]

    for section_name, outputs in section_summaries.items():
        lines.extend(
            [
                "",
                f"### {_normalize_text(section_name.title())}",
                "",
                "**Consistency**",
                *_format_consistency(outputs.get("consistency", {})),
                "",
                "**Grammar**",
                *_format_grammar(outputs.get("grammar", {})),
                "",
                "**Novelty**",
                *_format_novelty(outputs.get("novelty", {})),
                "",
                "**Fact Check**",
                *_format_fact_check(outputs.get("fact_check", {})),
                "",
                "**Authenticity**",
                *_format_authenticity(outputs.get("authenticity", {})),
            ]
        )

    return _normalize_text("\n".join(lines).strip())
