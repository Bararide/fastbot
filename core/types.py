from typing import (
    AsyncIterator,
    Iterator,
    TypeVar,
    Generic,
    Optional,
    Callable,
    Any,
    cast,
    overload,
)

import inspect
from collections.abc import Awaitable
from fastbot.logger import Logger

from functools import wraps

T = TypeVar("T")
U = TypeVar("U")
V = TypeVar("V")
E = TypeVar("E", bound=Exception)
F = TypeVar("F", bound=Exception)


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

    def unwrap_err(self) -> E:
        if self._is_ok:
            raise ValueError("Cannot unwrap_err from Ok result")
        return self._error

    def err(self) -> Optional[E]:
        if self._is_ok:
            return None
        return self._error

    def unwrap_or_else(self, fn: Callable[[E], T]) -> T:
        if self._is_ok:
            return self._value
        return fn(self._error)

    def map(self, fn: Callable[[T], U]) -> "Result[U, E]":
        if self._is_ok:
            return Ok(fn(self._value))
        return Err(self._error)

    async def map_async(self, fn: Callable[[T], Awaitable[U]]) -> "Result[U, E]":
        if self._is_ok:
            return Ok(await fn(self._value))
        return Err(self._error)

    def map_err(self, fn: Callable[[E], U]) -> "Result[T, U]":
        if self._is_ok:
            return Ok(self._value)
        return Err(fn(self._error))

    def and_then(self, fn: Callable[[T], "Result[U, E]"]) -> "Result[U, E]":
        if self._is_ok:
            return fn(self._value)
        return Err(self._error)

    def __iter__(self) -> Iterator[T]:
        if self._is_ok:
            if isinstance(self._value, (list, tuple, set)):
                yield from self._value
            else:
                yield self._value
        else:
            return
            yield

    def __aiter__(self) -> AsyncIterator[T]:
        async def async_gen():
            if self._is_ok:
                if isinstance(self._value, (list, tuple, set)):
                    for item in self._value:
                        yield item
                else:
                    yield self._value

        return async_gen()

    async def and_then_async(
        self, fn: Callable[[T], Awaitable["Result[U, E]"]]
    ) -> "Result[U, E]":
        if self._is_ok:
            return await fn(self._value)
        return Err(self._error)

    def __or__(self, other: Callable[[T], "Result[U, E]"]) -> "Result[U, E]":
        return self.and_then(other)

    def __rshift__(self, other: Callable[[T], U]) -> "Result[U, E]":
        return self.map(other)

    @staticmethod
    def pure(value: T) -> "Result[T, Any]":
        return Ok(value)

    @staticmethod
    def sequence(results: list["Result[T, E]"]) -> "Result[list[T], E]":
        values = []
        for result in results:
            if result.is_err():
                return cast(Result[list[T], E], Err(result.unwrap_err()))
            values.append(result.unwrap())
        return Ok(values)

    @staticmethod
    def traverse(
        items: list[T], f: Callable[[T], "Result[U, E]"]
    ) -> "Result[list[U], E]":
        results = [f(item) for item in items]
        return Result.sequence(results)

    def fold(self, ok_case: Callable[[T], U], err_case: Callable[[E], U]) -> U:
        if self._is_ok:
            return ok_case(self._value)
        return err_case(self._error)

    @staticmethod
    def combine(results: list["Result[T, E]"]) -> "Result[list[T], list[E]]":
        values = []
        errors = []

        for result in results:
            if result.is_ok():
                values.append(result.unwrap())
            else:
                errors.append(result.unwrap_err())

        if not errors:
            return Ok(values)
        return Err(errors)

    def combine_with(
        self, other: "Result[U, E]", combine_fn: Callable[[T, U], V]
    ) -> "Result[V, E]":
        if self.is_ok() and other.is_ok():
            return Ok(combine_fn(self.unwrap(), other.unwrap()))
        elif self.is_err():
            return Err(self.unwrap_err())
        else:
            return Err(other.unwrap_err())


def Ok(value: T) -> Result[T, Any]:
    return Result(True, value=value)


def Err(error: E) -> Result[Any, E]:
    return Result(False, error=error)


@overload
def result_try(func: Callable[..., T]) -> Callable[..., Result[T, Exception]]: ...


@overload
def result_try(
    func: Callable[..., Awaitable[T]],
) -> Callable[..., Awaitable[Result[T, Exception]]]: ...


@overload
def result_try(func: Callable[..., Result[T, E]]) -> Callable[..., Result[T, E]]: ...


def result_try(func):
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            result = await func(*args, **kwargs)
            if isinstance(result, Result):
                return result
            return Ok(result)
        except Exception as e:
            Logger.error(f"Error in {func.__name__}: {str(e)}")
            return Err(e)

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            if isinstance(result, Result):
                return result
            return Ok(result)
        except Exception as e:
            Logger.error(f"Error in {func.__name__}: {str(e)}")
            return Err(e)

    if inspect.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper


class Option(Generic[T]):
    def __init__(self, value: Optional[T] = None):
        self._value = value
        self._is_some = value is not None

    @staticmethod
    def Some(value: T) -> "Option[T]":
        return Option(value)

    @staticmethod
    def None_() -> "Option[T]":
        return Option()

    def is_some(self) -> bool:
        return self._is_some

    def is_none(self) -> bool:
        return not self._is_some

    def unwrap(self) -> T:
        if self._is_some:
            return self._value
        raise ValueError("Cannot unwrap None")

    def unwrap_or(self, default: T) -> T:
        if self._is_some:
            return self._value
        return default

    def map(self, f: Callable[[T], U]) -> "Option[U]":
        if self._is_some:
            return Option.Some(f(self._value))
        return Option.None_()

    def and_then(self, f: Callable[[T], "Option[U]"]) -> "Option[U]":
        if self._is_some:
            return f(self._value)
        return Option.None_()

    def to_result(self, err: E) -> Result[T, E]:
        if self._is_some:
            return Ok(self._value)
        return Err(err)


def option_from_result(result: Result[T, E]) -> Option[T]:
    if result.is_ok():
        return Option.Some(result.unwrap())
    return Option.None_()


def compose(f: Callable[[T], U], g: Callable[[U], V]) -> Callable[[T], V]:
    return lambda x: g(f(x))
