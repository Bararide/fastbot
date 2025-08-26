from typing import TypeVar, Generic, Union, Optional, Callable, Any, get_type_hints
from dataclasses import dataclass
import inspect

from FastBot.logger import Logger

T = TypeVar("T")
U = TypeVar("U")
E = TypeVar("E", bound=Exception)


class Result(Generic[T, E]):
    def __init__(self, is_ok: bool, value: T = None, error: E = None):
        self._is_ok = is_ok
        self._value = value
        self._error = error

    def is_ok(self) -> bool:
        return self._is_ok

    def is_err(self) -> bool:
        return not self._is_ok

    def unwrap(self) -> T:
        if self._is_ok:
            return self._value
        raise self._error

    def unwrap_or(self, default: T) -> T:
        if self._is_ok:
            return self._value
        return default

    def unwrap_or_else(self, fn: Callable[[E], T]) -> T:
        if self._is_ok:
            return self._value
        return fn(self._error)

    def map(self, fn: Callable[[T], U]) -> "Result[U, E]":
        if self._is_ok:
            return Ok(fn(self._value))
        return Err(self._error)

    def map_err(self, fn: Callable[[E], U]) -> "Result[T, U]":
        if self._is_ok:
            return Ok(self._value)
        return Err(fn(self._error))

    def and_then(self, fn: Callable[[T], "Result[U, E]"]) -> "Result[U, E]":
        if self._is_ok:
            return fn(self._value)
        return Err(self._error)


def Ok(value: T) -> Result[T, Any]:
    return Result(True, value=value)


def Err(error: E) -> Result[Any, E]:
    return Result(False, error=error)


def result_try(func):
    async def async_wrapper(*args, **kwargs):
        try:
            result = await func(*args, **kwargs)
            return Ok(result)
        except Exception as e:
            return Err(e)

    def sync_wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return Ok(result)
        except Exception as e:
            return Err(e)

    if inspect.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper
