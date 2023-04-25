from __future__ import annotations

import json


class RabbitMessage:
    def __init__(self, destination: str, source: str):
        self.destination = destination
        self.source = source
        self.type_ = type(self).__name__

    def __str__(self):
        return f"{self.source} -> {self.destination}"

    def __repr__(self):
        return self.__str__()

    def to_JSON(self) -> str:  # noqa
        return json.dumps(self, default=lambda x: x.__dict__)

    def to_str(self) -> str:
        return f"\n\t{self.source} -> {self.destination} "

    @classmethod
    def from_JSON(cls, message: str) -> RabbitMessage:  # noqa
        message = json.loads(message)
        return RabbitMessage(**message)


class RabbitMessageError(RabbitMessage):
    def __init__(self, source: str, error: str):
        super().__init__("error", source)
        self.error = error

    def __str__(self):
        return super().__str__() + f" | ERROR"

    def to_str(self) -> str:
        return f"\n\t{self.source} -> {self.destination} " \
                 f"\n\tERROR: {self.error}"


class RabbitMessageState(RabbitMessage):
    def __init__(self, class_, state: str):
        super().__init__("state", type(class_).__name__)
        self.state = state

    def __str__(self):
        return super().__str__() + f" | state: {self.state}"

    def to_str(self) -> str:
        return f"\n\t{self.source} -> {self.destination} " \
                 f"\n\tstate: {self.state}"


class RabbitMessageDeactivate(RabbitMessage):
    def __init__(self, destination: str):
        super().__init__(destination, "controller")

    def __str__(self):
        return super().__str__() + f" | Deactivate"

    def to_str(self) -> str:
        return f"\n\t{self.source} -> {self.destination} " \
                 f"\n\tDeactivate"


class RabbitMessageAction(RabbitMessage):
    def __init__(self, destination: str, source: str, action: str, value, parameters: dict = None):
        super().__init__(destination, source)
        self.action = action
        self.value = value
        self.parameters = parameters

    def __str__(self):
        return super().__str__() + f" | {self.action}: {self.value}"

    def to_str(self) -> str:
        return f"\n\t{self.source} -> {self.destination} " \
                 f"\n\taction: {self.action}" \
                 f"\n\tvalue: {self.value}"


class RabbitMessageRegister(RabbitMessage):
    def __init__(self, destination: str, source: str, equipment_interface):
        super().__init__(destination, source)
        self.equipment_interface = equipment_interface

    def __str__(self):
        return super().__str__()

    def to_str(self) -> str:
        return f"\n\t{self.source} -> {self.destination} " \
