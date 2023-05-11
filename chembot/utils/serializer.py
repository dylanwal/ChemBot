import enum

from chembot.utils.object_registry import ObjectRegistry


def serialize(obj):
    if isinstance(obj, (list, tuple)):
        return [serialize(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: serialize(value) for key, value in obj.items()}
    elif isinstance(obj, enum.Enum):
        return {'enum': type(obj).__name__, 'value': obj.value}
    elif hasattr(obj, '__dict__'):
        dict_ = serialize(obj.__dict__)
        dict_["class"] = type(obj).__name__
        return dict_
    else:
        return obj


def deserialize(json_data: dict, registry: ObjectRegistry):
    if isinstance(json_data, (list, tuple)):
        return [deserialize(item, registry) for item in json_data]
    elif isinstance(json_data, dict):
        if "enum" in json_data:
            return registry.get(json_data["enum"])(json_data["value"])
        if "class" in json_data:
            class_ = registry.get(json_data.pop("class"))
            parameters = {}
            for key, value in json_data.items():
                parameters[key] = deserialize(value, registry)
            return class_(**parameters)

        args = {}
        for key, value in json_data.items():
            args[key] = deserialize(value, registry)
        return args
    else:
        return json_data
