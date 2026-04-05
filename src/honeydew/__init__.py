from __future__ import annotations

import inspect
import typing as t
from dataclasses import dataclass, field

import dew
from dew.types import Argument, KeywordArgument, PositionalArgument

from honeydew._types import MaybeAwaitable

T = t.TypeVar("T")


@dataclass
class Command:
    name: str
    func: t.Callable[..., MaybeAwaitable[t.Any | None]]


@dataclass
class CommandTree:
    data: Command
    parent: CommandTree | None = None
    children: list[CommandTree] = field(default_factory=list)

    def get_command_sequence(self) -> list[CommandTree]:
        sequence: list[CommandTree] = []
        curr = self

        in_root = False

        while not in_root:
            if curr.parent is None:
                in_root = True

            else:
                sequence.insert(0, curr)
                curr = curr.parent
        return sequence

    def command(
        self, name: str
    ) -> t.Callable[[t.Callable[..., MaybeAwaitable[t.Any | None]]], CommandTree]:
        def __wrap__(func: t.Callable[..., t.Any | None]):

            children_names = []

            for child in self.children:
                if child.data:
                    children_names.append(child.data.name)

            if name in children_names:
                command_sequence = self.get_command_sequence()

                full_command_name = list(map(lambda x: x.data.name, command_sequence))
                full_command_name.append(name)

                raise Exception(
                    f"cannot add duplicate command '{' '.join(full_command_name)}'"
                )

            data = Command(name=name, func=func)
            tree = CommandTree(parent=self, data=data, children=[])

            self.children.append(tree)

            return tree

        return __wrap__

    def add_tree(self, tree: CommandTree) -> None:
        name = tree.data.name

        children_names = list(map(lambda c: c.data.name, self.children))

        if name in children_names:
            command_sequence = self.get_command_sequence()

            full_command_name = list(map(lambda x: x.data.name, command_sequence))
            full_command_name.append(name)

            raise Exception(
                f"cannot add duplicate command '{' '.join(full_command_name)}'"
            )

        tree.parent = self
        self.children.append(tree)

    def get_tree(self, command_sequence: list[str]) -> CommandTree:
        func = self.__get_tree_recursive([self], command_sequence)

        return func

    def __get_tree_recursive(
        self, trees: list[CommandTree], command_sequence: list[str]
    ) -> CommandTree:
        name = command_sequence.pop(0)
        for tree in trees:
            if tree.data.name == name:
                if len(command_sequence) != 0:
                    return self.__get_tree_recursive(tree.children, command_sequence)

                return tree

        raise Exception(f"could not find command '{name}'")

    def get_trees(self) -> list[CommandTree]:
        trees = self.__get_trees_recursive([self], [])

        return trees

    def __get_trees_recursive(
        self, trees: list[CommandTree], acc: list[CommandTree]
    ) -> list[CommandTree]:
        for tree in trees:
            acc.append(tree)
            if len(tree.children) != 0:
                self.__get_trees_recursive(tree.children, acc)

        return acc

    def parse_args(self, cmd: str):

        args = dew.parse(cmd)

        return self.get_command(args, self)

    def execute(self, cmd: str):

        args, func = self.parse_args(cmd)

        return parameterize(args, func)()

    def get_command(
        self, args: list[Argument], tree: CommandTree
    ) -> tuple[list[Argument], t.Callable[..., MaybeAwaitable[t.Any | None]]]:

        arg = args[0] if args else None

        match arg:
            case Argument(PositionalArgument(value)):
                for child in tree.children:
                    if child.data.name == value:
                        # consume the arg if confirmed to exist
                        args.pop(0)

                        if len(args) != 0:
                            return self.get_command(args, child)

                        func = child.data.func

                        return args, func
                func = tree.data.func

                return args, func

            case Argument(KeywordArgument(value)):
                func = tree.data.func

                return args, func

            case _:
                raise Exception(f"invalid argument: {arg}")


def command(
    name: str,
) -> t.Callable[[t.Callable[..., MaybeAwaitable[t.Any | None]]], CommandTree]:
    def __wrap__(func: t.Callable[..., t.Any | None]):
        data = Command(name=name, func=func)
        tree = CommandTree(parent=None, data=data, children=[])

        return tree

    return __wrap__


async def maybe_await(obj: MaybeAwaitable[T]) -> T:
    if inspect.iscoroutine(obj):
        return await obj

    return t.cast("T", obj)


def parameterize(
    args: list[Argument], func: t.Callable[..., MaybeAwaitable[t.Any | None]]
) -> t.Callable[[], MaybeAwaitable[t.Any | None]]:

    _args = []
    _kwargs = {}

    for arg in args:
        raw_arg = arg.value

        if isinstance(raw_arg, PositionalArgument):
            _args.append(raw_arg.value)

        elif isinstance(raw_arg, KeywordArgument):
            _kwargs.update({raw_arg.name: raw_arg.value})

        else:
            raise TypeError(f"invalid data: {arg}")

    def _call() -> MaybeAwaitable[t.Any | None]:

        return func(*_args, **_kwargs)

    return _call


def resolve_command(
    args: list[Argument], tree: CommandTree
) -> t.Callable[[], MaybeAwaitable[t.Any | None]]:

    arg = args[0] if args else None

    match arg:
        case Argument(PositionalArgument(value)):
            for child in tree.children:
                if child.data.name == value:
                    # consume the arg if confirmed to exist
                    args.pop(0)

                    if len(args) != 0:
                        return resolve_command(args, child)

                    func = child.data.func

                    return parameterize(func, args)

            func = tree.data.func

            return parameterize(func, args)

        case Argument(KeywordArgument(value)):
            func = tree.data.func

            return parameterize(func, args)

        case _:
            raise Exception(f"invalid argument: {arg}")
