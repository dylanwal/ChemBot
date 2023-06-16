from typing import Any

from chembot.master_controller.registry import EquipmentRegistry
from chembot.equipment.equipment_interface import EquipmentInterface, ActionParameter

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
    action = event.callable_
    if action not in equipment_interface.action_names:
        result.register_error(
            ValueError(f"{event.resource}.{action} not valid action.")
        )
        return

    validate_event_arguments(f"{event.resource}.{action}", event.kwargs,
                             equipment_interface.get_action(action).inputs, result)


def validate_event_arguments(
        event_label: str,
        kwargs: dict[str, Any],
        inputs: list[ActionParameter],
        result: JobSubmitResult
):
    required_actions = [arg.required for arg in inputs]  # true for required, will be changed to false if provided
    input_names = [input_.name for input_ in inputs]

    for k, v in kwargs.items():
        if k not in input_names:
            result.register_error(
                ValueError(f"{event_label}: '{k}' is invalid parameter.")
            )
            continue

        index = input_names.index(k)
        required_actions[index] = False

        try:
            inputs[index].validate(v)
        except (ValueError, TypeError) as e:
            result.register_error(
                type(e)(f"{event_label}: " + str(e))
            )

    # check if any required parameters are missing
    if any(required_actions):
        result.register_error(
            ValueError(f"{event_label}: the following are missing required parameters:\n" +
                       "\n".join(f"\t{kwarg.name}" for v, kwarg in zip(required_actions, inputs) if v))
        )
