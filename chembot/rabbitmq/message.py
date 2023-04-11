from __future__ import annotations

import json


class RabbitMessage:
    def __init__(self, destination: str, source: str, action: str, value, parameters: dict = None):
        self.destination = destination
        self.source = source
        self.action = action
        self.value = value
        self.parameters = parameters

    def __str__(self):
        return f"{self.source} -> {self.destination} | {self.action}: {self.value}"

    def __repr__(self):
        return self.__str__()

    def to_JSON(self) -> str:  # noqa
        return json.dumps(self, default=lambda x: x.__dict__)

    def to_str(self) -> str:
        return f"\n\t{self.source} -> {self.destination} " \
                 f"\n\taction: {self.action}" \
                 f"\n\tvalue: {self.value}"

    @classmethod
    def from_JSON(cls, message: str) -> RabbitMessage:  # noqa
        message = json.loads(message)
        return RabbitMessage(**message)
