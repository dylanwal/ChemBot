
from chembot.utils.numpy_parser import parse_numpy_docstring


def local_run():
    class Equip:
        def __init__(self):
            self.a = 1

        def read_status(self):
            pass

        def _read_status(self) -> str:
            """
            read status
            all functions have this

            Returns
            -------
            status:
                current equipment status

            """
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

        # def _read_none(self):
        #     a = 1

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

    class_ = Light
    funcs = [func for func in dir(class_) if
             callable(getattr(class_, func)) and (func.startswith("_read") or func.startswith("_write"))]
    print(funcs)

    for func in funcs:
        func = getattr(class_, func)
        result = get_numpy_style_docstring(func)
        print(result)
        print("")


if __name__ == "__main__":
    local_run()