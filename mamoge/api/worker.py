"""MamoGe Worker API.

The Worker API may be used as an entry or connection point to the
MamoGe Task Planning System. It could be utilized by a machine that intends to get
Tasks assigned to itself.

With this, the Worker has to handle the fulfillment of the Tasks with its own
job management. Meaning the WorkerAPI is just for Task retrieval as well as for
registering in the system. When a certain worker has done its job, it has to utilize
the API again to let the system know, what the current status of the Tasks are.
"""
import abc

import redis

from mamoge.models.capabilities import Capabilities, Capability
from mamoge.models.tasks import TaskEvent, TaskState, Tasks


class WorkerAPI(metaclass=abc.ABCMeta):
    """Base class for the WorkerAPI."""

    @abc.abstractmethod
    def register(self, name: str, capabilities: Capabilities):
        """Register this Worker at the Taskplanner.

        Proposal for Args:
            name (str): name of the worker that is unique in the domain space
            capabilities (Capabilities): workers' capabilities
        """
        raise NotImplementedError

    @abc.abstractmethod
    def unregister(self, name: str):
        """Unregister this Worker from the Taskplanner.

        Proposal for Args:
            name (str): name of the worker that is unique in the domain space
        """
        raise NotImplementedError

    @abc.abstractmethod
    def keep_alive(self, name: str):
        """Send a Heatbeat.

        This is to let the Taskplanner know, that the worker is still available.
        Otherwise the Taskplanner might try to retract Tasks that have assigned to this
        worker.

        Proposal for Args:
            name (str): name of the worker that is unique in the domain space
        """
        raise NotImplementedError

    @abc.abstractmethod
    def task_update_send(self, id, status: TaskState):
        """Update the properties of a Task.

        This could be used after finishing a Task or after aborting it. The status of
        the Tasks has to be set, so that the Taskplanner can take this status into
        account for the next planning job.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def tasks(self) -> Tasks:
        """Query current tasks from backend.

        Either reply to push by the Planner or implementation for pull to Planner,
        depending on implementation flavor.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def capabilities_update_send(self, name: str, capabilities: Capabilities):
        """Update the Capabilities of this Worker.

        This is an information directing to the Taskplanner.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def capability_update_send(self, name: str, capability: Capability):
        """Update a single Capability of this Worker.

        This is an information directing to the Taskplanner.
        """
        raise NotImplementedError


class WorkerRedisAPI(WorkerAPI):
    """The overlay for the WorkerAPI with a redis flavor.

    This WorkerAPI holds a connection to a redis database.
    """

    def __init__(self, name, host="localhost", port=6379) -> None:
        """Initialize."""
        super().__init__()
        self.redis = redis.Redis(host, port)
        self.name = name
        self._tasks = list()

    def register(self, capabilities: Capabilities):
        """Register this worker at the Taskplanner.

        Therefore write the capabilities of the worker into the `workers:{workername}`
        key of redis.

        TODO: imprudent setting of the value can have unexpected consequences; therefore
            find a way to a) set an ID in a controlled manner b) only set a value after
            getting permission from the Taskplanner.
            Alternative: ask just for permission: wait for getting an ID from the
            taskplanner
        """
        self.redis.set(f"workers:{self.name}", f"{capabilities.to_json()}")

    def tasks_receive(self):
        """Get the next scheduled Task(s) for this Worker.

        TODO define definitive purpose of the function.
        """
        # TODO define function purpose
        # self.tasks = self.connection.get(f"workers:{self.name}:pending")
        rlen = self.redis.llen(f"workers:{self.name}:pending")

        # Removes and returns the first elements of the list stored at key.
        self.tasks.append(self.redis.lpop(f"workers:{self.name}:pending"))

        # Returns the element at index in the list stored at key. Here, effectively the
        # whole list, since from 0 to length of the list
        for i in range(0, rlen - 1):
            self.tasks.append(self.redis.lindex(f"workers:{self.name}:pending", i))

        # alternative to list retrieval in previous line
        self.redis.lrange(f"workers:{self.name}:pending", 0, -1)
