#!/usr/bin/env python3

from typing import List
from mamoge.models.capabilities import (
    Capabilities,
    Capability,
    Requirement,
    Requirements,
)
from mamoge.models.process_board import ProcessBoard

from mamoge.models.tasks import DAG, Task, TaskEvent, TaskState


def generate_board_example_2():
    dag = DAG("Test_DAG")

    t1 = Task(
        1, "T1", requirements=Requirements(Requirement("water", 10, consumes=True))
    )
    t2 = Task(
        2, "T2", requirements=Requirements(Requirement("water", 20, consumes=True))
    )
    t3 = Task(
        3, "T3", requirements=Requirements(Requirement("water", 10, consumes=True))
    )
    t4 = Task(
        4, "T4", requirements=Requirements(Requirement("water", 10, consumes=True))
    )
    t5 = Task(
        5, "T5", requirements=Requirements(Requirement("water", 10, consumes=True))
    )

    t6 = Task(
        6, "T6", requirements=Requirements(Requirement("water", 15, consumes=True))
    )

    t7 = Task(
        7, "T7", requirements=Requirements(Requirement("water", 15, consumes=True))
    )
    t8 = Task(
        8, "T8", requirements=Requirements(Requirement("water", 20, consumes=True))
    )
    t9 = Task(
        9, "T9", requirements=Requirements(Requirement("water", 20, consumes=True))
    )

    t10 = Task(
        10, "T10", requirements=Requirements(Requirement("water", 60, consumes=True))
    )

    # t5 = Task(5, "Task5")
    #
    dag += t1
    dag += t2
    dag += t3
    dag += t4
    dag += t5
    dag += t6
    dag += t7
    dag += t8
    dag += t9
    dag += t10

    dag.set_downstream(t1, t2)
    dag.set_downstream(t2, t3)
    dag.set_downstream(t2, t4)
    dag.set_downstream(t4, t5)
    dag.set_downstream(t3, t6)
    dag.set_downstream(t5, t6)
    dag.set_downstream(t6, t7)
    dag.set_downstream(t5, t8)
    dag.set_downstream(t8, t9)

    pboard = ProcessBoard()
    pboard.execute(dag)

    return pboard


def generate_board_example_1():

    dag = DAG("Test_DAG")

    t1 = Task(
        1, "Task1", requirements=Requirements(Requirement("water", 10, consumes=True))
    )
    t2 = Task(
        2, "Task2", requirements=Requirements(Requirement("water", 10, consumes=True))
    )
    t3 = Task(
        3, "Task3", requirements=Requirements(Requirement("water", 10, consumes=True))
    )
    t4 = Task(
        4, "Task4", requirements=Requirements(Requirement("water", 10, consumes=True))
    )
    t5 = Task(
        5, "Task5", requirements=Requirements(Requirement("water", 10, consumes=True))
    )
    # t5 = Task(5, "Task5")
    #
    dag += t1
    dag += t2
    dag += t3
    dag += t4
    dag += t5

    dag.set_downstream(t1, t2)
    dag.set_downstream(t2, t3)
    dag.set_downstream(t2, t4)
    dag.set_downstream(t4, t5)

    pboard = ProcessBoard()
    pboard.execute(dag)

    return pboard


def test_initialization():
    pboard = generate_board_example_1()

    assert len(pboard.tasks()) == 5


def test_default_openlist():
    pboard = generate_board_example_1()

    ol = pboard.get_openlist()

    assert len(ol) == 1


def test_task_states():
    pboard = generate_board_example_1()

    task: Task = pboard.get_openlist()[0]
    assert task.state == TaskState.AVAILABLE

    # event of planning happens
    pboard.event_input(task.id, TaskEvent.PLAN)
    assert task.state == TaskState.PLANNED

    # event of queud / accapting happens
    pboard.event_input(task.id, TaskEvent.ACCEPT)
    assert task.state == TaskState.QUEUED

    # task switches from queued to active
    pboard.event_input(task.id, TaskEvent.START)
    assert task.state == TaskState.RUNNING

    # task switches from running to completed
    pboard.event_input(task.id, TaskEvent.COMPLETED)
    assert task.state == TaskState.COMPLETED

    # task switches from running to completed
    task.state = TaskState.RUNNING
    pboard.event_input(task.id, TaskEvent.ERROR)
    assert task.state == TaskState.FAILURE


def test_no_tasks_available():
    pboard = generate_board_example_1()

    task: Task = pboard.get_openlist()[0]
    assert task.state == TaskState.AVAILABLE

    # event of planning happens
    pboard.event_input(task.id, TaskEvent.PLAN)
    assert task.state == TaskState.PLANNED

    available_tasks = pboard.get_openlist()
    assert len(available_tasks) == 0


def test_subgraph_query():
    pboard = generate_board_example_1()

    task: Task = pboard.get_openlist()[0]
    assert task.state == TaskState.AVAILABLE

    task.state = TaskState.RUNNING
    pboard.event_input(task.id, TaskEvent.COMPLETED)
    assert task.state == TaskState.COMPLETED

    available_tasks = pboard.get_openlist()
    assert len(available_tasks) == 1

    # update current task and complete it
    task: Task = pboard.get_openlist()[0]

    task.state = TaskState.RUNNING
    pboard.event_input(task.id, TaskEvent.COMPLETED)
    assert task.state == TaskState.COMPLETED

    available_tasks = pboard.get_openlist()
    assert len(available_tasks) == 2


def test_capabiltiy_query():

    pboard = generate_board_example_1()

    tasks: List[Task] = pboard.get_openlist()
    assert len(tasks) == 1

    cap = Capabilities(Capability("water", 20))
    tasks: List[Task] = pboard.get_openlist(capabilities=cap)
    assert len(tasks) == 1

    # tasks[0].set_state(TaskState.COMPLETED)
    task = tasks[0]
    pboard.event_input(task.id, TaskEvent.PLAN)
    pboard.event_input(task.id, TaskEvent.ACCEPT)
    pboard.event_input(task.id, TaskEvent.START)
    pboard.event_input(task.id, TaskEvent.COMPLETED)

    cap = Capabilities(Capability("water", 20))
    tasks: List[Task] = pboard.get_openlist(capabilities=cap)
    assert len(tasks) == 1
    assert tasks[0].local_id == 2

    cap = Capabilities(Capability("water", 5))
    tasks: List[Task] = pboard.get_openlist(capabilities=cap)
    assert len(tasks) == 0

    cap = Capabilities(Capability("water", 25), Capability("temp", 50))
    tasks: List[Task] = pboard.get_openlist(capabilities=cap)
    assert len(tasks) == 1

    task = tasks[0]
    pboard.event_input(task.id, TaskEvent.PLAN)
    pboard.event_input(task.id, TaskEvent.ACCEPT)
    pboard.event_input(task.id, TaskEvent.START)
    pboard.event_input(task.id, TaskEvent.COMPLETED)

    tasks: List[Task] = pboard.get_openlist(capabilities=cap)
    assert len(tasks) == 2


def test_tasklist_query():

    pboard = generate_board_example_1()

    tasks: List[Task] = pboard.get_openlist()
    assert len(tasks) == 1


def test_tasklist_query_w_capabilities():

    pboard = generate_board_example_1()

    tasklists: List[List[Task]] = pboard.get_tasklists()
    assert len(tasklists) == 2
    assert len(tasklists[0]) == 3
    assert len(tasklists[1]) == 4

    cap = Capabilities(Capability("water", 20))
    tasklists: List[List[Task]] = pboard.get_tasklists(capabilities=cap)

    assert len(tasklists) == 2
    assert len(tasklists[0]) == 2
    assert len(tasklists[1]) == 2

    cap = Capabilities(Capability("water", 30))
    tasklists: List[List[Task]] = pboard.get_tasklists(capabilities=cap)

    assert len(tasklists) == 2
    assert len(tasklists[0]) == 3
    assert len(tasklists[1]) == 3

    cap = Capabilities(Capability("water", 40))
    tasklists: List[List[Task]] = pboard.get_tasklists(capabilities=cap)

    assert len(tasklists) == 2
    assert len(tasklists[0]) == 3
    assert len(tasklists[1]) == 4
