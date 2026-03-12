import json
import re
from typing import Any, Dict, TypedDict

from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, StateGraph

from research_paper_analyser.core.llm import build_llm
from research_paper_analyser.schemas import (
    AuthenticityResult,
    ConsistencyResult,
    FactCheckResult,
    GrammarResult,
    NoveltyResult,
)


class AgentState(TypedDict):
    chunk_text: str
    section_name: str
    novelty_context: str
    fact_check_context: str
    results: Dict[str, Any]


def _normalize_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _clamp_score(value: Any, default: int) -> int:
    try:
        numeric_value = int(float(value))
    except (TypeError, ValueError):
        return default
    return max(0, min(100, numeric_value))


def _extract_json_object(text: str) -> Dict[str, Any]:
    text = text.strip()
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            return {}
        try:
            parsed = json.loads(match.group(0))
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}


def _run_agent(
    system_prompt: str,
    chunk_text: str,
    section_name: str,
    external_context: str = "",
) -> Dict[str, Any]:
    llm = build_llm()
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            (
                "human",
                "Section: {section_name}\n\nContent:\n{chunk_text}\n\n"
                "External Context:\n{external_context}\n\n"
                "Return only one valid JSON object and no surrounding markdown.",
            ),
        ]
    )
    chain = prompt | llm
    try:
        response = chain.invoke(
            {
                "chunk_text": chunk_text,
                "section_name": section_name,
                "external_context": external_context or "No external context available.",
            }
        )
        content = response.content if hasattr(response, "content") else str(response)
        return _extract_json_object(content)
    except Exception as exc:
        return {"error": str(exc).strip()}


def _normalize_consistency_output(raw_output: Dict[str, Any]) -> ConsistencyResult:
    return ConsistencyResult.model_validate(
        {
            "score": _clamp_score(raw_output.get("score"), 50),
            "summary": str(
                raw_output.get(
                    "summary",
                    raw_output.get("error", "Consistency assessment unavailable."),
                )
            ).strip(),
            "strengths": _normalize_list(raw_output.get("strengths")),
            "concerns": _normalize_list(raw_output.get("concerns")),
        }
    )


def _normalize_grammar_output(raw_output: Dict[str, Any]) -> GrammarResult:
    rating = str(raw_output.get("rating", "Medium")).strip().title()
    if rating not in {"High", "Medium", "Low"}:
        rating = "Medium"
    return GrammarResult.model_validate(
        {
            "rating": rating,
            "summary": str(
                raw_output.get(
                    "summary",
                    raw_output.get("error", "Grammar assessment unavailable."),
                )
            ).strip(),
            "strengths": _normalize_list(raw_output.get("strengths")),
            "issues": _normalize_list(raw_output.get("issues")),
        }
    )


def _normalize_novelty_output(raw_output: Dict[str, Any]) -> NoveltyResult:
    return NoveltyResult.model_validate(
        {
            "novelty_index": str(raw_output.get("novelty_index", "Undetermined")).strip()
            or "Undetermined",
            "summary": str(
                raw_output.get(
                    "summary",
                    raw_output.get("error", "Novelty assessment unavailable."),
                )
            ).strip(),
            "evidence": _normalize_list(raw_output.get("evidence")),
            "limitations": _normalize_list(raw_output.get("limitations")),
        }
    )


def _normalize_fact_check_output(raw_output: Dict[str, Any]) -> FactCheckResult:
    return FactCheckResult.model_validate(
        {
            "summary": str(
                raw_output.get(
                    "summary",
                    raw_output.get("error", "Fact-check assessment unavailable."),
                )
            ).strip(),
            "claims_to_verify": _normalize_list(raw_output.get("claims_to_verify")),
            "items_to_verify": _normalize_list(raw_output.get("items_to_verify")),
        }
    )


def _normalize_authenticity_output(raw_output: Dict[str, Any]) -> AuthenticityResult:
    return AuthenticityResult.model_validate(
        {
            "risk_percent": _clamp_score(raw_output.get("risk_percent"), 35),
            "summary": str(
                raw_output.get(
                    "summary",
                    raw_output.get("error", "Authenticity assessment unavailable."),
                )
            ).strip(),
            "signals": _normalize_list(raw_output.get("signals")),
            "concerns": _normalize_list(raw_output.get("concerns")),
        }
    )


def _consistency_node(state: AgentState) -> AgentState:
    output = _normalize_consistency_output(
        _run_agent(
            "You are a peer reviewer focusing on internal consistency. "
            "Check whether the methodology supports the results. "
            "Return JSON with keys: score (0-100 integer), summary (string), "
            "strengths (array of strings), concerns (array of strings).",
            state["chunk_text"],
            state["section_name"],
            "",
        )
    )
    state["results"]["consistency"] = output.model_dump()
    return state


def _grammar_node(state: AgentState) -> AgentState:
    output = _normalize_grammar_output(
        _run_agent(
            "You are a technical editor. Evaluate grammar and tone. "
            "Return JSON with keys: rating (High|Medium|Low), summary (string), "
            "strengths (array of strings), issues (array of strings).",
            state["chunk_text"],
            state["section_name"],
            "",
        )
    )
    state["results"]["grammar"] = output.model_dump()
    return state


def _novelty_node(state: AgentState) -> AgentState:
    output = _normalize_novelty_output(
        _run_agent(
            "You are a research analyst. Compare the provided section against the external literature context. "
            "Use the external context when available and state when evidence is weak or absent. "
            "Return JSON with keys: novelty_index (string), summary (string), "
            "evidence (array of strings), limitations (array of strings).",
            state["chunk_text"],
            state["section_name"],
            state["novelty_context"],
        )
    )
    state["results"]["novelty"] = output.model_dump()
    return state


def _fact_check_node(state: AgentState) -> AgentState:
    output = _normalize_fact_check_output(
        _run_agent(
            "You are a fact checker. Use the external context to compare claims in the section against outside evidence. "
            "Only treat something as externally supported when the context clearly aligns. "
            "Return JSON with keys: summary (string), claims_to_verify (array of strings), "
            "items_to_verify (array of strings).",
            state["chunk_text"],
            state["section_name"],
            state["fact_check_context"],
        )
    )
    state["results"]["fact_check"] = output.model_dump()
    return state


def _authenticity_node(state: AgentState) -> AgentState:
    output = _normalize_authenticity_output(
        _run_agent(
            "You are an auditor estimating fabrication risk. "
            "Return JSON with keys: risk_percent (0-100 integer), summary (string), "
            "signals (array of strings), concerns (array of strings).",
            state["chunk_text"],
            state["section_name"],
            "",
        )
    )
    state["results"]["authenticity"] = output.model_dump()
    return state


def build_agent_graph():
    graph = StateGraph(AgentState)
    graph.add_node("consistency", _consistency_node)
    graph.add_node("grammar", _grammar_node)
    graph.add_node("novelty", _novelty_node)
    graph.add_node("fact_check", _fact_check_node)
    graph.add_node("authenticity", _authenticity_node)

    graph.set_entry_point("consistency")
    graph.add_edge("consistency", "grammar")
    graph.add_edge("grammar", "novelty")
    graph.add_edge("novelty", "fact_check")
    graph.add_edge("fact_check", "authenticity")
    graph.add_edge("authenticity", END)
    return graph.compile()
