import honeydew

root = honeydew.create_root("/")


@root.command(name="sample")
def sample() -> str:

    return "sample"


@root.command(name="sample2")
def sample2() -> str:

    return "sample2"


@sample2.command("sample22")
def sample22() -> str:
    return "sample22"


cmd = root.get_func_data("sample2 sample22")
print(cmd.func())
