
def get_actions_list(class_) -> list[str]:
    actions = []
    for func in dir(class_):
        if (func.startswith("read_") or func.startswith("write_")) and callable(getattr(class_, func)):
            actions.append(func)

    return actions
