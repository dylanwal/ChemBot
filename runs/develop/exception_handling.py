
class ExceptionNew(Exception):
    ...

def func1():
    raise ExceptionNew("func1")

def func2(a = 1):
    try:
        func1()
    except Exception as e:
        e.args += "func2"

func2(2)

