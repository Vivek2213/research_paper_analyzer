from typing import Literal

from pydantic import BaseModel, Field


class ConsistencyResult(BaseModel):
    score: int = Field(default=50, ge=0, le=100)
    summary: str = "Consistency assessment unavailable."
    strengths: list[str] = Field(default_factory=list)
    concerns: list[str] = Field(default_factory=list)


class GrammarResult(BaseModel):
    rating: Literal["High", "Medium", "Low"] = "Medium"
    summary: str = "Grammar assessment unavailable."
    strengths: list[str] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)


class NoveltyResult(BaseModel):
    novelty_index: str = "Undetermined"
    summary: str = "Novelty assessment unavailable."
    evidence: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class FactCheckResult(BaseModel):
    summary: str = "Fact-check assessment unavailable."
    claims_to_verify: list[str] = Field(default_factory=list)
    items_to_verify: list[str] = Field(default_factory=list)


class AuthenticityResult(BaseModel):
    risk_percent: int = Field(default=35, ge=0, le=100)
    summary: str = "Authenticity assessment unavailable."
    signals: list[str] = Field(default_factory=list)
    concerns: list[str] = Field(default_factory=list)


class SectionAgentOutputs(BaseModel):
    consistency: ConsistencyResult = Field(default_factory=ConsistencyResult)
    grammar: GrammarResult = Field(default_factory=GrammarResult)
    novelty: NoveltyResult = Field(default_factory=NoveltyResult)
    fact_check: FactCheckResult = Field(default_factory=FactCheckResult)
    authenticity: AuthenticityResult = Field(default_factory=AuthenticityResult)
