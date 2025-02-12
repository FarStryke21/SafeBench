'''
Author:
Email: 
Date: 2023-01-31 22:23:17
LastEditTime: 2023-03-01 16:53:00
Description: 
    Copyright (c) 2022-2023 Safebench Team

    This file is modified from <https://github.com/carla-simulator/scenario_runner/tree/master/srunner/scenarios>
    Copyright (c) 2018-2020 Intel Corporation

    This work is licensed under the terms of the MIT license.
    For a copy, see <https://opensource.org/licenses/MIT>
'''

import math
import json
import carla

from safebench.scenario.scenario_manager.carla_data_provider import CarlaDataProvider
from safebench.scenario.scenario_definition.basic_scenario import BasicScenario
from safebench.scenario.tools.scenario_helper import generate_target_waypoint, generate_target_waypoint_in_route

from safebench.scenario.tools.scenario_operation import ScenarioOperation
from safebench.scenario.tools.scenario_utils import calculate_distance_transforms
from safebench.scenario.tools.scenario_utils import calculate_distance_locations


def get_opponent_transform(added_dist, waypoint, trigger_location):
    """
    Calculate the transform of the adversary
    """
    lane_width = waypoint.lane_width

    offset = {"orientation": 270, "position": 90, "k": 1.0}
    _wp = waypoint.next(added_dist)
    if _wp:
        _wp = _wp[-1]
    else:
        raise RuntimeError("Cannot get next waypoint !")

    location = _wp.transform.location
    orientation_yaw = _wp.transform.rotation.yaw + offset["orientation"]
    position_yaw = _wp.transform.rotation.yaw + offset["position"]

    offset_location = carla.Location(
        offset['k'] * lane_width * math.cos(math.radians(position_yaw)),
        offset['k'] * lane_width * math.sin(math.radians(position_yaw)))
    location += offset_location
    location.z = trigger_location.z
    transform = carla.Transform(location, carla.Rotation(yaw=orientation_yaw))

    return transform


def get_right_driving_lane(waypoint):
    """
    Gets the driving / parking lane that is most to the right of the waypoint
    as well as the number of lane changes done
    """
    lane_changes = 0

    while True:
        wp_next = waypoint.get_right_lane()
        lane_changes += 1

        if wp_next is None or wp_next.lane_type == carla.LaneType.Sidewalk:
            break
        elif wp_next.lane_type == carla.LaneType.Shoulder:
            # Filter Parkings considered as Shoulders
            if is_lane_a_parking(wp_next):
                lane_changes += 1
                waypoint = wp_next
            break
        else:
            waypoint = wp_next

    return waypoint, lane_changes


def is_lane_a_parking(waypoint):
    """
    This function filters false negative Shoulder which are in reality Parking lanes.
    These are differentiated from the others because, similar to the driving lanes,
    they have, on the right, a small Shoulder followed by a Sidewalk.
    """

    # Parking are wide lanes
    if waypoint.lane_width > 2:
        wp_next = waypoint.get_right_lane()

        # That are next to a mini-Shoulder
        if wp_next is not None and wp_next.lane_type == carla.LaneType.Shoulder:
            wp_next_next = wp_next.get_right_lane()

            # Followed by a Sidewalk
            if wp_next_next is not None and wp_next_next.lane_type == carla.LaneType.Sidewalk:
                return True

    return False


class VehicleTurningRoute(BasicScenario):

    """
    This class holds everything required for a simple object crash
    with prior vehicle action involving a vehicle and a cyclist.
    The ego vehicle is passing through a road and encounters
    a cyclist after taking a turn. This is the version used when the ego vehicle
    is following a given route. (Traffic Scenario 4)
    This is a single ego vehicle scenario
    """

    def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, criteria_enable=True,
                 timeout=60):
        """
        Setup all relevant parameters and create scenario
        """
        self._wmap = CarlaDataProvider.get_map()
        self.timeout = timeout
        self._other_actor_target_velocity = 10
        self._reference_waypoint = self._wmap.get_waypoint(config.trigger_points[0].location)
        self._trigger_location = config.trigger_points[0].location
        self._ego_route = CarlaDataProvider.get_ego_vehicle_route()

        self._num_lane_changes = 0

        self._ego_route = CarlaDataProvider.get_ego_vehicle_route()

        super(VehicleTurningRoute, self).__init__("VehicleTurningRouteDynamic",
                                                  ego_vehicles,
                                                  config,
                                                  world,
                                                  debug_mode,
                                                  criteria_enable=criteria_enable,
                                                  terminate_on_failure=True)

        self.scenario_operation = ScenarioOperation(self.ego_vehicles, self.other_actors)

        self.actor_type_list.append('vehicle.diamondback.century')

        self.reference_actor = None
        self.trigger_distance_threshold = 17
        self.ego_max_driven_distance = 180

        self.running_distance = 20
        self.step = 0
        with open(config.parameters, 'r') as f:
            parameters = json.load(f)
        self.control_seq = [control * 2 - 1 for control in parameters]
        # self._other_actor_max_velocity = self._other_actor_target_velocity * 2
        self.total_steps = len(self.control_seq)
        self.actor_transform_list = []
        self.perturbed_actor_transform_list = []

    def initialize_actors(self):
        """
        Custom initialization
        """
        waypoint = generate_target_waypoint_in_route(self._reference_waypoint, self._ego_route)

        # Move a certain distance to the front
        start_distance = 8
        waypoint = waypoint.next(start_distance)[0]

        # Get the last driving lane to the right
        waypoint, self._num_lane_changes = get_right_driving_lane(waypoint)
        # And for synchrony purposes, move to the front a bit
        added_dist = self._num_lane_changes

        _other_actor_transform = get_opponent_transform(added_dist, waypoint, self._trigger_location)

        self.other_actor_transform.append(_other_actor_transform)

        # forward_vector = self.other_actor_transform[0].rotation.get_forward_vector() * num_lanes * self._reference_waypoint.lane_width
        forward_vector = self.other_actor_transform[0].rotation.get_forward_vector() * self.running_distance
        right_vector = self.other_actor_transform[0].rotation.get_right_vector()
        for i in range(self.total_steps):
            self.actor_transform_list.append(carla.Transform(
                carla.Location(self.other_actor_transform[0].location + forward_vector * i / self.total_steps),
                self.other_actor_transform[0].rotation))
        for i in range(self.total_steps):
            self.perturbed_actor_transform_list.append(carla.Transform(
                carla.Location(self.actor_transform_list[i].location + right_vector * self.control_seq[i]),
                self.other_actor_transform[0].rotation))

        self.scenario_operation.initialize_vehicle_actors(self.other_actor_transform, self.other_actors, self.actor_type_list)

        """Also need to specify reference actor"""
        self.reference_actor = self.other_actors[0]

    def update_behavior(self):
        # print(self.step)
        # target_waypoint = CarlaDataProvider.get_map().get_waypoint(self.perturbed_actor_transform_list[self.step])
        target_transform = self.perturbed_actor_transform_list[self.step if self.step < self.total_steps else -1]
        self.step += 1  # <= 50 steps
        for i in range(len(self.other_actors)):
            # print('input location', self.perturbed_actor_transform_list[self.step])
            # print('input waypoint', target_waypoint)
            self.scenario_operation.drive_to_target_followlane(i, target_transform, self._other_actor_target_velocity)

    def check_stop_condition(self):
        """
        This condition is just for small scenarios
        """

        return False


    def _create_behavior(self):
        pass