
def get_actions_list(class_) -> list[str]:
    actions = []
    for func in dir(class_):
        if callable(getattr(class_, func)) and (func.startswith("read_") or func.startswith("write_")):
            actions.append(func)

    return actions
