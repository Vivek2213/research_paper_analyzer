from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from research_paper_analyser.utils.templates import (
    MAIN_PAGE_TEMPLATE,
    TEMPLATE_DESCRIPTION,
    TEMPLATE_HEADER,
    TEMPLATE_TITLE,
)

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def ping(request: Request):
    base_url = str(request.base_url)
    return MAIN_PAGE_TEMPLATE.format(
        title=TEMPLATE_TITLE,
        header=TEMPLATE_HEADER,
        description=TEMPLATE_DESCRIPTION,
        api_url=base_url,
    )
