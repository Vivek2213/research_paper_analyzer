import logging
import time

from fastapi import Request

from research_paper_analyser.config import llm_provider_config

APP_NAME = llm_provider_config.APP_NAME

logging.basicConfig(level=logging.INFO)
logging.getLogger("azure.servicebus").setLevel(logging.WARNING)
logging.getLogger("azure.core.pipeline").setLevel(logging.CRITICAL)
log_handler = logging.getLogger(name=APP_NAME)


def apiLogStats(start_time: float, request: Request) -> None:
    end_time = time.time()
    elapsed_time = end_time - start_time
    log_handler.info("API Response Time: %.4fs path=%s", elapsed_time, request.url.path)
