import typing as t


T = t.TypeVar("T")

MaybeAwaitable: t.TypeAlias = t.Union[T, t.Awaitable[T]]

