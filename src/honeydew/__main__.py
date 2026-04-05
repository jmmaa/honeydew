from honeydew import command


@command("root")
def root():
    return "root"


@root.command("addr")
def addr() -> str:

    return "addr command"


@addr.command("str")
def _str(level: str = "10", active: str = "true") -> str:

    return f"addr str command w/ level = {level} and active = {active}"


@addr.command("dex")
def dex(level: str, active: str) -> str:

    return f"addr dex command w/ level = {level} and active = {active}"


res = root.execute("addr")
print(res)

res = root.execute("addr str 10 true")
print(res)

res = root.execute("addr str")
print(res)

res = root.execute("addr dex level = 10 active = true")
print(res)
