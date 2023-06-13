
from chembot.master_controller.registry import EquipmentRegistry
from chembot.equipment.equipment_interface import EquipmentInterface

from chembot.scheduler.event import Event
from chembot.scheduler.schedule import Schedule
from chembot.scheduler.schedular import JobSubmitResult


def validate_job(schedule: Schedule, registry: EquipmentRegistry, result: JobSubmitResult):
    for resource in schedule.resources:
        if resource.name not in registry.equipment:
            result.register_error(
                ValueError(f"{resource.name} not in 'registered equipment'.")
            )
            continue

        for event in resource.events:
            validate_event(event, registry.equipment[resource.name], result)


def validate_event(event: Event, equipment_interface: EquipmentInterface, result: JobSubmitResult):
    event_action = event.callable_.__name__
    if event_action not in equipment_interface.action_names:
        result.register_error(
            ValueError(f"{event.resource}.{event.callable_} not valid action.")
        )
        return

    action_inputs = equipment_interface.get_action(event_action)
    required_actions = a

    if event.args is not None:
        for i, args in enumerate(event.args):
            if not action_inputs[i].valid_value(args):
                continue

    for kwargs in event.kwargs:
        pass
