from os import listdir
from os.path import isfile, join
import importlib
import inspect


class ObjectRegistry:
    def __init__(self):
        self.objects: dict[str, object] = {}

    def __contains__(self, item: str) -> bool:
        if item in self.objects:
            return True
        return False

    def register(self, obj: type):
        if obj.__name__ in self.objects:
            raise ValueError("Objects can't be registered twice.")

        self.objects[obj.__name__] = obj

    def get(self, obj_name: str):
        if obj_name in self.objects:
            return self.objects[obj_name]

        raise ValueError(f"'{obj_name}' not found.")

    def register_all_class(self, path: str):
        files = [f for f in listdir(path) if isfile(join(path, f))]
        for x in files:
            module = importlib.import_module(x)
            for name, obj in inspect.getmembers(module, inspect.isclass):
                self.register(obj)
