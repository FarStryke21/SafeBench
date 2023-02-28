'''
Author: 
Email: 
Date: 2023-02-16 11:20:54
LastEditTime: 2023-02-28 00:55:54
Description: 
'''

import carla

from safebench.scenario.scenario_manager.carla_data_provider import CarlaDataProvider
from safebench.scenario.tools.scenario_helper import get_waypoint_in_distance
from safebench.scenario.scenario_definition.basic_scenario import BasicScenario
from safebench.scenario.tools.scenario_operation import ScenarioOperation


class ManeuverOppositeDirection(BasicScenario):
    """
        Vehicle is passing another vehicle in a rural area, in daylight, under clear weather conditions, 
        at a non-junction and encroaches into another vehicle traveling in the opposite direction. (Traffic Scenario 06)
    """

    def __init__(self, world, ego_vehicle, config, timeout=60):
        super(ManeuverOppositeDirection, self).__init__("ManeuverOppositeDirection-LC", config, world)
        self.ego_vehicle = ego_vehicle
        self.timeout = timeout

        self._map = CarlaDataProvider.get_map()
        self._reference_waypoint = self._map.get_waypoint(config.trigger_points[0].location)
        # self._source_transform = None
        # self._sink_location = None
        self._first_actor_transform = None
        self._second_actor_transform = None
        # self._third_actor_transform = None

        self.scenario_operation = ScenarioOperation()
        self.trigger_distance_threshold = 45
        self.ego_max_driven_distance = 200

    def convert_actions(self, actions):
        x_min = 40
        x_max = 60
        x_scale = (x_max-x_min)/2

        y_min = 20
        y_max = 40
        y_scale = (y_max-y_min)/2

        yaw_min = 6
        yaw_max = 10
        yaw_scale = (yaw_max-yaw_min)/2

        x_mean = (x_max + x_min)/2
        y_mean = (y_max + y_min)/2
        yaw_mean = (yaw_max + yaw_min)/2

        x = actions[0] * x_scale + x_mean
        y = actions[1] * y_scale + y_mean
        yaw = actions[2] * yaw_scale + yaw_mean
        return [x, y, yaw]

    def initialize_actors(self):
        first_actor_waypoint, _ = get_waypoint_in_distance(self._reference_waypoint, self._first_vehicle_location)
        second_actor_waypoint, _ = get_waypoint_in_distance(self._reference_waypoint, self._second_vehicle_location)
        second_actor_waypoint = second_actor_waypoint.get_left_lane()
        first_actor_transform = carla.Transform(first_actor_waypoint.transform.location, first_actor_waypoint.transform.rotation)
        second_actor_transform = second_actor_waypoint.transform

        self.actor_type_list = ['vehicle.nissan.micra', 'vehicle.nissan.micra']
        self.actor_transform_list = [first_actor_transform, second_actor_transform]
        self.other_actors = self.scenario_operation.initialize_vehicle_actors(self.actor_transform_list, self.actor_type_list)
        self.reference_actor = self.other_actors[0] # used for triggering this scenario
        
    def create_behavior(self, scenario_init_action):
        actions = self.convert_actions(scenario_init_action)
        x1, x2, v2 = actions  
        self._first_vehicle_location = x1
        self._second_vehicle_location = self._first_vehicle_location + x2
        self._opposite_speed = v2  # m/s

    def update_behavior(self, scenario_action):
        assert scenario_action is None, f'{self.name} should receive [None] action. A wrong scenario policy is used.'

        # first actor run in low speed, second actor run in normal speed from oncoming route
        self.scenario_operation.go_straight(self._opposite_speed, 1)

    def check_stop_condition(self):
        pass
