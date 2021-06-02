from abc import abstractmethod
import networkx as nx
from mamoge.taskplanner import nx as mamogenx

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import numpy as np

class ORTaskOptimizer():


    def __init__(self) -> None:
        self.graph = None
        self.manager: pywrapcp.RoutingIndexManager = None
        self.distance_callback_counter = 0
        self.distance_callback_counter_fail = 0
        self.vel_meter_per_sec = 1 # / 3.6 # 6km/h
        pass

    def set_graph(self, G:nx.Graph)-> None:
        """set the problem graph to be optimized"""
        self.graph = G


    def time_matrix_callback(self, D, from_index, to_index):
        # print("Travel cost", from_index, to_index)
        try:
            from_node = self.manager.IndexToNode(from_index)
            to_node = self.manager.IndexToNode(to_index)

            t = (from_node, to_node)

            dist = D[from_node, to_node] / 100

            if (dist < 0.001):
                return 1000000
            #if(t in [(2,1), (2,4)]):
            #    print("Time_matrix_callback", from_index, to_index, dist)

            return dist / self.vel_meter_per_sec

        except Exception as e:
            print("time matrix callback error", from_index, to_index, e)

            return 10000000

    def time_cost_per_node(self, D, node_index):
        # print("cost per node", node_index)
        #TODO get from graph
        return 3 * 60 # 3min


    def time_cost_callback(self, D, from_index, to_index):

        try:
                # if(from_index == 0):
                # print("Time_cost_callback", from_index, to_index)
            travel_time =  self.time_matrix_callback(D, from_index, to_index)
            service_time = self.time_cost_per_node(D, to_index)

            if(np.isinf(travel_time)):
                return 1000000000000

            cost =  int(travel_time + service_time)

            t = (from_index, to_index)

        #mmininif(t in [(0,1), (1,2), (2,3), (3,4), (4,5), (5,6), (6,7)]):
            #if(t in [(0,1), (1,2), (2,3), (2,4), (4,5), (3,5), (3,4), (4,3)]):
            #print("Time_cost_callback", from_index, to_index, cost, travel_time, service_time)
            return cost
        except Exception as e:
            print("error",e)
            return 10000000000

    @abstractmethod
    def solve(self, time=30, constrains=[]):
        """Solve the optimization problem"""
        num_nodes = len(self.graph.nodes)
        num_routes = 1
        #print("Solving dag", self.dag)
        node_start = mamogenx.G_first(self.graph)
        node_end = mamogenx.G_last(self.graph)
        print("Start to end", node_start, node_end)

        self.manager = pywrapcp.RoutingIndexManager(num_nodes, num_routes, [node_start],[node_end])
        routing_parameters = pywrapcp.DefaultRoutingModelParameters()
        #routing_parameters.solver_parameters.trace_propagation = True
        #routing_parameters.solver_parameters.trace_search = True
        self.routing = pywrapcp.RoutingModel(self.manager, routing_parameters)


        print("Calculating distance matrix")
        distance_matrix = mamogenx.G_distance_matrix(self.graph)

        print("distance matrix")
        print(distance_matrix)

        #cb = lambda x,y: self.distance_callback(x,y)
        time_cost_callback_or = lambda x,y: self.time_cost_callback(distance_matrix, x,y)
        #cb = lambda x,y: 1

        time_callback_index = self.routing.RegisterTransitCallback(time_cost_callback_or)

        # Define cost of each arc.
        self.routing.SetArcCostEvaluatorOfAllVehicles(time_callback_index)


        time_dimension_name = 'Time'
        self.routing.AddDimension(
            time_callback_index,
            30 * 60 * 1,  # slack 25min
            6 * 60 * 6000,  # 6h, vehicle maximum travel time
            True,  # start cumul to zero
            time_dimension_name)
        time_dimension = self.routing.GetDimensionOrDie(time_dimension_name)
        time_dimension.SetGlobalSpanCostCoefficient(1)


        print("Adding constraints")
        for u,v in constrains:
            print("constraints", u,v)
            first_index = self.manager.NodeToIndex(u)
            second_index = self.manager.NodeToIndex(v)
            # same vehicle for every node in the sequence
            self.routing.solver().Add(self.routing.VehicleVar(first_index) == self.routing.VehicleVar(second_index))

            self.routing.solver().Add(
                time_dimension.CumulVar(first_index) + 5 * 60 <=  time_dimension.CumulVar(second_index))



        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.log_search = True
        # search_parameters.first_solution_strategy = (routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
        search_parameters.first_solution_strategy = (routing_enums_pb2.FirstSolutionStrategy.PATH_MOST_CONSTRAINED_ARC)
        search_parameters.local_search_metaheuristic = (routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
        search_parameters.time_limit.FromSeconds(time)

        print("Solving tasks")
        solution = self.routing.SolveWithParameters(search_parameters)

        print("Done", solution)

        if solution is None:
            return []

        return self.extract_solution(num_routes, self.manager, self.routing, solution)


    def extract_solution(self, num_routes, manager, routing, solution):
        """Prints solution on console."""
        print(f'Objective: {solution.ObjectiveValue()}')

        time_dim = routing.GetDimensionOrDie("Time")
        total_time = 0

        results = []
        # max_route_distance = 0
        for vehicle_id in range(num_routes):
            print("Vehicle ID", vehicle_id)
            route = []
            index = routing.Start(vehicle_id)
            plan_output = 'Route for vehicle {}:\n'.format(vehicle_id)
            # route_distance = 0
            while not routing.IsEnd(index):
                route.append(manager.IndexToNode(index))
                # plan_output += ' {} -> '.format(manager.IndexToNode(index))
                time_var  = time_dim.CumulVar(index)
                plan_output += '{0} Time({1},{2}) -> '.format(
                    manager.IndexToNode(index), solution.Min(time_var),
                    solution.Max(time_var))

                # previous_index = index
                index = solution.Value(routing.NextVar(index))

                # route_distance += routing.GetArcCostForVehicle(
                    # previous_index, index, vehicle_id)
                    #
            time_var = time_dim.CumulVar(index)
            plan_output += '{0} Time({1},{2})\n'.format(manager.IndexToNode(index),
                                                    solution.Min(time_var),
                                                    solution.Max(time_var))
            plan_output += 'Time of the route: {}sec\n'.format(
                solution.Min(time_var))
            print(plan_output)
            total_time += solution.Min(time_var)

            route.append(manager.IndexToNode(index))
            results.append(route)

            # plan_output += '{}\n'.format(manager.IndexToNode(index))
            # plan_output += 'Distance of the route: {}m\n'.format(route_distance)
            # print(plan_output)
            # max_route_distance = max(route_distance, max_route_distance)
        #print('Maximum of the route distances: {}m'.format(max_route_distance))
        return results
