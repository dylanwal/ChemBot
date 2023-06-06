import enum
import json
import logging

from unitpy import Quantity, Unit

from chembot import registry
from chembot.utils.object_registry import ObjectRegistry
from chembot.configuration import config

logger = logging.getLogger(config.root_logger_name + ".serialize")


def to_JSON(obj):
    try:
        return json.dumps(serialize(obj))
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
    elif isinstance(obj, Quantity):
        return {"class": Quantity.__name__, "value": str(obj)}
    elif isinstance(obj, Unit):
        return {"class": Unit.__name__, "unit": str(obj)}
    elif hasattr(obj, '__dict__'):
        keys = {k.lstrip("_") for k in vars(obj) if not k.startswith("__")}
        dict_ = {k: serialize(getattr(obj, k)) for k in keys}
        dict_["class"] = type(obj).__name__
        return dict_
    elif hasattr(obj, '__slots__'):
        keys = {k.lstrip("_") for k in obj.__slots__ if not k.startswith("__")}
        dict_ = {k: serialize(getattr(obj, k)) for k in keys}
        dict_["class"] = type(obj).__name__
    else:
        return obj


#######################################################################################################################
#######################################################################################################################
def from_JSON(json_data: str | dict[str, object], registry_: ObjectRegistry = registry):
    try:
        if isinstance(json_data, str):
            json_data = json.loads(json_data)
        return deserialize(json_data, registry_)
    except Exception as e:
        logger.exception(f"Exception raise while deserializing: {json_data}")
        raise e


def deserialize(json_data: dict, registry_: ObjectRegistry = registry):
    if isinstance(json_data, (list, tuple)):
        return [deserialize(item, registry_) for item in json_data]
    elif isinstance(json_data, dict):
        if "enum" in json_data:
            return registry_.get(json_data["enum"])(json_data["value"])
        if "class" in json_data:
            class_ = registry_.get(json_data.pop("class"))
            __init__param = class_.__init__.__code__.co_varnames
            init_parameters = {}
            parameters = {}
            for key, value in json_data.items():
                parameter = deserialize(value, registry_)
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
