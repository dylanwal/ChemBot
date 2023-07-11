
from unitpy import Unit, Quantity
import pickle
import jsonpickle


def main():
    a = 12.3 * Unit("mL/min")
    aa = Unit("mL/min")

    c = jsonpickle.dumps(a)
    d = jsonpickle.loads(c)
    # b = type(aa).__mro__
    # for bb in b:
    #     hasattr(bb, '__getitem__') and hasattr(bb, 'append')
    print("hi")


if __name__ == "__main__":
    main()
