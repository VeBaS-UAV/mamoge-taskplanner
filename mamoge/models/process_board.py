#!/usr/bin/env python3


from functools import reduce
import logging
from typing import List, Tuple

from mamoge.models.tasks import DAG, Task, TaskEvent, TaskState
from mamoge.processboard.nx_utils import dag_paths, dag_paths_w_capabilities


class ProcessBoard:
    def __init__(self) -> None:
        self.logger = logging.getLogger(ProcessBoard.__name__)
        self.dags: List[DAG] = []

    def execute(self, dag):

        self.dags.append(dag)
        self.logger.debug(f"executing DAG {dag}")
        for t in dag.roots():
            t.set_state(TaskState.AVAILABLE)

    def task_by_id(self, task_id: str) -> Tuple[Task, DAG]:
        for dag in self.dags:
            if task_id in dag.tasks():
                return dag.tasks()[task_id], dag
        raise Exception(f"task id {task_id} not found")

    def tasks(self):
        results = {}
        for d in self.dags:
            results.update(**d.tasks())
        return results

    def event_input(self, task_id: str, event: TaskEvent):

        try:
            task, dag = self.task_by_id(task_id)
        except Exception as e:
            self.logger.warning(f"Could not find task for id {task_id}")
            return

        # simple state changes
        if task.in_state(TaskState.AVAILABLE) and event == TaskEvent.PLAN:
            task.set_state(TaskState.PLANNED)
        elif task.in_state(TaskState.PLANNED) and event == TaskEvent.ACCEPT:
            task.set_state(TaskState.QUEUED)
        elif task.in_state(TaskState.QUEUED) and event == TaskEvent.START:
            task.set_state(TaskState.RUNNING)

        elif task.in_state(TaskState.RUNNING) and event == TaskEvent.COMPLETED:
            task.set_state(TaskState.COMPLETED)

            # set next tasks to enable
            for _, t in dag.dag.edges([task]):
                # TODO check if not planned or queued
                # FIXME remove this loop, what about two dependend tasks?
                t.set_state(TaskState.AVAILABLE)

        elif task.in_state(TaskState.RUNNING) and event == TaskEvent.ERROR:
            task.set_state(TaskState.FAILURE)

        elif task.in_state(TaskState.COMPLETED):
            self.logger.warning(
                f"task {task.id} is completed, can not process event {event}"
            )

        elif task.in_state(TaskState.FAILURE) and event == TaskEvent.RESOLVED:
            task.set_state(TaskState.PLANNED)

        else:
            self.logger.warning(
                f"task {task.id} has state {task.state} and can not process event {event}"
            )

    def get_openlist(self, capabilities=None) -> List[Task]:
        open_list = []
        selected_list = []

        for dag in self.dags:
            # open_list.extend(dag.roots())

            for t in dag.dag.nodes:
                if t.in_state(TaskState.AVAILABLE):
                    open_list.append(t)
                    continue

        if capabilities is None:
            return open_list

        for task in open_list:
            if task.meet_capabilities(capabilities):
                selected_list.append(task)
        return selected_list

    def get_tasklists(self, capabilities=None):

        start_tasks = self.get_openlist()

        G = self.dags[0].dag

        if capabilities:
            paths = [
                list(dag_paths_w_capabilities(G, [t], capabilities))
                for t in start_tasks
            ]
        else:
            paths = [list(dag_paths(G, [t])) for t in start_tasks]

        return reduce(lambda x, y: x + y, paths)

    def get_taskset(self, capabilities=None):
        tasklists = self.get_tasklists(capabilities=capabilities)
        return set(reduce(lambda x, y: x + y, tasklists))

    def get_subgraph(self, capabilities=None):
        G = self.dags[0].dag
        taskset = list(self.get_taskset(capabilities))
        Gs = G.subgraph(taskset)

        # TODO add sync point check
        return Gs
