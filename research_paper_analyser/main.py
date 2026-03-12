from fastapi import FastAPI

from research_paper_analyser.api import api_router
from research_paper_analyser.config import llm_provider_config

app = FastAPI(
    title=llm_provider_config.APP_NAME,
    description=llm_provider_config.APP_DESCRIPTION,
    version=llm_provider_config.APP_VERSION,
)
app.include_router(api_router)
