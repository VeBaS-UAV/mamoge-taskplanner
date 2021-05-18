from abc import abstractmethod
from mamoge.taskplanner.optimize.ortools import ORTaskOptimizer
import networkx as nx

class TaskOptimizer:


    def __init__(self) -> None:
        self.dag = None
        self.impl = ORTaskOptimizer()
        pass

    def set_dag(self, G:nx.Graph)-> None:
        """set the problem graph to be optimized"""
        self.dag = G

    @abstractmethod
    def solve(self, time=30):
        """Solve the optimization problem"""
        self.impl.set_dag(self.dag)
        return self.impl.solve(time)
