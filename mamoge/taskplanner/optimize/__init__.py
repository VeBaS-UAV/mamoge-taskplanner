from abc import abstractmethod
import networkx as nx
import mamoge.taskplanner.nx as mamogenx
from mamoge.taskplanner.optimize.ortools import ORTaskOptimizer

class TaskOptimizer:


    def __init__(self) -> None:
        self.graph = None
        self.impl = ORTaskOptimizer()
        pass

    def set_graph(self, G:nx.Graph)-> None:
        """set the problem graph to be optimized"""
        # self.graph = G
        self.impl.graph = G

    @abstractmethod
    def solve(self, time=30, constraints=[]):
        """Solve the optimization problem"""
        # raise "solve not implemented"
        return self.impl.solve(time, constraints=constraints)
