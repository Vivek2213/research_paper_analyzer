from pydantic import BaseModel, HttpUrl


class AnalyzeRequest(BaseModel):
    arxiv_url: HttpUrl
