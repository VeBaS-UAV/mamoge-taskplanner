"""MamoGe Process Board API.

This API handles the process of managing processing (here processes in the sense of
ordered Tasks that are to be done by workers.)
"""
import redis

from mamoge.models.tasks import DAG


class ProcessBoardAPI:
    """Base class for the ProcessBoardAPI."""

    def run_process(self, name: str, template: DAG):
        """Instantiate and run the given named process.

        This will create a process instance, which will be run.

        Args:
            name (str): A unique name to identify the process.
            template: DAG
        """
        raise NotImplementedError

    def get_process_list(self):
        """Get the list of currently running processes.

        This information can be used for listing the processes in the GUI service.

        If looking for not only the running but the planned as well, please ask the
        process director service.
        """
        raise NotImplementedError

    def update(self, name: str, template: DAG):
        """Update the given process.

        Unlike `run_process` this function allows to update a running process.
        Running processes
        """
        raise NotImplementedError

    def delete_process(self, name: str):
        """Delete the given process.

        A delete is equivalent to aborting a process.

        Args:
            name (str): A unique name to identify the process.
        """
        raise NotImplementedError


class ProcessBoardRedisAPI(ProcessBoardAPI):
    """The overlay for the WorkerAPI with a redis flavor.

    This WorkerAPI holds a connection to a redis database.
    """

    def __init__(self, host="localhost", port=6379):
        """Initialize."""
        super().__init__()
        self.redis = redis.Redis(host, port)
        self.tasks = list()
