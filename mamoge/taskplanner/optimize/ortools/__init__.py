from abc import abstractmethod
from mamoge.taskplanner.location import cached_result
import networkx as nx
from mamoge.taskplanner import nx as mamogenx

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import numpy as np
from typing import Callable
from mamoge.taskplanner.optimize import TaskOptimizer
import logging

#logging.getLogger().removeHandler()
#[logging.getLogger().removeHandler(h) for h in logging.getLogger().handlers]
#logging.getLogger().addHandler(logging.StreamHandler())
logging.getLogger().setLevel(logging.DEBUG)

import time

class ORTaskOptimizer(TaskOptimizer):


    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.manager: pywrapcp.RoutingIndexManager = None
        self.distance_callback_counter = 0
        self.distance_callback_counter_fail = 0
        self.vel_meter_per_sec = 1 # / 3.6 # 6km/h
        #
        self.dimensions = {}
        self.capacities = {}
        self.penalty_dimension = "steps"
        pass

    def add_dimension(self, name:str, cost_callback:Callable[[nx.Graph, int, int],int], capacity=None, slack=0):
        self.logger.debug("adding dimension %s" , name)
        self.dimensions[name] = dict(cost_callback=cost_callback, capacity=capacity, slack=slack)

    def add_capacity(self, name:str, capacity_callback:Callable[[nx.Graph,int],int], capacity=None, slack=0):
        self.capacities[name]= dict(capacity_callback=capacity_callback, capacity=capacity, slack=slack)


    @abstractmethod
    def solve(self, max_time=30, constraints=[]):
        """Solve the optimization problem"""
        # breakpoint()
        self.graph = mamogenx.G_problem_from_dag(self.graph)
        num_nodes = len(self.graph.nodes)
        num_routes = 1
        #print("Solving dag", self.dag)
        # node_start = mamogenx.G_first(self.graph)
        # node_end = mamogenx.G_last(self.graph)
        node_start = 0
        node_end = len(self.graph)-1

        # map from index to graph node id
        G_idx2node = list(self.graph.nodes)

        self.logger.info(f"Solving DAG from start to end {node_start}->{node_end}")

        self.manager = pywrapcp.RoutingIndexManager(num_nodes, num_routes, [node_start],[node_end])
        routing_parameters = pywrapcp.DefaultRoutingModelParameters()
        # routing_parameters.solver_parameters.trace_propagation = True
        # routing_parameters.solver_parameters.trace_search = True
        self.routing = pywrapcp.RoutingModel(self.manager, routing_parameters)

        has_arc_def = False
        for dim_name, dim_args in self.dimensions.items():
            self.logger.info(f"Adding dimension {dim_name} with args {dim_args}")
            dim_cost_callback = dim_args["cost_callback"]
            slack = dim_args["slack"] if dim_args["slack"] is not None else 0
            capacity = dim_args["capacity"] if dim_args["capacity"] is not None else 300000000
            fix_start_cumul_to_zero = True

            # cost_matrix = mamogenx.G_cost_matrix(self.graph, lambda u,v: dim_cost_callback(self.graph, u,v))

            dim_matrix = np.zeros((len(self.graph), len(self.graph)))

            def cost_callback(from_index, to_index):
                #TODO transform callback to matrix for better performance
                #
                if dim_matrix[from_index, to_index] > 0:
                    # print("cache hit", from_index, to_index)
                    return dim_matrix[from_index, to_index]
                try:
                    # print("query", from_index, to_index)
                    from_node = G_idx2node[self.manager.IndexToNode(from_index)]
                    to_node = G_idx2node[self.manager.IndexToNode(to_index)]
                    # print('dim_cost_callback', from_node, to_node)
                    val =  dim_cost_callback(self.graph, from_node, to_node)
                    # print("cost_callback", from_index, to_index, cost_callback, val)

                    dim_matrix[from_index, to_index] = val

                    return val
                except Exception as e:
                    self.logger.error(f"cost_callback error ({from_index}, {to_index}), {cost_callback}")
                    self.logger.error(e)
                    return -1

            callback_index = self.routing.RegisterTransitCallback(cost_callback)

            if has_arc_def == False:
                self.logger.info(f"Setting ArcCost to dimension {dim_name}")
                # Define cost of each arc.
                self.routing.SetArcCostEvaluatorOfAllVehicles(callback_index)

                has_arc_def = True
            self.logger.info(f"Adding dimension {dim_name}: {slack}, {capacity}, {fix_start_cumul_to_zero}")
            self.routing.AddDimension(
                   callback_index,
                   slack,
                   capacity,
                   fix_start_cumul_to_zero,
                   dim_name)
            dimension = self.routing.GetDimensionOrDie(dim_name)
            dimension.SetGlobalSpanCostCoefficient(1)

        for cap_name, cap_args in self.capacities.items():
            self.logger.info(f"Adding capacity dimension {cap_name} with args {cap_args}")

            cap_cost_callback = cap_args["capacity_callback"]
            slack = cap_args["slack"] if cap_args["slack"] is not None else 0
            capacity = cap_args["capacity"] if cap_args["capacity"] is not None else 100000000
            fix_start_cumul_to_zero = True

            # capacity_vector = mamogenx.G_cost_vector(self.graph, lambda u: cap_cost_callback(self.graph, u))
            def capacity_callback(index):
                # print("capacity callback", index)
                node = self.manager.IndexToNode(index)
                return int(cap_cost_callback(self.graph, node))

            capacity_callback_index = self.routing.RegisterUnaryTransitCallback(capacity_callback)

            self.routing.AddDimensionWithVehicleCapacity(
                capacity_callback_index,
                slack,
                [capacity]*num_routes,
                fix_start_cumul_to_zero,
                cap_name
            )

            dimension = self.routing.GetDimensionOrDie(cap_name)
            dimension.SetGlobalSpanCostCoefficient(1)

        for constraint in constraints:
            u = constraint.u
            v = constraint.v
            self.logger.info(f"Adding constraint {constraint}")
            first_index = self.manager.NodeToIndex(u)
            second_index = self.manager.NodeToIndex(v)
            # same vehicle for every node in the sequence
            #self.routing.solver().Add(self.routing.VehicleVar(first_index) == self.routing.VehicleVar(second_index))

            kw_args = constraint.kw_args

            dimension = self.routing.GetDimensionOrDie(constraint.dimension)

            if "min" in kw_args:
                #TODO dynamic select dimension
                min_value = kw_args["min"]
                dim_str = constraint.dimension
                constrain_arg = (dimension.CumulVar(first_index) + min_value) <= dimension.CumulVar(second_index)
                self.routing.solver().Add(constrain_arg)
                #print("Adding min constraint", u,v,dim_str, min_value)


            if "max" in kw_args:
                #TODO dynamic select dimension
                max_value = kw_args["max"]
                dim_str = constraint.dimension
                constrain_arg = (dimension.CumulVar(first_index) + max_value) <= dimension.CumulVar(second_index)
                self.routing.solver().Add(constrain_arg)
                #print("Adding max constraint", u,v,dim_str, min_value)
                raise "Not implemented"
        # Allow to drop nodes.
        penalty = 24*60*60
        self.logger.info("Adding Penalty")
        dimension = self.routing.GetDimensionOrDie(self.penalty_dimension)
        for node in range(1, num_nodes -1):
            self.logger.debug(f"Add penality {node}, {self.manager.NodeToIndex(node)}")
            i = self.manager.NodeToIndex(node)
            self.routing.AddDisjunction([i], penalty)
            slackVar = dimension.SlackVar(i)
            #slackVar.SetMax(1200)
            self.routing.AddToAssignment(slackVar)
            pass


        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        # search_parameters.log_search = True
        # search_parameters.first_solution_strategy = (routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
        # search_parameters.first_solution_strategy = (routing_enums_pb2.FirstSolutionStrategy.PATH_MOST_CONSTRAINED_ARC)
        # search_parameters.first_solution_strategy = (routing_enums_pb2.FirstSolutionStrategy.BEST_INSERTION)
        # search_parameters.first_solution_strategy = (routing_enums_pb2.FirstSolutionStrategy.ALL_UNPERFORMED)
        # search_parameters.first_solution_strategy = (routing_enums_pb2.FirstSolutionStrategy.LOCAL_CHEAPEST_ARC)
        # search_parameters.first_solution_strategy = (routing_enums_pb2.FirstSolutionStrategy.GLOBAL_CHEAPEST_ARC)
        search_parameters.first_solution_strategy = (routing_enums_pb2.FirstSolutionStrategy.FIRST_UNBOUND_MIN_VALUE)
        # search_parameters.first_solution_strategy = (routing_enums_pb2.FirstSolutionStrategy.SWEEP)

        # search_parameters.local_search_metaheuristic = (routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
        # search_parameters.local_search_metaheuristic = (routing_enums_pb2.LocalSearchMetaheuristic.TABU_SEARCH)
        search_parameters.time_limit.FromSeconds(max_time)

        # init_route =[[1, 2,3,4,5,6]]
        # init_route =[[0, 9, 7, 19, 17, 21]]
        # init_route =[[0, 9, 7, 17, 19, 21]]
        # init_route =[[1,2,3,4,5,6]]
        # init_route =[[1,2,3,4,6]]
        # init_route =[list(range(1,num_nodes-1))]

        # print('raw init solution', init_route)
        # initial_solution = self.routing.ReadAssignmentFromRoutes(init_route, True)

        # print("Initial Solution", initial_solution)
        # breakpoint()
        # if initial_solution:
            # self.extract_solution(num_routes, self.manager, self.routing, initial_solution)
            # return [], []
        # else:
            # return [],[]
            # pass
        self.logger.info("Solving task ...")
        time.sleep(1)

        initial_solution = None
        if initial_solution:
            solution = self.routing.SolveFromAssignmentWithParameters(initial_solution, search_parameters)
        else:
            solution = self.routing.SolveWithParameters(search_parameters)

        self.logger.info("Done")

        if solution is None:
            return [], []

        result, meta =  self.extract_solution(num_routes, self.manager, self.routing, solution)

        self.logger.debug(f"{result}")

        return [G_idx2node[n] for n in result[0]]

    def extract_values(self, solution, dim, index, prev_index, vehicle_id):
        results = {}

        cum = dim.CumulVar(index)
        results[self.penalty_dimension] = solution.Min(cum)#, solution.Max(cum)
        results["slack"] = 0
        results["transit"] = 0#dim.GetTransitValue(index)
        if(prev_index>=0):
            cum_prev = dim.CumulVar(prev_index)
            d_cost = solution.Min(cum) - solution.Min(cum_prev)#, solution.Max(cum) - solution.Max(cum_prev),
            # print("extract_values", dim, index, prev_index)
            results["transit"] = dim.GetTransitValue(prev_index, index, vehicle_id)
            results["slack"] = d_cost - results["transit"]

        return results

    def extract_solution(self, num_routes, manager, routing, solution):
        """Prints solution on console."""
        # print(f'Objective: {solution.ObjectiveValue()}')

        time_dim = routing.GetDimensionOrDie(self.penalty_dimension)
        total_time = 0

        results = []
        results_meta = []

        # max_route_distance = 0
        for vehicle_id in range(num_routes):
            # print("Vehicle ID", vehicle_id)
            route = []
            route_meta = {}#[]
            index = routing.Start(vehicle_id)
            prev_index = -1
            plan_output = 'Route for vehicle {}:\n'.format(vehicle_id)
            # print("Transits", time_dim.CumulVar(index))
            # route_distance = 0
            while not routing.IsEnd(index):
                node = manager.IndexToNode(index)
                route.append(node)
                # plan_output += ' {} -> '.format(manager.IndexToNode(index))
                time_var  = time_dim.CumulVar(index)
                #slack_var = time_dim.SlackVar(index)
                #transit_var = time_dim.TransitVar(index)

                route_meta[node] = self.extract_values(solution, time_dim, index, prev_index, vehicle_id)

                #route_meta[node]["time"] = solution.Min(time_var), solution.Max(time_var)
                #print("Transit var", transit_var, solution.Value(transit_var))
                #route_meta[node]["slack"] = slack_var.Min(), slack_var.Max()
                #route_meta[node]["transit"] = transit_var.Min(), transit_var.Max()
                #route_meta[node]["transit"] = solution.Min(transit_var), solution.Max(transit_var)

                #(solution.Min(time_var), solution.Max(time_var), time_dim.SlackVar(index))
                plan_output += '{0} Time({1},{2}) -> '.format(
                    manager.IndexToNode(index), solution.Min(time_var),
                    solution.Max(time_var))

                prev_index = index
                index = solution.Value(routing.NextVar(index))

                # route_distance += routing.GetArcCostForVehicle(
                    # previous_index, index, vehicle_id)
                    #
            node = manager.IndexToNode(index)
            time_var = time_dim.CumulVar(index)
            # slack_var = time_dim.SlackVar(index)
            #transit_var = time_dim.TransitVar(index)


            plan_output += '{0} Step({1},{2})\n'.format(node,
                                                    solution.Min(time_var),
                                                    solution.Max(time_var))
            plan_output += 'Time of the route: {}sec\n'.format(
                solution.Min(time_var))
            # print(plan_output)
            total_time += solution.Min(time_var)

            route_meta[node] = self.extract_values(solution, time_dim, index, prev_index, vehicle_id)

            route.append(manager.IndexToNode(index))

            results.append(route)
            results_meta.append(route_meta)
            # plan_output += '{}\n'.format(manager.IndexToNode(index))
            # plan_output += 'Distance of the route: {}m\n'.format(route_distance)
            # print(plan_output)
            # max_route_distance = max(route_distance, max_route_distance)
        #print('Maximum of the route distances: {}m'.format(max_route_distance))
        return results, results_meta
