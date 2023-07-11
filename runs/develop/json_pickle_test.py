import copy
import time
import pickle
import jsonpickle

from unitpy import U

import chembot


def main():
    t_pickle_dumps = 0
    t_pickle_loads = 0
    t_jsonpickle_dumps = 0
    t_jsonpickle_loads = 0

    a = chembot.equipment.pumps.SyringePumpHarvard(
        name="t",
        syringe=chembot.equipment.pumps.Syringe(1 * U("ml"), 0.1 * U.cm),
        communication="comm"
    )

    obj = a.equipment_interface
    obj2 = copy.deepcopy(obj)
    n = 1000
    for i in range(n):
        start = time.perf_counter()
        dump = pickle.dumps(obj, protocol=5)
        end = time.perf_counter()
        t_pickle_dumps += end - start

        start = time.perf_counter()
        dump2 = jsonpickle.dumps(obj2)
        end = time.perf_counter()
        t_jsonpickle_dumps += end - start

        start = time.perf_counter()
        obj = pickle.loads(dump)
        end = time.perf_counter()
        t_pickle_loads += end - start

        start = time.perf_counter()
        obj2 = jsonpickle.loads(dump2)
        end = time.perf_counter()
        t_jsonpickle_loads += end - start

    print("pickle.dumps: ", t_pickle_dumps/n)
    print("pickle.loads: ", t_pickle_loads / n)
    print("jsonpickle.dumps: ", t_jsonpickle_dumps / n)
    print("jsonpickle.loads: ", t_jsonpickle_loads / n)
    print("dumps", t_pickle_dumps/t_jsonpickle_dumps)
    print("loads", t_pickle_loads/t_jsonpickle_loads)


if __name__ == "__main__":
    main()

""" Conclusion: pickle is x40 faster than jsonpickle """
