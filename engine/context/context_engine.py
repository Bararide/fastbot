from typing import Dict, Callable, Any
import inspect


class ContextEngine:
    def __init__(self):
        self._context_templates: Dict[str, Callable] = {}

    def add(self, name: str, template: Callable) -> None:
        if not callable(template):
            raise ValueError("Template must be callable")
        self._context_templates[name] = template

    async def get(self, name: str, **kwargs) -> Dict[str, Any]:
        if name not in self._context_templates:
            raise KeyError(f"Context '{name}' not registered")

        template = self._context_templates[name]
        sig = inspect.signature(template)

        bound_args = sig.bind_partial(**kwargs)
        bound_args.apply_defaults()

        if inspect.iscoroutinefunction(template):
            return await template(**bound_args.arguments)
        return template(**bound_args.arguments)

    async def combine(
        self,
        names: list[str],
        *,
        prefix: str = "",
        suffix: str = "",
        overwrite: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        context = {}
        for name in names:
            ctx = await self.get(name, **kwargs)

            processed_ctx = {
                f"{prefix}{key}{suffix}": value for key, value in ctx.items()
            }

            if not overwrite:
                conflicting_keys = set(processed_ctx.keys()) & set(context.keys())
                if conflicting_keys:
                    raise KeyError(
                        f"Key conflict for {conflicting_keys} "
                        f"when combining context '{name}'"
                    )

            context.update(processed_ctx)
        return context

    def __str__(self):
        return f"ContextEngine({', '.join(self._context_templates.keys())})"
