from mamoge.api.planner import TaskPlannerBase, TaskplannerRedisAPI
from mamoge.models.capabilities import Capabilities, Capability


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

        # cls.t1 = Task(id=, name=, requirements=, state=)


class Test_PlannerRedisAPI(BasePlannerAPI):
    """Implements the Task Planner with a Redis connection.

    It inherits the base classes' test functions. Therefore only test for function
    implementations that are specific for the redis connection are defined here.
    """

    @classmethod
    def setup_class(cls):
        cls.worker = TaskplannerRedisAPI()
