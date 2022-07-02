from mamoge_helpers import graph_helper
import numpy as np
import mamoge.taskplanner.nx as mamogenx

from mamoge.taskplanner.optimize import TaskOptimizer
# %%


def test_simple_graph_solver():
    # create default example graph
    G = graph_helper.example_graph_1()

    # check graph length
    assert len(set(G.nodes).difference(set(np.arange(7)))) == 0

    assert len(G.edges) == 9

    # build problem graph
    Gn = mamogenx.G_problem_from_dag(G)

    assert len(Gn.edges) == 34

    # find solution

    taskoptimizer = TaskOptimizer()
    taskoptimizer.set_graph(Gn)

    results = taskoptimizer.solve(time=1)

    path = results[0]

    assert len(set(path).difference(set([0, 3, 2, 1, 4, 5]))) == 0

# %%


def test_extended_graph_solver():

    # create extended example graph
    G = graph_helper.example_graph_2()

    # check graph length
    assert len(set(G.nodes).difference(set(np.arange(14)))) == 0

    assert len(G.edges) == 18

    # build problem graph
    Gn = mamogenx.G_problem_from_dag(G)

    assert len(Gn.edges) == 72

    # find solution

    taskoptimizer = TaskOptimizer()
    taskoptimizer.set_graph(Gn)

    results = taskoptimizer.solve(time=1)

    path = results[0]

    assert len(set(path).difference(
        set([0, 3, 2, 1, 4, 5, 6, 9, 8, 7, 11, 10, 12]))) == 0
