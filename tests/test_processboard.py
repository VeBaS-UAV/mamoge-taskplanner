from mamoge.api.processboard import ProcessBoardAPI, ProcessBoardRedisAPI
from mamoge.models.capabilities import Capabilities, Capability


class BaseProcessBoardAPI:
    """Global test cases that are meant to be run for every child class.

    Child classes are different implementations of the Baseclass,
    e.g. with different DB connections and corresponding specifications.

    Note: does not start with `Test_` to avoid running the base class tests.
    """

    @classmethod
    def setup_class(cls):
        cls.board = ProcessBoardAPI()

        cls.cap_water = Capability("water", 10)
        cls.cap_energy = Capability("energy", 15)
        cls.cap_multiple = Capabilities(cls.cap_water, cls.cap_energy)


class Test_ProcessBoardRedis(BaseProcessBoardAPI):
    """Implements the Process Board with a Redis connection.

    It inherits the base classes' test functions. Therefore only test for function
    implementations that are specific for the redis connection are defined here.
    """

    @classmethod
    def setup_class(cls):
        cls.worker = ProcessBoardRedisAPI("name")
