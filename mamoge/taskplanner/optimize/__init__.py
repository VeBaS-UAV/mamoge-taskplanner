from abc import abstractmethod
from mamoge.taskplanner.optimize.ortools import ORTaskOptimizer
import networkx as nx

class TaskOptimizer:


    def __init__(self) -> None:
        self.graph = None
        self.impl = ORTaskOptimizer()
        pass

    def set_graph(self, G:nx.Graph)-> None:
        """set the problem graph to be optimized"""
        self.graph = G

    @abstractmethod
    def solve(self, time=30):
        """Solve the optimization problem"""
        self.impl.set_graph(self.graph)
        return self.impl.solve(time)
