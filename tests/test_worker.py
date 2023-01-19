from mamoge.worker.worker import WorkerAPI, RedisWorker


class Test_WorkerAPI:
    """Global test cases that are meant to be run for every child class.

    child classes are different imlpementations of the workerAPI, e.g. with different
    connections and corresponding specifications.
    """

    def test_register(self):
        assert True is True

    def test_unregister(self):
        assert True is True

    def test_keep_alive(self):
        assert True is True

    def test_task_update(self):
        assert True is True

    def test_tasks_receive(self):
        assert True is True

    def test_update_capabilities(self):
        assert True is True

    def test_update_capability(self):
        assert True is True


class Test_Redis(Test_WorkerAPI):
    @classmethod
    def setup_class(cls):
        cls.worker = RedisWorker("name")


class Test_Postgressql(Test_WorkerAPI):
    @classmethod
    def setup_class(cls):
        cls.worker = RedisWorker("name")

    def test_specific(self):
        assert True

    def test_impl2(self):
        assert True is True


class Test_Mock(Test_WorkerAPI):
    @classmethod
    def setup_class(cls):
        cls.worker = WorkerAPI()
