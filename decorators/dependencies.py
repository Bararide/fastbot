from functools import wraps
from fastapi import Request
from typing import Callable
import inspect


def inject(*dependencies: str):
    def decorator(func: Callable) -> Callable:
        original_sig = inspect.signature(func)

        new_parameters = []
        for param_name, param in original_sig.parameters.items():
            if param_name not in dependencies:
                new_parameters.append(param)

        new_sig = original_sig.replace(parameters=new_parameters)

        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if not request:
                for _, value in kwargs.items():
                    if isinstance(value, Request):
                        request = value
                        break

            if not request:
                raise ValueError("Request object not found in arguments")

            injected = {}
            for dep_name in dependencies:
                if hasattr(request.app.state, dep_name):
                    injected[dep_name] = getattr(request.app.state, dep_name)
                else:
                    raise ValueError(f"Dependency '{dep_name}' not found in app.state")

            bound_args = {}

            sig_params = list(original_sig.parameters.values())
            for i, arg in enumerate(args):
                if i < len(sig_params):
                    param_name = sig_params[i].name
                    bound_args[param_name] = arg

            bound_args.update(kwargs)
            bound_args.update(injected)

            return await func(**bound_args)

        wrapper.__signature__ = new_sig
        return wrapper

    return decorator
