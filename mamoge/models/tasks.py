#!/usr/bin/env python3
from __future__ import annotations
from functools import reduce

import logging
import pyvis
import uuid
import networkx as nx

from enum import Enum
from graphviz import Digraph
from typing import List, Any, Dict, Union, Tuple

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger()

from mamoge.models.capabilities import (
    Requirements,
    Requirement,
    Capabilities,
    Capability,
)


# %%


class TaskState(Enum):
    UNDEFINED = ("undefined",)
    AVAILABLE = ("available",)
    PLANNED = ("planned",)
    QUEUED = ("queued",)
    RUNNING = ("running",)
    COMPLETED = "completed"
    FAILURE = "failure"


class TaskEvent(Enum):
    ACTIVATE = "ACTIVATE"
    PLAN = "PLAN"
    ACCEPT = "ACCEPT"
    START = "start"
    COMPLETED = "completed"
    ERROR = "error"
    RESOLVED = "resolved"


#%%
class Task:
    def __init__(
        self, id: str, name: str, requirements: Requirements = Requirements()
    ) -> None:
        self.logger = logging.getLogger(Task.__name__)
        self.id = f"/{id}"
        self.local_id = id
        self.name = name
        self.state: TaskState = TaskState.UNDEFINED
        self.requirements = requirements

    def set_state(self, state: TaskState):
        self.logger.debug(f"change state {self.id} from {self.state} to {state}")
        self.state = state

    def __repr_rec__(self, intent=1) -> str:
        name = f"<{self.id}:{self.name}[{self.state}]>"
        name = f"<{self.id}/{self.name}>"
        # name = f"<{self.name}[{self.state}]>"
        # name = f"<{self.name}>"

        ds_repr = ""
        # for t in self.downstream:
        #    ds_repr += "\n"
        #    ds_repr += " "* intent
        #    ds_repr += t.__repr_rec__(intent+1)
        # ds_repr += "\n"
        return name + ds_repr

    def has_requirements(self, name: str):
        return name in self.requirements

    def meet_capabilities(self, capabilities: Capabilities):
        return self.requirements.meet(capabilities)

    def __repr__(self) -> str:
        return self.__repr_rec__()

    def in_state(self, state):
        return self.state == state


class DAG:
    def __init__(self, name: str) -> None:
        self.logger = logging.getLogger(DAG.__name__)
        # self.id: str = uuid.uuid4().hex[:6]
        self.id: str = name

        self.name = name
        self.dag = nx.DiGraph()

    def add_task(self, task: Task) -> None:

        task.id = f"{self.id}/{task.local_id}"

        self.dag.add_node(task)

    def tasks(self):
        return {t.id: t for t in self.dag.nodes}

    def set_downstream(self, t_up: Task, t_down: Task):
        self.dag.add_edge(t_up, t_down)

    def downstream(self, task):
        return [d for t, d in self.dag.edges([task])]

    def roots(self):
        return [t for t in self.dag.nodes if len(self.dag.in_edges(t)) == 0]

    def __repr__(self) -> str:
        dag = ""

        return f"DAG({self.id}:{self.name})\n{dag}"

    def __iadd__(self, task: Task):
        self.add_task(task)
        return self
