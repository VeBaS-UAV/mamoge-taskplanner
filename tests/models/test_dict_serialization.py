#!/usr/bin/env python3


from mamoge.models.capabilities import (
    Capabilities,
    Capability,
    CapabilityBag,
    Requirement,
    Requirements,
)

from mamoge.models.tasks import TaskSyncPoint, DAG, Task


def test_requirement():

    r = Requirement(name="water", value=10)

    dict_r = r.to_dict()

    r_new = Requirement.from_dict(dict_r)

    assert str(r) == str(r_new)
    assert str(dict_r) == str(r_new.to_dict())


def test_capability():

    c = Capability(name="water", value=10)

    dict_c = c.to_dict()

    c_new = Capability.from_dict(dict_c)

    assert str(c) == str(c_new)
    assert str(dict_c) == str(c_new.to_dict())


def test_requirements():

    r = Requirement(name="water", value=10)

    rs = Requirements([r])
    dict_rs = rs.to_dict()

    rs_new = Requirements.from_dict(dict_rs)

    assert str(rs) == str(rs_new)
    assert str(dict_rs) == str(rs_new.to_dict())


def test_capabilities():

    c = Capability(name="water", value=10)

    cs = Capabilities([c])
    dict_cs = cs.to_dict()

    cs_new = Capabilities.from_dict(dict_cs)

    assert str(cs) == str(cs_new)
    assert str(dict_cs) == str(cs_new.to_dict())


def test_task():

    t1 = Task(
        1,
        "T1",
        requirements=Requirements([Requirement(name="water", value=10, consumes=True)]),
    )

    dict_t = t1.to_dict()

    t1_new = Task.from_dict(dict_t)

    assert str(t1) == str(t1_new)
    assert str(dict_t) == str(t1_new.to_dict())


def test_dag():
    dag = DAG("Test_DAG")

    t1 = Task(
        1,
        "T1",
        requirements=Requirements([Requirement(name="water", value=10, consumes=True)]),
    )
    t2 = Task(
        2,
        "T2",
        requirements=Requirements([Requirement(name="water", value=10, consumes=True)]),
    )
    t3 = Task(
        3,
        "T3",
        requirements=Requirements([Requirement(name="water", value=10, consumes=True)]),
    )
    t4 = Task(
        4,
        "T4",
        requirements=Requirements([Requirement(name="water", value=10, consumes=True)]),
    )
    t5 = Task(
        5,
        "T5",
        requirements=Requirements([Requirement(name="water", value=10, consumes=True)]),
    )
    #

    ts1 = TaskSyncPoint(10, "TS1")
    ts2 = TaskSyncPoint(20, "TS2")

    dag += t1
    dag += t2

    dag += ts1

    dag += t3
    dag += t4
    dag += t5

    # dag += t7
    # dag += t8
    # dag += t9

    dag.set_downstream(t1, t2)
    dag.set_downstream(t2, ts1)

    dag.set_downstream(ts1, t3)
    dag.set_downstream(ts1, t4)

    dag.set_downstream(t3, ts2)
    dag.set_downstream(t4, ts2)

    dag.set_downstream(ts2, t5)

    dict_dag = dag.to_dict()

    dag_new = DAG.from_dict(dict_dag)

    assert str(dag) == str(dag_new)

    print(dict_dag)
    print("####")
    print(dag_new.to_dict())

    assert str(dict_dag) == str(dag_new.to_dict())
