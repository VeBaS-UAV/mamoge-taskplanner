"""MamoGe Worker API."""
import redis

from mamoge.models.capabilities import Capabilities, Capability
from mamoge.models.tasks import Tasks


class WorkerAPI:
    """Base class for the WorkerAPI."""

    def register(self, name: str, capabilities: Capabilities):
        """Register this Worker at the Taskplanner.

        Args:
            name (str): name of the worker that is unique in the domain space
            capabilities (Capabilities): workers' capabilities
        """
        raise NotImplementedError

    def unregister(self, name: str):
        """Unregister this Worker from the Taskplanner.

        Args:
            name (str): name of the worker that is unique in the domain space
        """
        raise NotImplementedError

    def keep_alive(self, name: str):
        """Send a Heatbeat.

        This is to let the Taskplanner know, that the worker is still available.
        Otherwise the Taskplanner might try to retract Tasks that have assigned to this
        worker.

        Args:
            name (str): name of the worker that is unique in the domain space
        """
        raise NotImplementedError

    def task_update(self, id, status):
        """Update the properties of a Task.

        This could be used after finishing a task or after aborting it. The status of
        the tasks has to be set, so that the Taskplanner can take this status into
        account for the next planning job.
        """
        raise NotImplementedError

    def tasks_receive(self):
        """Get the next scheduled Task(s) for this Worker.

        TODO define definitive purpose of the function.
        """
        raise NotImplementedError

    def update_capabilities(self, name: str, capabilities: Capabilities):
        """Update the Capabilities of this Worker."""
        raise NotImplementedError

    def update_capability(self, name: str, capability: Capability):
        """Update a single Capability of this Worker."""
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
        self.tasks = list()

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

        # Returns the element at index index in the list stored at key.
        for i in range(0, rlen):
            self.tasks.append(self.redis.lindex(f"workers:{self.name}:pending", 1))


def push_tasks(tasks: Tasks):
    """Experimental function; to be deleted."""
    r = redis.Redis(host="localhost", port=6379)

    for task in tasks.tasks:
        r.rpush("workers:dude:pending", task.to_json())
