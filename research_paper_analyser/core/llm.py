from langchain_google_genai import ChatGoogleGenerativeAI

from research_paper_analyser.config import llm_provider_config


def build_llm() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=llm_provider_config.GEMINI_MODEL,
        google_api_key=llm_provider_config.GEMINI_API_KEY,
        temperature=0.2,
        max_output_tokens=llm_provider_config.MAX_OUTPUT_TOKENS,
    )
