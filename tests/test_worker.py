import pytest

from mamoge.api.worker import WorkerAPI, RedisWorker
from mamoge.models.capabilities import Capabilities, Capability
from mamoge.models.tasks import Task


class BaseWorkerAPI:
    """Global test cases that are meant to be run for every child class.

    child classes are different imlpementations of the workerAPI, e.g. with different
    connections and corresponding specifications.
    """

    @classmethod
    def setup_class(cls):
        cls.worker = WorkerAPI()

        cls.cap_water = Capability("water", 10)
        cls.cap_energy = Capability("energy", 15)
        cls.cap_multiple = Capabilities(cls.cap_water, cls.cap_energy)

        cls.t1 = Task(id=, name=, requirements=, state=)

    def test_register(self):
        result = self.worker.register("username", self.cap_multiple)
        assert result is True

    def test_unregister(self):
        result = self.worker.unregister("username")
        assert result is True

    def test_keep_alive(self) -> None:
        result = self.worker.keep_alive("username")
        assert result is True

    def test_task_update(self):
        id
        status

        result = self.worker.task_update(id, status)
        assert result is True

    def test_tasks_receive(self):
        assert True is True

    def test_update_capabilities(self):

        result = self.worker.update_capabilities("username", self.cap_multiple)
        assert result is True

    def test_update_capability(self):
        result = self.worker.update_capability("username", self.cap_water)
        assert result is True


class Test_Redis(BaseWorkerAPI):
    @classmethod
    def setup_class(cls):
        cls.worker = RedisWorker("name")


class Test_Postgressql(BaseWorkerAPI):
    @classmethod
    def setup_class(cls):
        cls.worker = WorkerAPI()


#     def test_specific(self):
#         assert True

#     def test_impl2(self):
#         assert True is True


# class Test_Mock(Test_WorkerAPI):
#     @classmethod
#     def setup_class(cls):
#         cls.worker = WorkerAPI()
