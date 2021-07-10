import os
for module in os.listdir(os.path.dirname(__file__)):
    print(module)
    if module[-3:] == '.py':
        exec(f"from {module[:-3]} import *")
del module
