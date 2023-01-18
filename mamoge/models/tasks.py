#!/usr/bin/env python3
from __future__ import annotations
from abc import abstractmethod
from enum import Enum
from functools import reduce
from typing import List, Any, Dict, Union, Tuple
import json
import logging

from graphviz import Digraph
import networkx as nx
import pyvis
import uuid

from mamoge.models.capabilities import (
    Capabilities,
    Capability,
    Requirement,
    Requirements,
)


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()


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


class Task:
    def __init__(
        self,
        id: str,
        name: str,
        requirements: Requirements,
        state: TaskState = TaskState.UNDEFINED,
    ) -> None:
        self._logger = logging.getLogger(Task.__name__)
        self.id = id
        self.local_id = id
        self.name = name
        self.state: TaskState = TaskState.UNDEFINED
        self.requirements: Requirements = requirements

    def set_state(self, state: TaskState):
        self._logger.debug(f"change state {self.id} from {self.state} to {state}")
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
        return name in self.requirements.requirements

    def meet_capabilities(self, capabilities: Capabilities):
        return self.requirements.meet(capabilities)

    def __repr__(self) -> str:
        return self.__repr_rec__()

    def in_state(self, state):
        return self.state == state

    def dict(self):
        d = {}
        d["id"] = self.id
        d["local_id"] = self.local_id
        d["name"] = self.name
        d["state"] = str(self.state)
        d["requirements"] = self.requirements.dict()

        return d

    @staticmethod
    def from_dict(dict_value):
        id = dict_value["id"]
        local_id = dict_value["local_id"]
        name = dict_value["name"]
        state = dict_value["state"]
        req = Requirements.from_dict(dict_value["requirements"])
        t = Task(id=id, name=name, state=state, requirements=req)
        t.local_id = local_id

        return t


class TaskSyncPoint(Task):
    def __init__(self, id: str, name: str) -> None:
        super().__init__(id, name, requirements=Requirements())


class DAG:
    def __init__(self, name: str) -> None:
        self.logger = logging.getLogger(DAG.__name__)
        # self.id: str = uuid.uuid4().hex[:6]
        self.id: str = name

        self.name = name
        self.dag = nx.DiGraph()

    def add_task(self, task: Task) -> None:

        task.id = f"{self.id}/{task.id}"

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

    def __hash__(self):
        return hash(self.__repr__())

    def dict(self):

        nodes = [t.dict() for t in self.dag.nodes]

        edges = [(u.id, v.id) for u, v in self.dag.edges]
        d = {"name": self.name, "nodes": nodes, "edges": edges}

        return d

    @staticmethod
    def from_dict(dict_values):
        name = dict_values["name"]
        nodes = dict_values["nodes"]
        edges = dict_values["edges"]

        dag = DAG(name)

        for n in nodes:
            t = Task.from_dict(n)
            id = t.id
            dag += t
            t.id = id

        tasks = dag.tasks()
        for u, v in edges:
            u_node = tasks[u]
            v_node = tasks[v]
            dag.set_downstream(u_node, v_node)
        return dag
