
class Equip:
    def __init__(self):
        self.a = 1

    def read_status(self) -> str:
        """
        read status
        all functions have this

        Returns
        -------
        status:
            current equipment status

        """
        pass

    def _read_status(self) -> str:
        return "str"

    def _write_status(self, status):
        """
        read status
        all functions have this

        Returns
        -------
        status: str, int
            current equipment status

        """
        return "str"

    def func(self, status: int) -> int:
        """
        read status
        all functions have this

        Returns
        -------
        status: str, int
            current equipment status

        """
        return "str"

    def func2(self, status: int | float) -> int | float:
        """
        read status
        all functions have this

        Returns
        -------
        status: str, int
            current equipment status

        """
        return "str"

    def func3(self, status: int | float | list[int] | list[int, ...] | dict[str, int]) -> int | float | list[int]:
        """
        read status
        all functions have this

        Returns
        -------
        status: str, int
            current equipment status

        """
        return "str"


class Light(Equip):
    def __init__(self):
        super().__init__()
        self._b = "stuff"

    def write_power(self, text: str):
        """ pass"""
        self._write_power(power=0.1)

    def _write_power(self, power: float):
        """
        write power

        Parameters
        ----------
        power:
            light power
            range: [0, 1]


        """
        a = 1

    def _read_comm(self) -> tuple[str, int, list[int, ...]]:
        """
        read_comm
        """
        pass


def get_class_functions(class_: type) -> list[str]:
    funcs = []
    for func in dir(class_):
        if callable(getattr(class_, func)) and not func.startswith("_"):
            # and (func.startswith("read") or func.startswith("write"))
            funcs.append(func)
    return funcs


def run_parse_docstring():
    from chembot.utils.numpy_parser import parse_numpy_docstring_and_signature

    class_ = Light
    funcs = get_class_functions(class_)

    results = []
    for func_name in funcs:
        func = getattr(class_, func_name)
        result = parse_numpy_docstring_and_signature(func)
        results.append(result)

    print(results)


def run_parse_to_equipment_interface():
    from chembot.equipment.equipment_interface import get_equipment_interface

    interface = get_equipment_interface(Light)
    print(interface)


if __name__ == "__main__":
    # run_parse_docstring()
    run_parse_to_equipment_interface()
