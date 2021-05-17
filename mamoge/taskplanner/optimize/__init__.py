from abc import abstractmethod
import networkx as nx

class TaskOptimizer:


    def __init__(self) -> None:
        self.dag = None
        pass

    def set_dag(self, G:nx.Graph)-> None:
        """set the problem graph to be optimized"""
        self.dag = G

    @abstractmethod
    def solve(self):
        """Solve the optimization problem"""
        pass
