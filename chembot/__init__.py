from chembot.configuration import config
from chembot.utils.object_registry import ObjectRegistry
registry = ObjectRegistry()

import logging
logger = logging.getLogger(config.root_logger_name)

from chembot.gui.gui_core import GUI
from chembot.master_controller.master_controller import MasterController

import chembot.utils as utils
import chembot.communication as communication
import chembot.equipment as equipment


import inspect
import importlib
import os
import pathlib

def get_classes(directory):
    classes = {}
    for filename in os.listdir(directory):
        if filename.endswith('.py'):
            module_name = filename[:-3]
            module = importlib.import_module(module_name)
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj):
                    classes[name] = obj
    return classes

a = get_classes(pathlib.Path(__file__).parent)
