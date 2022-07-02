import functools
from itertools import chain
from itertools import permutations
from multiprocessing import Pool

import acopy
import networkx as nx
import numpy as np

from mamoge.taskplanner import nx as mamogenx


class VebasAnt(acopy.ant.Ant):

    def __init__(self, alpha=1, beta=3):
        super().__init__(alpha, beta)

    def get_starting_node(self, graph):
        """Return a starting node for an ant.

        :param graph: the graph being solved
        :type graph: :class:`networkx.Graph`
        :return: node
        """
        return 0

    def tour(self, graph):
        """Find a solution to the given graph.
        :param graph: the graph to solve
        :type graph: :class:`networkx.Graph`
        :return: one solution
        :rtype: :class:`~acopy.solvers.Solution`
        """

        solution = self.initialize_solution(graph)
        unvisited = self.get_unvisited_nodes(graph, solution)

        max_nodes = 25
        while unvisited and len(solution.path) < max_nodes:
            node = self.choose_destination(graph, solution.current, unvisited)
            solution.add_node(node)
            unvisited.remove(node)

        # ipdb.set_trace()
        solution.close()

        # print('solution', solution)
        return solution

    def score_edge(self, edge):
        """Return the score for the given edge.

        :param dict edge: the edge data
        :return: score
        :rtype: float
        """
        weight = edge.get("weight", 1)
        if weight == 0:
            return 0
        pre = 1 / weight
        post = edge["pheromone"]
        return post**self.alpha * pre**self.beta


class VebasColony(acopy.ant.Colony):

    def __init__(self, alpha=1, beta=3):
        super().__init__(alpha, beta)

    def get_ants(self, count):
        """Return the requested number of :class:`~acopy.ant.Ant` s.

        :param int count: number of ants to return
        :rtype: list
        """

        return [VebasAnt(**vars(self)) for __ in range(count)]


def _call(func, *args):
    return func(*args)


def _call_ant_tour(ant, graph):
    return ant.tour(graph)


def _call_mp(self, *args):
    ants = args[0][0]
    graph = args[0][1]

    return list(chain([ant.tour(graph) for ant in ants]))


class VebasMPSolver(acopy.Solver):

    def __init__(self, rho, q, top=None, plugins=None, num_processes=None):
        super().__init__(rho=rho, q=q, top=top, plugins=plugins)
        self.num_processes = num_processes if num_processes else 5
        self.mp = Pool(self.num_processes)

    def find_solutions(self, graph, ants):

        ant_chunks = [
            ants[i::self.num_processes] for i in range(self.num_processes)
        ]

        _ant_call_w_graph = functools.partial(_call_ant_tour, graph=graph)

        # results = self.mp.map(_ant_call_w_graph, [ant for ant in ants])

        results = [_ant_call_w_graph(ant) for ant in ants]

        # result_list = self.mp.map(_call_mp, [(ant_chunk, graph)
        #                                      for ant_chunk in ant_chunks])
        # result_list = self.mp.map(_call,
        #                           [(ant, graph) for ant_chunk in ant_chunks])

        # results = []
        # for r in result_list:
        #     results.extend(r)

        # ipdb.set_trace()

        return results

    def global_update(self, state):
        """Perform a global pheromone update.
        :param state: solver state
        :type state: :class:`~State`
        """
        # ipdb.set_trace()
        for edge in state.graph.edges:
            amount = 0
            if self.top:
                solutions = state.solutions[:self.top]
            else:
                solutions = state.solutions
            for solution in solutions:
                if edge in solution.path:
                    amount += self.q / solution.cost
            p = state.graph.edges[edge]["pheromone"]
            state.graph.edges[edge]["pheromone"] = (1 - self.rho) * p + amount


class ACOTaskOptimizer:

    def __init__(self) -> None:
        self.graph: nx.Graph = None

    def set_graph(self, G: nx.Graph) -> None:
        """set the problem graph to be optimized"""
        self.graph = G

    def solve(self, time=30, constrains=[]):
        """Solve the optimization problem."""
        num_nodes = len(self.graph.nodes)
        num_routes = 1
        # print("Solving dag", self.dag)
        node_start = mamogenx.G_first(self.graph)
        node_end = mamogenx.G_last(self.graph)

        print("Calculating distance matrix")
        distance_matrix = mamogenx.G_distance_matrix(self.graph,
                                                     distance_fallback=np.nan)

        print("Distance matrix", distance_matrix)

        pmatrix = distance_matrix / np.nansum(distance_matrix, axis=1)[:, None]
        pmatrix = np.nan_to_num(pmatrix, 0)
        print("pmatrix", pmatrix)

        G = nx.Graph()

        for i, j in permutations(range(0, pmatrix.shape[0]), 2):
            d_ij = pmatrix[i, j]
            d_i0 = pmatrix[i, 0]
            d_j0 = pmatrix[j, 0]

            d_ij0 = abs(d_i0 - d_j0)

            # print(d_ij, d_ij0)
            G.add_edge(i, j, weight=d_ij + d_ij0, pheromone=1.0)

        # ipdb.set_trace()
        stats_recorder = acopy.plugins.StatsRecorder()
        time_limit = acopy.plugins.TimeLimit(10)

        solver = VebasMPSolver(
            rho=0.3,
            q=1,
            top=5,
            plugins=[
                acopy.plugins.Printout(),
                acopy.plugins.EliteTracer(),
                stats_recorder,
                time_limit,
            ],
        )
        colony = VebasColony(alpha=1, beta=3)

        print("solving...")
        # %%

        tour = solver.solve(G, colony, limit=100, gen_size=500)

        best_path = tour.nodes

        return [best_path]
