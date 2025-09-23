from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
from typing import Any, Dict
from .template_engine import TemplateEngine
from ..context import ContextEngine
from typing import Optional
from datetime import datetime


class WebTemplateEngine:
    def __init__(self, template_engine: TemplateEngine, context_engine: ContextEngine = None):
        self.template_engine = template_engine
        self.context_engine = context_engine or ContextEngine()
        
    async def render_page(
        self,
        request: Request,
        template_name: str,
        context_template: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None,
        status_code: int = 200,
    ) -> HTMLResponse:
        base_context = {
            "request": request,
            "now": datetime.now(),
        }
        
        if context_template:
            template_context = await self.context_engine.get(
                context_template, 
                request=request,
                **(additional_context or {})
            )
            base_context.update(template_context)
        
        if additional_context:
            base_context.update(additional_context)
        
        html_content = await self.template_engine.render_html_template(
            template_name, 
            context=base_context
        )
        
        return HTMLResponse(content=html_content, status_code=status_code)