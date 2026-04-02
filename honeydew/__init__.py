from __future__ import annotations

import logging
import typing as t
from dataclasses import dataclass, field

import dew
from dew.types import Argument, KeywordArgument, PositionalArgument

from honeydew._types import MaybeAwaitable

logging = logging.getLogger("yui")


@dataclass
class Command:
    name: str
    func: t.Callable[..., MaybeAwaitable[t.Any | None]]


@dataclass
class CommandTree:
    data: Command
    parent: CommandTree | None
    children: list[CommandTree] = field(default_factory=list)

    def get_command_sequence(self) -> list[CommandTree]:
        # TODO: probably make this in functional pattern
        sequence: list[CommandTree] = []
        curr = self

        in_root = False

        while not in_root:
            sequence.insert(0, curr)
            if curr.parent is None:
                in_root = True

            else:
                curr = curr.parent
        return sequence

    def command(
        self, name: str
    ) -> t.Callable[[t.Callable[..., MaybeAwaitable[t.Any | None]]], CommandTree]:
        def __wrap__(func: t.Callable[..., t.Any | None]):
            children_names = list(map(lambda c: c.data.name, self.children))

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

    def get_func_data(self, cmd: str):
        args = dew.parse(cmd)
        resolved = resolve_command(args, self)

        return resolved


def command(
    name: str,
) -> t.Callable[[t.Callable[..., MaybeAwaitable[t.Any | None]]], CommandTree]:
    def __wrap__(func: t.Callable[..., t.Any | None]):
        data = Command(name=name, func=func)
        tree = CommandTree(parent=None, data=data, children=[])

        return tree

    return __wrap__


def parse_command(inp: str):

    return dew.parse(inp)


def resolve_command(args: list[Argument], tree: CommandTree) -> Command:

    arg = args.pop(0)

    match arg:
        case Argument(PositionalArgument(value)):
            for child in tree.children:
                if child.data.name == value:
                    chosen_child = child

                    if len(args) != 0:
                        return resolve_command(args, chosen_child)

                    return child.data
                continue

            raise Exception(f"unknown command: {value}")

        case Argument(KeywordArgument(value)):
            raise Exception("a keyword argument cannot be a command")

        case _:
            raise Exception(f"invalid data: {arg}")


def create_root(prefix: str):
    cmd = Command(name=prefix, func=lambda: None)

    return CommandTree(cmd, parent=None, children=[])
