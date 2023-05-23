from __future__ import annotations

import inspect
import json
import sys
import uuid

from chembot import registry
from chembot.utils.serializer import serialize_try, deserialize_try


class RabbitMessage:
    def __init__(self, destination: str, source: str):
        self.id_: int = uuid.uuid4().int
        self.destination = destination
        self.source = source
        # self.type_ = type(self).__name__

    def __str__(self):
        return self.to_str()

    def __repr__(self):
        return self.__str__()

    def to_JSON(self) -> str:  # noqa
        dict_ = serialize_try(self)
        return json.dumps(dict_)

    def to_str(self) -> str:
        return f"\n\t{type(self).__name__} | {self.source} -> {self.destination} (id: {self.id_})"


class RabbitMessageError(RabbitMessage):
    def __init__(self, source: str, error: str):
        super().__init__("master_controller", source)
        self.error = error

    def to_str(self) -> str:
        return super().to_str() + f"\n\tERROR: {self.error}"


class RabbitMessageCritical(RabbitMessage):
    def __init__(self, source: str, error: str):
        super().__init__("master_controller", source)
        self.error = error

    def to_str(self) -> str:
        return super().to_str() + f"\n\tCritical: {self.error}"


class RabbitMessageAction(RabbitMessage):
    def __init__(self, destination: str, source: str, action: str, parameters: dict = None):
        super().__init__(destination, source)
        self.action = action
        self.parameters = parameters

    def to_str(self) -> str:
        text = super().to_str()
        text += f"\n\taction: {self.action}"
        text += "\n\tparameters: "
        if self.parameters is not None:
            text += "".join(f"\n\t\t{k}: {v}" for k, v in self.parameters.items())

        return text


class RabbitMessageReply(RabbitMessage):
    def __init__(self, destination: str, source: str, id_reply: int, value):
        super().__init__(destination, source)
        self.id_reply = id_reply
        self.value = value

    def to_str(self) -> str:
        return super().to_str() + f"\n\tid_reply: {self.id_reply}" + f"\n\tvalue: {self.value}"

    @staticmethod
    def create_reply(message: RabbitMessage, value):
        return RabbitMessageReply(
            destination=message.source,
            source=message.destination,
            id_reply=message.id_,
            value=value
        )


class RabbitMessageRegister(RabbitMessage):
    def __init__(self, source: str, equipment_interface):
        super().__init__("master_controller", source)
        self.equipment_interface = equipment_interface

    def to_str(self) -> str:
        return super().to_str()


# automatically grab all messages
class_in_file = inspect.getmembers(sys.modules[__name__], inspect.isclass)
message_factory = {k: v for k, v in class_in_file}


def JSON_to_class(data: str | dict[str, object]):
    if isinstance(data, str):
        data = json.loads(data)
    return deserialize_try(data, registry)


registry.register(RabbitMessage)
registry.register(RabbitMessageRegister)
registry.register(RabbitMessageCritical)
registry.register(RabbitMessageError)
registry.register(RabbitMessageAction)
registry.register(RabbitMessageReply)
