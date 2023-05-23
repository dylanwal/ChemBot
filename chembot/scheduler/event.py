from datetime import datetime


class Event:
    def __init__(self,
                 equipment: str,
                 action: str,
                 parameters: dict[str, object],
                 time_: datetime = None,
                 callback: callable = None
                 ):
        self.equipment = equipment
        self.action = action
        self.parameters = parameters
        self.time_ = time_
        self.callback = callback
