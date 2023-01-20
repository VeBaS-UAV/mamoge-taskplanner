"""MamoGe Task-Planner-API.

This API handles the process of optimizing processes.
Those processes have to be in `DAG` format and the result will be an
ordered list of `Tasks`.
The planner will also take care of delegation and dispatching of these
`Tasks` by providing the respective communication tools while standardizing
and harmonizing their use.
"""

import abc


class TaskPlannerBase(metaclass=abc.ABCMeta):
    """Base class for the Task Planner API."""

    @abc.abstractmethod
    def optimize(self, process):
        """Optimize the given given process.

        A process is a definition of Tasks and edges that together form a template
        for the Task Planner.

        The planner will transform the DAG into Tasks while preserving the dependecy
        graph. Tasks are grouped into one or more Tasklists, depending on the number
        and structure of registered workers.

        The process itself is derived from a template as well, which will be handeled by
        the Process Board. Use the Process Board to generate the necessary process.

        Proposal for Args:
            dag (Any): The DAG to be optimized. In subclasses this could be a reference
                string (unique identifier) to a DAG, or a `mamoge.models.tasks.DAG`
                object, or string formatted representation, or a json formatted
                representation. This depends on the individual implementation of
                the variants.
                TODO: discuss whether to have a reference (as name like in
                    `ProcessBoardAPI.run_process`), or an arbitrary type (`Any`)
                    of dag here.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def update_task_status(self):
        """Update a Tasks' status."""
        raise NotImplementedError

    @abc.abstractmethod
    def register(self, name):
        """Register a Worker at the Task Planner."""
        raise NotImplementedError


class TaskplannerRedisAPI(TaskPlannerBase):
    def __init__(self) -> None:
        super().__init__()
