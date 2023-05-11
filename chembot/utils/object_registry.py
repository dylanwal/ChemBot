from os import listdir, getcwd
from os.path import isfile, join
import importlib
import inspect


class ObjectRegistry:
    def __init__(self):
        self.objects = {}

    def register(self, obj):
        if type(obj).__name__ in self.objects:
            raise ValueError("Objects can't be registered twice.")

        self.objects[type(obj).__name__] = obj

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
