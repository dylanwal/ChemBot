
import json


class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, '_JSON_dump'):
            return obj._JSON()
        else:
            return json.JSONEncoder.default(self, obj)


def JSON_dumps(obj) -> str:
    if not hasattr(obj, '_JSON_dump'):
        raise ValueError("Not serializable. Need '_JSON_dump' method.")
    return json.dumps(obj._JSON_dump(), cls=ComplexEncoder)


def JSON_loads(json_str, obj):
