from abc import abstractmethod

import networkx as nx

from mamoge.taskplanner.optimize.ortools import ORTaskOptimizer


class TaskOptimizer:

    def __init__(self) -> None:
        self.graph = None
        self.impl = ORTaskOptimizer()
        pass

    def set_graph(self, G: nx.Graph) -> None:
        """Set the problem graph to be optimized."""
        # self.graph = G
        self.impl.graph = G

    @abstractmethod
    def solve(self, time=30, constraints=None):
        """Solve the optimization problem."""
        if constraints is None:
            constraints = []
        # raise "solve not implemented"
        return self.impl.solve(time, constraints=constraints)
