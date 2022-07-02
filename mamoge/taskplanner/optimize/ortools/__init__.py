from abc import abstractmethod
import logging
import time
from typing import Callable

from ortools.constraint_solver import pywrapcp
from ortools.constraint_solver import routing_enums_pb2
import networkx as nx
import numpy as np

from mamoge.taskplanner import nx as mamogenx

# logging.getLogger().removeHandler()
# [logging.getLogger().removeHandler(h) for h in logging.getLogger().handlers]
# logging.getLogger().addHandler(logging.StreamHandler())
logging.getLogger().setLevel(logging.DEBUG)


class ORTaskOptimizer():

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.graph = None
        self.manager: pywrapcp.RoutingIndexManager = None
        self.distance_callback_counter = 0
        self.distance_callback_counter_fail = 0
        self.vel_meter_per_sec = 1  # / 3.6 # 6km/h
        #
        self.dimensions = {}
        self.capacities = {}
        self.penalty_dimension = "time"
        # add default dimension for each step
        # self.add_dimension("step", cost_callback=lambda G,u,v: 1)
        pass

    def add_dimension(self, name: str,
                      cost_callback: Callable[[nx.Graph, int, int], int],
                      capacity=None,
                      slack=0,
                      demand_callback=None):
        self.logger.debug("adding dimension %s", name)
        self.dimensions[name] = dict(cost_callback=cost_callback,
                                     capacity=capacity, slack=slack,
                                     demand_callback=demand_callback)

    def add_capacity(self, name: str,
                     capacity_callback: Callable[[nx.Graph, int], int],
                     capacity=None,
                     slack=0):
        self.capacities[name] = dict(capacity_callback=capacity_callback,
                                     capacity=capacity,
                                     slack=slack)

    @abstractmethod
    def solve(self, max_time=30, num_routes=1, constraints=[]):
        """Solve the optimization problem"""
        # breakpoint()
        # self.graph = mamogenx.G_problem_from_dag(self.graph)
        num_nodes = len(self.graph.nodes)
        # num_routes = 1
        #print("Solving dag", self.dag)
        # node_start = mamogenx.G_first(self.graph)
        # node_end = mamogenx.G_last(self.graph)
        node_start = [0] * num_routes
        node_end = [len(self.graph)-1]*num_routes

        # map from index to graph node id
        G_idx2node = list(self.graph.nodes)

        self.logger.info(
            f"Solving DAG from start to end {node_start}->{node_end}")

        self.manager = pywrapcp.RoutingIndexManager(
            num_nodes, num_routes, node_start, node_end)
        routing_parameters = pywrapcp.DefaultRoutingModelParameters()
        # routing_parameters.solver_parameters.trace_propagation = True
        # routing_parameters.solver_parameters.trace_search = True
        self.routing = pywrapcp.RoutingModel(self.manager, routing_parameters)

        has_arc_def = False
        for dim_name, dim_args in self.dimensions.items():
            self.logger.info(
                f"Adding dimension {dim_name} with args {dim_args}")
            dim_cost_callback = dim_args["cost_callback"]
            dim_demand_callback = dim_args["demand_callback"]
            slack = dim_args["slack"] if dim_args["slack"] is not None else 0
            capacity = (dim_args["capacity"]
                        if dim_args["capacity"] is not None
                        else 300000000)
            fix_start_cumul_to_zero = True

            # cost_matrix = mamogenx.G_cost_matrix(self.graph, lambda u,v: dim_cost_callback(self.graph, u,v))

            dim_matrix = np.zeros(
                (len(self.graph), len(self.graph)), dtype=int)

            def cost_callback(from_index, to_index):
                # TODO transform callback to matrix for better performance
                #
                try:
                    if dim_matrix[from_index, to_index] > 0:
                        # print("cache hit", from_index, to_index)
                        return dim_matrix[from_index, to_index]
                    #
                    # print("query", from_index, to_index)
                    from_node = G_idx2node[self.manager.IndexToNode(
                        from_index)]
                    to_node = G_idx2node[self.manager.IndexToNode(to_index)]
                    # print('dim_cost_callback', from_node, to_node)
                    val = dim_cost_callback(self.graph, from_node, to_node)
                    # print("cost_callback", from_index, to_index, cost_callback, val)

                    node_time_demand = dim_demand_callback(
                        self.graph, from_node)

                    # dim_matrix[from_index, to_index] = val + node_time_demand

                    return val
                except Exception as e:
                    self.logger.error((f"cost_callback error ({from_index}, "
                                       f"{to_index}), "
                                       f"{cost_callback}"))
                    self.logger.error(e)
                    return -1

            callback_index = self.routing.RegisterTransitCallback(
                cost_callback)

            if has_arc_def == False:
                self.logger.info(f"Setting ArcCost to dimension {dim_name}")
                # Define cost of each arc.
                self.routing.SetArcCostEvaluatorOfAllVehicles(callback_index)

                has_arc_def = True
            self.logger.info((f"Adding dimension {dim_name}: {slack}, "
                              f"{capacity}, "
                              f"{fix_start_cumul_to_zero}"))
            self.routing.AddDimension(
                callback_index,
                slack,
                capacity,
                fix_start_cumul_to_zero,
                dim_name)

            dimension = self.routing.GetDimensionOrDie(dim_name)
            dimension.SetGlobalSpanCostCoefficient(1)

            def demand_callback(from_index):
                from_node = G_idx2node[self.manager.IndexToNode(from_index)]
                return dim_demand_callback(self.graph, from_node)

            # demand_callback_index = self.routing.RegisterUnaryTransitCallback(demand_callback)

        if len(self.capacities) == 0:
            self.logger.info("No capacaties has been defined")
        for cap_name, cap_args in self.capacities.items():
            self.logger.info(
                f"Adding capacity dimension {cap_name} with args {cap_args}")

            cap_cost_callback = cap_args["capacity_callback"]
            slack = cap_args["slack"] if cap_args["slack"] is not None else 0
            capacity = (cap_args["capacity"]
                        if cap_args["capacity"] is not None
                        else 100000000)
            fix_start_cumul_to_zero = True

            # capacity_vector = mamogenx.G_cost_vector(self.graph, lambda u: cap_cost_callback(self.graph, u))
            def capacity_callback(index):
                # print("capacity callback", index)
                node = self.manager.IndexToNode(index)
                return int(cap_cost_callback(self.graph, node))

            capacity_callback_idx = self.routing.RegisterUnaryTransitCallback(
                capacity_callback)

            self.routing.AddDimensionWithVehicleCapacity(
                capacity_callback_idx,
                slack,
                [capacity]*num_routes,
                fix_start_cumul_to_zero,
                cap_name
            )

            dimension = self.routing.GetDimensionOrDie(cap_name)
            dimension.SetGlobalSpanCostCoefficient(1)

        if len(constraints) == 0:
            self.logger.info("No constraints has been defined")

        for constraint in constraints:
            u = constraint.u
            v = constraint.v
            self.logger.info(f"Adding constraint {constraint}")
            first_index = self.manager.NodeToIndex(u)
            second_index = self.manager.NodeToIndex(v)
            # same vehicle for every node in the sequence
            self.routing.solver().Add(self.routing.VehicleVar(first_index) == self.routing.VehicleVar(second_index))

            kw_args = constraint.kw_args

            dimension = self.routing.GetDimensionOrDie(constraint.dimension)

            if "min" in kw_args:
                # TODO dynamic select dimension
                min_value = kw_args["min"]
                dim_str = constraint.dimension
                constrain_arg = (dimension.CumulVar(first_index) +
                                 min_value) <= dimension.CumulVar(second_index)
                self.routing.solver().Add(constrain_arg)
                #print("Adding min constraint", u,v,dim_str, min_value)

            if "max" in kw_args:
                # TODO dynamic select dimension
                max_value = kw_args["max"]
                dim_str = constraint.dimension
                constrain_arg = (dimension.CumulVar(first_index) +
                                 max_value) > dimension.CumulVar(second_index)
                self.routing.solver().Add(constrain_arg)
                #print("Adding max constraint", u,v,dim_str, min_value)
                # raise "Not implemented"

        # Allow to drop nodes, penalty of 60min.
        penalty = 60*60
        # penalty = 1
        self.logger.info(
            f"Adding Penalty to dimension {self.penalty_dimension}")
        dimension = self.routing.GetDimensionOrDie(self.penalty_dimension)
        for node in range(1, num_nodes - 1):
            self.logger.debug(
                f"Add penality {node}, {self.manager.NodeToIndex(node)}")
            i = self.manager.NodeToIndex(node)
            self.routing.AddDisjunction([i], penalty)
            slack_var = dimension.SlackVar(i)
            self.routing.AddToAssignment(slack_var)
            pass

        self.logger.info("Defining search parameters")
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.log_search = True
        # search_parameters.first_solution_strategy = (routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
        # search_parameters.first_solution_strategy = (routing_enums_pb2.FirstSolutionStrategy.PATH_MOST_CONSTRAINED_ARC)
        # search_parameters.first_solution_strategy = (routing_enums_pb2.FirstSolutionStrategy.BEST_INSERTION)
        # search_parameters.first_solution_strategy = (routing_enums_pb2.FirstSolutionStrategy.ALL_UNPERFORMED)
        # search_parameters.first_solution_strategy = (routing_enums_pb2.FirstSolutionStrategy.LOCAL_CHEAPEST_ARC)
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.GLOBAL_CHEAPEST_ARC)
        # search_parameters.first_solution_strategy = (routing_enums_pb2.FirstSolutionStrategy.FIRST_UNBOUND_MIN_VALUE)
        # search_parameters.first_solution_strategy = (routing_enums_pb2.FirstSolutionStrategy.SWEEP)

        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
        # search_parameters.local_search_metaheuristic = (routing_enums_pb2.LocalSearchMetaheuristic.TABU_SEARCH)
        search_parameters.time_limit.FromSeconds(max_time)

        # search_parameters.first_solution_strategy = (
        # routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
        # Routing: forbids use of TSPOpt neighborhood, (this is the default behaviour)
        # search_parameters.local_search_operators.use_tsp_opt = pywrapcp.BOOL_FALSE
        # Disabling Large Neighborhood Search, (this is the default behaviour)
        # search_parameters.local_search_operators.use_path_lns = pywrapcp.BOOL_FALSE
        # search_parameters.local_search_operators.use_inactive_lns = pywrapcp.BOOL_FALSE

        # search_parameters.setLogSearch(True)
        # search_parameters.setPrintAddedConstraints(True)
        # search_parameters.setPrintModel(True)
        # search_parameters.setProfilePropagation(True)
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
        # print("start here 1")
        self.logger.info("Solving task ...")
        time.sleep(1)

        initial_solution = None
        if initial_solution:
            solution = self.routing.SolveFromAssignmentWithParameters(
                initial_solution, search_parameters)
        else:
            solution = self.routing.SolveWithParameters(search_parameters)

        self.logger.info("Done")

        if solution is None:
            self.logger.warn("Could not find any solution")
            return [], []

        self.logger.info("Found solution")
        self.logger.info(f"{solution}")
        self.logger.info(f"num_route {num_routes}")

        result, meta = self.extract_solution(
            num_routes, self.manager, self.routing, solution)

        self.logger.debug(f"Results {result}")

        # [print(n) for n in [route for route in result]]

        return [[G_idx2node[n] for n in path] for path in result], meta
        # return [G_idx2node[n] for n in [route for route in result]], meta
        # return result

    def extract_values(self, solution, dim, index, prev_index, vehicle_id):
        results = {}

        cum = dim.CumulVar(index)
        # results[self.penalty_dimension] = solution.Min(cum), solution.Max(cum)
        results["cumul"] = solution.Min(cum)  # , solution.Max(cum)
        results["demand"] = 0
        results["slack"] = 0
        results["transit"] = 0  # dim.GetTransitValue(index)
        if(prev_index >= 0):
            cum_prev = dim.CumulVar(prev_index)
            # , solution.Max(cum) - solution.Max(cum_prev),
            d_cost = solution.Min(cum) - solution.Min(cum_prev)
            # print("extract_values", dim, index, prev_index)
            results["demand"] = d_cost
            results["transit"] = dim.GetTransitValue(
                prev_index, index, vehicle_id)  # - results["demand"]
            results["slack"] = d_cost - results["transit"]

        return results

    def print_solution(self, manager, routing, solution):
        """Print solution on console."""
        # print('Objective: {} miles'.format(solution.ObjectiveValue()))
        index = routing.Start(0)
        plan_output = 'Route for vehicle 0:\n'
        route_distance = 0
        while not routing.IsEnd(index):
            plan_output += ' {} ->'.format(manager.IndexToNode(index))
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            # print(f"prev index, index: {type(previous_index)}, {type(index)}")
            route_distance += routing.GetArcCostForVehicle(
                previous_index, index, 0)
        # plan_output += ' {}\n'.format(manager.IndexToNode(index))
        # print(plan_output)
        # plan_output += 'Route distance: {}miles\n'.format(route_distance)

    def extract_solution(self, num_routes, manager, routing, solution):
        """Print solution on console."""
        # print(f'Objective: {solution.ObjectiveValue()}')

        time_dim = routing.GetDimensionOrDie(self.penalty_dimension)
        water_dim = routing.GetDimensionOrDie("water")
        total_time = 0

        results = []
        results_meta = []

        # max_route_distance = 0
        for vehicle_id in range(num_routes):
            print("Vehicle ID", vehicle_id)
            route = []
            route_meta = {}  # []
            index = routing.Start(vehicle_id)
            prev_index = -1
            # plan_output = 'Route for vehicle {}:\n'.format(vehicle_id)
            # print("Transits", time_dim.CumulVar(index))
            # route_distance = 0
            while not routing.IsEnd(index):
                node = manager.IndexToNode(index)
                route.append(node)
                # plan_output += ' {} -> '.format(manager.IndexToNode(index))
                time_var = time_dim.CumulVar(index)
                #slack_var = time_dim.SlackVar(index)
                # transit_var = time_dim.TransitVar(index)

                # print(f"time_var ", time_var)
                # print(f"index ", index)
                # print(f"prev_index ", prev_index)
                # print(f"vehicle_id ", vehicle_id)
                # print(f"{solution}, {time_dim}, {index}, {prev_index}, {vehicle_id}")
                values = {}
                values["time"] = self.extract_values(
                    solution, time_dim, index, prev_index, vehicle_id)
                values["water"] = self.extract_values(
                    solution, water_dim, index, prev_index, vehicle_id)

                route_meta[node] = values
                # route_meta[node]["time"] = solution.Min(time_var), solution.Max(time_var)
                #  print("Transit var", transit_var, solution.Value(transit_var))
                # route_meta[node]["slack"] = slack_var.Min(), slack_var.Max()
                # route_meta[node]["transit"] = transit_var.Min(), transit_var.Max()
                # route_meta[node]["transit"] = solution.Min(transit_var), solution.Max(transit_var)

                # (solution.Min(time_var), solution.Max(time_var), time_dim.SlackVar(index))
                # plan_output += '{0} Time({1},{2}) -> '.format(
                # manager.IndexToNode(index), solution.Min(time_var),
                # solution.Max(time_var))

                # print(f"plan output {plan_output}")
                prev_index = index
                index = solution.Value(routing.NextVar(index))

                # print(f"next index {index}")
                # route_distance += routing.GetArcCostForVehicle(
                # previous_index, index, vehicle_id)

            node = manager.IndexToNode(index)
            time_var = time_dim.CumulVar(index)
            # slack_var = time_dim.SlackVar(index)
            # transit_var = time_dim.TransitVar(index)

            # plan_output += '{0} Step({1},{2})\n'.format(node,
            #                                         solution.Min(time_var),
            #                                         solution.Max(time_var))
            # plan_output += 'Time of the route: {}sec\n'.format(
            #     solution.Min(time_var))
            # print(plan_output)
            total_time += solution.Min(time_var)

            values = {}
            values["time"] = self.extract_values(
                solution, time_dim, index, prev_index, vehicle_id)
            values["water"] = self.extract_values(
                solution, water_dim, index, prev_index, vehicle_id)
            route_meta[node] = values

            route.append(manager.IndexToNode(index))

            results.append(route)
            results_meta.append(route_meta)
            # plan_output += '{}\n'.format(manager.IndexToNode(index))
            # plan_output += 'Distance of the route: {}m\n'.format(route_distance)
            # print(plan_output)
            # max_route_distance = max(route_distance, max_route_distance)
        # print('Maximum of the route distances: {}m'.format(max_route_distance))
        return results, results_meta
