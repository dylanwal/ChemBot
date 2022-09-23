import enum


class EquipmentState(enum.Enum):
    offline = 0
    standby = 1
    scheduled_for_use = 2
    error = 3


from chembot.utils.event_scheduler import EventScheduler

event_scheduler = EventScheduler()

from chembot.utils.logger import logger
from chembot.configuration import global_ids, configuration
