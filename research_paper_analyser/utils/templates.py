from research_paper_analyser.config import llm_provider_config


TEMPLATE_TITLE: str = llm_provider_config.TEMPLATE_TITLE
TEMPLATE_HEADER: str = llm_provider_config.TEMPLATE_HEADER
TEMPLATE_DESCRIPTION: str = llm_provider_config.TEMPLATE_DESCRIPTION

MAIN_PAGE_TEMPLATE = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>{title}</title>
        <link
        href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap"
        rel="stylesheet"
        />
        <style>
            body {{
                font-family: 'Inter', sans-serif;
                margin: 0;
                padding: 0;
                background-color: #fafafa;
                color: #333;
                line-height: 1.6;
            }}
            .container {{
                margin: auto;
                background-color: #fafafa;
            }}
            .header {{
                background-color: #1e293b;
                color: #fff;
                padding: 20px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 2.5em;
                font-weight: 700;
            }}
            .content {{
                padding: 30px;
                text-align: center;
            }}
            .content h3 {{
                margin-top: 0;
                font-size: 2em;
                color: #1e293b;
                font-weight: 500;
            }}
            .content p {{
                font-size: 1.2em;
                color: #555;
                margin: 20px 0;
            }}
            .links {{
                margin: 48px 0;
                text-align: center;
            }}
            .link {{
                display: inline-block;
                margin: 10px;
                padding: 10px 20px;
                font-size: 1em;
                color: #fff;
                background-color: #1e293b;
                border: none;
                border-radius: 25px;
                text-decoration: none;
                transition: background-color 0.3s ease;
            }}
            .link:hover {{
                background-color: #293b4d;
            }}
            .button {{
                display: inline-block;
                padding: 12px 25px;
                font-size: 1em;
                color: #fff;
                background-color: #1e293b;
                border: none;
                border-radius: 25px;
                text-decoration: none;
                transition: background-color 0.3s ease;
                margin-top: 20px;
            }}
            .button:hover {{
                background-color: #293b4d;
            }}
            .footer {{
                background-color: #1e293b;
                color: #fff;
                text-align: center;
                padding: 12px;
                position: fixed;
                left: 0;
                bottom: 0;
                width: 100%;
            }}
            .footer p {{
                margin: 0;
                font-size: 1em;
            }}
            .footer a {{
                color: #cbd5e1;
                text-decoration: none;
            }}
            .footer a:hover {{
                text-decoration: underline;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>{title}</h1>
            </div>
            <div class="content">
                <h3>{header}</h3>
                <p>{description}</p>
                <div class="links">
                    <a href="{api_url}" class="link">API URL</a>
                    <a href="{api_url}docs" class="link">Swagger Documentation</a>
                    <a href="{api_url}redoc" class="link">ReDoc Documentation</a>
                    <a href="{api_url}openapi.json" class="link">OpenAPI Documentation</a>
                </div>
            </div>
        </div>
        <div class="footer">
            <p>Personal Project</p>
        </div>
    </body>
    </html>
"""
