from __future__ import annotations

import inspect
import json
import sys
import uuid


class RabbitMessage:
    def __init__(self, destination: str, source: str):
        self.id_ = uuid.uuid4().int
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


class RabbitMessageError(RabbitMessage):
    def __init__(self, source: str, error: str):
        super().__init__("master_controller", source)
        self.error = error

    def __str__(self):
        return super().__str__() + f" | ERROR"

    def to_str(self) -> str:
        return f"\n\t{self.source} -> {self.destination} " \
                 f"\n\tERROR: {self.error}"


class RabbitMessageCritical(RabbitMessage):
    def __init__(self, source: str, error: str):
        super().__init__("master_controller", source)
        self.error = error

    def __str__(self):
        return super().__str__() + f" | ERROR"

    def to_str(self) -> str:
        return f"\n\t{self.source} -> {self.destination} " \
                 f"\n\tCritical: {self.error}"


class RabbitMessageAction(RabbitMessage):
    def __init__(self, destination: str, source: str, action: str, parameters: dict = None):
        super().__init__(destination, source)
        self.action = action
        self.parameters = parameters

    def __str__(self):
        return super().__str__() + f" | {self.action}"

    def to_str(self) -> str:
        return f"\n\t{self.source} -> {self.destination} " \
                 f"\n\taction: {self.action}"


class RabbitMessageReply(RabbitMessage):
    def __init__(self, message: RabbitMessage, value):
        super().__init__(source=message.destination, destination=message.source)
        self.id_reply = message.id_
        self.value = value

    def __str__(self):
        return super().__str__() + f" | {self.value}"

    def to_str(self) -> str:
        return f"\n\t{self.source} -> {self.destination} " \
                 f"\n\tvalue: {self.value}"


class RabbitMessageRegister(RabbitMessage):
    def __init__(self, source: str, equipment_interface):
        super().__init__("master_controller", source)
        self.equipment_interface = equipment_interface

    def __str__(self):
        return super().__str__()

    def to_str(self) -> str:
        return f"\n\t{self.source} -> {self.destination} " \


# automatically grab all messages
class_in_file = inspect.getmembers(sys.modules[__name__], inspect.isclass)
message_factory = {k: v for k, v in class_in_file}


def JSON_to_message(message: str) -> RabbitMessage:
    dict_ = json.loads(message)
    class_ = message_factory[dict_.pop("type_")]
    return class_(**dict_)
