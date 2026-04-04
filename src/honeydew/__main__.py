from honeydew import command


@command("root")
def root():
    return "root"


@root.command("addr")
def addr() -> str:

    return "addr command"


@addr.command("str")
def _str(level: str, active: str) -> str:

    return f"addr str command w/ level = {level} and active = {active}"


@addr.command("dex")
def dex(level: str, active: str) -> str:

    return f"addr dex command w/ level = {level} and active = {active}"


cmd = root.parse_args("addr")
print(cmd())

cmd = root.parse_args("addr str 10 true")
print(cmd())

cmd = root.parse_args("addr dex level = 10 active = true")
print(cmd())
