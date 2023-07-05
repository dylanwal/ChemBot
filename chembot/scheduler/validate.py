import traceback
from typing import Any

from chembot.equipment.equipment_interface import EquipmentRegistry, EquipmentInterface, ActionParameter
from chembot.equipment.profile import Profile
from chembot.scheduler.event import Event
from chembot.scheduler.schedule import Schedule
from chembot.scheduler.resource import Resource
from chembot.scheduler.submit_result import JobSubmitResult


def validate_schedule(schedule: Schedule, registry: EquipmentRegistry, result: JobSubmitResult):
    check_job(schedule, registry, result)
    check_schedule_for_overlapping_events(schedule, result)

    if len(result.errors) == 0:
        result.validation_success = True


def check_job(schedule: Schedule, registry: EquipmentRegistry, result: JobSubmitResult):
    for resource in schedule.resources:  # loop over resources
        if resource.name not in registry.equipment:
            result.register_error(
                ValueError(f"{resource.name} not in 'registered equipment'.")
            )
            continue

        for event in resource.events:  # loop over events in the resources
            check_event(event, registry.equipment[resource.name], result)


def check_event(event: Event, equipment_interface: EquipmentInterface, result: JobSubmitResult):
    action = event.callable_
    if action not in equipment_interface.action_names:
        result.register_error(
            ValueError(f"{event.resource}.{action} not valid action.")
        )
        return

    validate_event_arguments(f"{event.resource}.{action}", event.kwargs,
                             equipment_interface.get_action(action).inputs, result)

    if event.kwargs is not None and "profile" in event.kwargs:
        profile_: Profile = event.kwargs["profile"]
        validate_event_arguments(
            profile_.callable_,
            profile_.step_as_dict(0, with_time=False),
            equipment_interface.get_action(profile_.callable_).inputs,
            result
        )
        validate_event_arguments(
            profile_.callable_,
            profile_.step_as_dict(-1, with_time=False),
            equipment_interface.get_action(profile_.callable_).inputs,
            result
        )
        # TODO: only checking first and last values in profile


def validate_event_arguments(
        event_label: str,
        kwargs: dict[str, Any],
        inputs: list[ActionParameter],
        result: JobSubmitResult
):
    if len(inputs) == 0:
        if kwargs is None:
            return
        raise ValueError("No arguments for this action but some were given.")

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
                type(e)(f"{event_label}: " + traceback.format_exc())
            )

    # check if any required parameters are missing
    if any(required_actions):
        result.register_error(
            ValueError(f"{event_label}: the following are missing required parameters:\n" +
                       "\n".join(f"\t{kwarg.name}" for v, kwarg in zip(required_actions, inputs) if v))
        )


#######################################################################################################################
#######################################################################################################################

def check_schedule_for_overlapping_events(schedule: Schedule, result: JobSubmitResult):
    for resource in schedule.resources:
        conflicts = check_resource_for_overlapping_events(resource)
        if conflicts:
            for conflict in conflicts:
                result.register_error(
                    ValueError(f"Overlapping events in {resource.name} schedule.\n "
                               f"Events: {resource.events[conflict[0]].name} - {resource.events[conflict[1]].name} "
                               f"({conflict})")
                )


def check_resource_for_overlapping_events(resource: Resource, window: int = 2) -> list:
    conflicts = []
    # it assumes the events are ordered
    length = len(resource.events)
    for i in range(length):
        for ii in range(i + 1, i + 1 + window):
            if ii > length - 1:
                continue
            if resource.events[i].time_end > resource.events[ii].time_start:
                conflicts.append((i, ii))

    return conflicts
