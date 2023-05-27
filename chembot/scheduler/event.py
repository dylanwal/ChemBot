
from chembot.rabbitmq.messages import RabbitMessageAction


class Condition:
    def __init__(self):
        ...


class Event:
    def __init__(self,
                 equipment: str,
                 action: str,
                 time_: float = None,
                 condition: Condition = None,
                 kwargs: dict[str, object] = None,
                 priority: int = 1,
                 callback: callable = None
                 ):
        self.equipment = equipment
        self.action = action
        self.time_ = time_
        self.kwargs = kwargs
        self.priority = priority
        self.callback = callback

    @property
    def message(self) -> RabbitMessageAction:
        return RabbitMessageAction(self.equipment, "master_controller", self.action, self.kwargs)
