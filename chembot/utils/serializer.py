import enum
import logging

from chembot.utils.object_registry import ObjectRegistry
from chembot.configuration import config

logger = logging.getLogger(config.root_logger_name + ".serialize")


def serialize_try(obj):
    try:
        return serialize(obj)
    except Exception as e:
        logger.exception(f"Exception raise while serializing: {obj}")
        raise e


def serialize(obj):
    if isinstance(obj, (list, tuple)):
        return [serialize(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: serialize(value) for key, value in obj.items()}
    elif isinstance(obj, enum.Enum):
        return {'enum': type(obj).__name__, 'value': obj.value}
    elif hasattr(obj, '__dict__'):
        keys = {k.lstrip("_") for k in vars(obj) if not k.startswith("__")}
        dict_ = {k: serialize(getattr(obj, k)) for k in keys}
        dict_["class"] = type(obj).__name__
        return dict_
    else:
        return obj


def deserialize_try(json_data: dict, registry: ObjectRegistry):
    try:
        return deserialize(json_data, registry)
    except Exception as e:
        logger.exception(f"Exception raise while deserializing: {json_data}")
        raise e


def deserialize(json_data: dict, registry: ObjectRegistry):
    if isinstance(json_data, (list, tuple)):
        return [deserialize(item, registry) for item in json_data]
    elif isinstance(json_data, dict):
        if "enum" in json_data:
            return registry.get(json_data["enum"])(json_data["value"])
        if "class" in json_data:
            class_ = registry.get(json_data.pop("class"))
            __init__param = class_.__init__.__code__.co_varnames
            init_parameters = {}
            parameters = {}
            for key, value in json_data.items():
                parameter = deserialize(value, registry)
                if key in __init__param:
                    init_parameters[key] = parameter
                else:
                    parameters[key] = parameter

            obj = class_(**init_parameters)
            for k, v in parameters.items():
                if not hasattr(obj, k):
                    raise ValueError(f"Attempting to setattr({type(obj).__name__}, {k}); but {k} does not exist.")
                setattr(obj, k, v)
            return obj

        args = {}
        for key, value in json_data.items():
            args[key] = deserialize(value, registry)
        return args
    else:
        return json_data
