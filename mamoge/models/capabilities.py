from __future__ import annotations
from typing import List, Any, Dict, Union
import json
import logging

logger = logging.getLogger()


class Requirement:
    def __init__(self, name: str, value: Any, consumes=False):
        self.name = name
        self._value = value
        self.consumes = consumes

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value

    def meet(self, other: Capability):
        if self.name is not other.name:
            return False

        return self.value <= other.value

    def __repr__(self):
        return f"Requirement{self.name, self.value}"

    def copy(self):
        return Requirement(self.name, self.value)

    def __iadd__(self, req: Requirement):
        if self.name is not req.name:
            raise Exception(
                f"Can not sum up different requirements ({self.name} vs {req.name})"
            )

        self.value += req.value

        return self

    def to_dict(self):
        dict_values = ["name", "value", "consumes"]
        return {n: getattr(self, n) for n in dict_values}

    @staticmethod
    def from_dict(dict_values):
        r = Requirement(**dict_values)
        return r


class Capability:
    def __init__(self, name: str, value: Any):
        self.name = name
        self.value = value

    def satisfy(self, other: Requirement):
        if self.name is not other.name:
            return False

        return self.value >= other.value

    def __repr__(self):
        return f"Capability{self.name, self.value}"

    def copy(self):
        return Capability(self.name, self.value)

    def __isub__(self, req: Requirement):
        if self.name is not req.name:
            raise Exception(
                f"Can not subtract different requirement from capabilty ({self.name} vs {req.name})"
            )

        self.value -= req.value

        return self

    def to_dict(self):
        dict_values = ["name", "value"]
        return {n: getattr(self, n) for n in dict_values}

    @staticmethod
    def from_dict(dict_values):
        r = Capability(**dict_values)
        return r


class Requirements:
    def __init__(self, requirements: List[Requirement]):
        self.requirements = {c.name: c for c in requirements}

    def __contains__(self, item: Capability):
        if isinstance(item, str):
            return item in self.requirements

        return item.name in self.requirements

    def __getitem__(self, key):
        return self.requirements[key]

    def __iadd__(self, req: Union[Requirement, Requirements]):
        if isinstance(req, Requirements):
            for r in req.requirements.values():
                self += r
            return self

        if isinstance(req, list):
            print(req)

        if req.name in self.requirements:
            self.requirements[req.name] += req.copy()
        else:
            self.requirements[req.name] = req.copy()

        return self

    def __repr__(self):
        return f"Requirements({[r for r in self.requirements.values()]})"

    def meet(self, other: Capabilities):
        for req_name, self_req in self.requirements.items():
            if req_name not in other:
                logger.warning(
                    f"not found requirement {self_req} in capabilities {other}"
                )
                return False

            other_cap = other[req_name]
            if self_req.meet(other_cap) is False:
                logger.warning(
                    f"not meet requirement {self_req} with capabilities {other_cap}"
                )
                return False

        return True

    def copy(self):
        cpy = Requirements([])

        for r in self.requirements:
            cpy += r.copy()

        return cpy

    def to_dict(self):
        return {k: r.to_dict() for k, r in self.requirements.items()}

    @staticmethod
    def from_dict(requirement_values: Dict):
        rl = [Requirement.from_dict(req) for name, req in requirement_values.items()]
        return Requirements(*rl)


class Capabilities:
    def __init__(self, capabilities: List[Capability]):
        self.capabilities = {c.name: c for c in capabilities}

    def __contains__(self, item: Capability):
        if isinstance(item, str):
            return item in self.capabilities
        return item.name in self.capabilities

    def __getitem__(self, key):
        return self.capabilities[key]

    def __iadd__(self, cap: Capability):
        self.capabilities[cap.name] = cap
        return self

    def __repr__(self):
        return f"Capabilities({[c for c in self.capabilities.values()]})"

    def copy(self):
        cpy = Capabilities([])

        for n, c in self.capabilities.items():
            cpy += c.copy()

        return cpy

    def satisfy(self, requirements: Requirements):

        for req_name, req in requirements.requirements.items():
            if req.name not in self.capabilities:
                print(f"could not find cap for req {req}")
                # logger.warning(f"could not find capabiltiy for requirement {req}")
                return False

            self_cap = self[req.name]
            if self_cap.satisfy(req) is False:
                print(f"could not satisfy req {req} for cap {self_cap}")
                # logger.warning(
                #     f"Could not satisfy requirement {req} with capability {self_cap}"
                # )
                return False

        return True

    def __lt__(self, requirements: Requirements):
        return self.satisfy(requirements)

    def __le__(self, requirements: Requirements):
        return self.satisfy(requirements)

    def to_dict(self):
        return {k: r.to_dict() for k, r in self.capabilities.items()}

    def to_json(self):
        return json.dumps(self.to_dict())

    @staticmethod
    def from_dict(capabilities_values: Dict):
        rl = [Capability.from_dict(req) for name, req in capabilities_values.items()]
        return Capabilities(*rl)


class CapabilityBag:
    """menge an capabilities.

    frage: How much can I take?
    clou: remaining capabilities

    TODO: check if still valid and necessary

    can add:
        boolean: is there still enough resources for the task?
    """

    def __init__(self, capabilities: Capabilities):
        self.capabilities = capabilities
        self.requirements = Requirements([])

    def remaining_capabilities(self):
        temp_cap = self.capabilities.copy()

        for name, req in self.requirements.requirements.items():
            if name in temp_cap:
                cap = temp_cap[name]

                if req.consumes:
                    cap -= req

        return temp_cap

    def can_add(self, requirements: Requirements):
        temp_cap = self.remaining_capabilities()
        return temp_cap < requirements

    def __repr__(self):
        return "CAPBAG{" + str(self.capabilities) + ", " + str(self.requirements) + "}"
