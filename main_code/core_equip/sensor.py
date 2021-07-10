"""
Valve Class

"""


class Valve:
    def __init__(self,
                 name: str = None,
                 positions: str = None,
                 ):
        pass

    def __repr__(self):
        return f"Valve: {self.name}\n\tport: {self.port}\n\t position: {self.position}"

    def move(self, pos: str):
        ...

    def move_next(self):
        ...

    def move_back(self):
        ...


if __name__ == '__main__':
    ...