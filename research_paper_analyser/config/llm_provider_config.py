from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProviderCredentials(BaseSettings):
    APP_NAME: str = "Agentic Research Paper Evaluator"
    APP_DESCRIPTION: str = "API for evaluating research papers from arXiv with agent-based analysis."
    APP_VERSION: str = "0.1.0"
    TEMPLATE_TITLE: str = "Agentic Research Paper Evaluator"
    TEMPLATE_HEADER: str = "Research Paper Evaluator"
    TEMPLATE_DESCRIPTION: str = "Multi-agent research paper analysis and judgement report generation"
    GEMINI_API_KEY: str
    GEMINI_MODEL: str
    GROBID_URL: str = "http://localhost:8070"
    MAX_INPUT_TOKENS: int = 10500
    CHUNK_OVERLAP_TOKENS: int = 500
    MAX_OUTPUT_TOKENS: int = 1200
    OUTPUT_DIR: str = "output"
    EXTERNAL_RETRIEVAL_ENABLED: bool = True
    EXTERNAL_SEARCH_MAX_RESULTS: int = 5

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
