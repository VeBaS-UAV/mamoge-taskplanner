from mamoge.api.planner import TaskPlannerBase, TaskplannerRedisAPI
from mamoge.models.capabilities import Capability, Capabilities
from mamoge.models.capabilities import Requirement, Requirements
from mamoge.models.capabilities import RequirementTime
from mamoge.models.tasks import Task


class BasePlannerAPI:
    """Global test cases that are meant to be run for every child class.

    Child classes are different implementations of the Baseclass,
    e.g. with different DB connections and corresponding specifications.

    Note: does not start with `Test_` to avoid running the base class tests.
    """

    @classmethod
    def setup_class(cls):
        cls.worker: TaskPlannerBase

        cls.cap_water = Capability("water", 10)
        cls.cap_energy = Capability("energy", 15)
        cls.cap_multiple = Capabilities([cls.cap_water, cls.cap_energy])

        cls.req_energy = Requirement("energy", 10)
        cls.req_time = RequirementTime("time_window", 1100, 1300)

        cls.t1 = Task(
            id="t1",
            name="t1",
            requirements=Requirements([cls.req_energy]),
            time=cls.req_time,
        )

    def test_time_requirement(self):
        # check if a task meets the time requirement
        assert False


class Test_PlannerRedisAPI(BasePlannerAPI):
    """Implements the Task Planner with a Redis connection.

    It inherits the base classes' test functions. Therefore only test for function
    implementations that are specific for the redis connection are defined here.
    """

    @classmethod
    def setup_class(cls):
        cls.worker = TaskplannerRedisAPI()
