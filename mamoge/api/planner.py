"""MamoGe Task-Planner-API.

This API handles the process of optimizing processes.
Those processes have to be in `DAG` format and the result will be an
ordered list of `Tasks`.
The planner will also take care of delegation and dispatching of these
`Tasks` by providing the respective communication tools while standardizing
and harmonizing their use.
"""

import abc

from mamoge.models.tasks import DAG, Tasks
from mamoge.models.capabilities import Capability, Capabilities


class TaskPlannerBase(metaclass=abc.ABCMeta):
    """Base class for the Task Planner API.

    Task Planner pushes DAGs to a list queue, to which the optimizer has access.

    The optimizer waits for the DAGs accordingly, each DAG representing a job for it.

    Could ine blocking queue, with queuing mechanics, preparing for the case that there
    are several optimizers.

    The optimizer can then also be accessible via the network (alternatively locally).

    idea: before the optimization the DAG gets a UUID (as ACK), which is
    returned to the (Task Planner), so that he can fetch the result later.
    Alternatively: the Task Planner gets its own answer queue.

    As answer the result of the optimizer comes into another queue.
    """

    @abc.abstractmethod
    def optimize(self, process: DAG):
        """Optimize the given given process.

        A process is a definition of Tasks and edges that together form a template
        for the Task Planner.

        The planner will transform the DAG into Tasks while preserving the dependecy
        graph. Tasks are grouped into one or more Tasklists, depending on the number
        and structure of registered workers.

        The process itself is derived from a template as well, which will be handeled by
        the Process Board. Use the Process Board to generate the necessary process.

        Proposal for Args:
            process (DAG): The DAG to be optimized. In subclasses this could be a
                reference string (unique identifier) to a DAG, or a
                `mamoge.models.tasks.DAG` object, or string formatted representation, or
                a json formatted representation. This depends on the individual
                implementation of the variants.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def task_update_send(self):
        """Update a Tasks' status.

        Directive to the board.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def task_update_receive(self):
        """Update a Tasks' status.

        Information from outside. This may be the worker or the Process Board or
        whomever.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def capability_update_receive(self, name: str, capability: Capability):
        """Update a Capability of a specific worker.

        Information from outside. This may be the worker or the Process Board or
        whomever.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def capabilities_update_receive(self, name: str, capabilities: Capabilities):
        """Update Capabilities of a specific worker.

        Information from outside. This may be the worker or the Process Board or
        whomever.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def register(self, name):
        """Register a Worker at the Task Planner.

        Either reply to request by the Worker or implementation for push to Worker,
        depending on implementation flavor.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def unregister(self, name):
        """Unregister a Worker at the Task Planner.

        Either reply to request by the Worker or implementation for push to Worker,
        depending on implementation flavor.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def tasks(self, worker_name: str, tasks: Tasks):
        """Return current tasks for worker.

        Either reply to request by the Worker or implementation for push to Worker,
        depending on implementation flavor.
        """
        raise NotImplementedError


class TaskplannerRedisAPI(TaskPlannerBase):
    def __init__(self) -> None:
        super().__init__()
