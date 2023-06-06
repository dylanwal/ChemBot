from typing import Collection


class Resource:
    """
    A resource is something which can processes event
    """
    def __init__(self, name: str, callables):
        self.name = name
        self.callables = callables


class Policy:
    def __init__(self):
        ...


class PolicyDistributeEqually(Policy):
    ...


class ResourceGroup:
    def __init__(self, resources: Collection[Resource], policy: Policy = None):
        self.resources = resources
        self.policy = policy if policy is None else PolicyDistributeEqually()
