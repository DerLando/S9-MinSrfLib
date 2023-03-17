from typing import Any, Dict, List
import numpy as np
from geometry import Point
import json
from conversion import NumpyArrayEncoder
from enum import Enum

import geometry

COORDINATE_TOLERANCE = 0.001

class WorldDimension(Enum):
    X = 0
    Y = 1
    Z = 2

class BoundaryConditionBase:
    """
    Abstract base class for all boundary conditions
    """
    def to_json(self):
        """
        Convert this boundary condition to a JSON representation.
        Mostly used to get around the limitations of hops...    
        """
        return json.dumps(self, default=lambda o: o.__dict__)

    @staticmethod
    def from_json_hook(json: dict):
        pass
        
class VertexBoundaryCondition(BoundaryConditionBase):
    position: Point
    index: int

    def __init__(self, position: Point, index: int):
        self.position = position
        self.index = index

    def enforce(self, pt: Point) -> Point:
        return pt

    def is_fully_constrained(self) -> bool:
        return False

class VertexAnchorCondition(VertexBoundaryCondition):
    """
    A vertex that is anchored to a given position
    """
    x_locked: bool
    y_locked: bool
    z_locked: bool

    constrained_indices: List[int]

    def __init__(self, position: Point, index: int, x_locked=True, y_locked=True, z_locked=True):
        self.position = position
        self.index = index
        self.x_locked = x_locked
        self.y_locked = y_locked
        self.z_locked = z_locked

        self.constrained_indices = self._calc_constrained_indices()

    def _calc_constrained_indices(self) -> List[int]:
        constrained_indices = []
        if self.x_locked: constrained_indices.append(0)
        if self.y_locked: constrained_indices.append(1)
        if self.z_locked: constrained_indices.append(2)

        return constrained_indices

    def is_fully_constrained(self) -> bool:
        """
        Check to see if the anchor point is fully constrained,
        meaning it can not move at all.
        """
        return self.x_locked and self.y_locked and self.z_locked

    def constrained_count(self) -> int:
        return len(self.constrained_indices)

    def _enforce_x(self, pt: Point) -> Point:
        pt[0] = self.position[0]

    def enforce(self, pt: Point) -> Point:
        """
        Enforces the inner boundary conditions on the incoming point
        """
        for index in self.constrained_indices:
            pt[index] = self.position[index]

        return pt

    def to_json(self):
        self.position = [self.position[0], self.position[1], self.position[2]]
        return super().to_json()
    
    @staticmethod    
    def from_json(serialized: str):
        return json.loads(serialized, object_hook=VertexAnchorCondition.from_json_hook)
        
    @staticmethod
    def from_json_hook(json: dict):
        position = np.array(json["position"])
        return VertexAnchorCondition(position, json["index"], json["x_locked"], json["y_locked"], json["z_locked"])


VertexBoundaryConditionsCollection = Dict[int, List[VertexBoundaryCondition]]

def build_boundary_collection(boundaries: List[VertexBoundaryCondition]) -> VertexBoundaryConditionsCollection:
    result = dict()
    for boundary in boundaries:
        if boundary.index in result:
            result[boundary.index].append(boundary)
        else:
            result[boundary.index] = [boundary]

    return result

class OnCircleBoundaryCondition(VertexBoundaryCondition):
    """
    A boundary condition to keep a given vertex on a circle.
    This is achieved by remapping the vertex and it's one-ring neighbors
    to the circle plane before calculating the new vertex position
    and enforcing two invariants on the new vertex position:
        1. Z coordinate of the vertex in circle space must be 0
        2. Length of the vector center->vertex must be equal to the circle radius
    """

    center: Point
    radius: float
    normal: Point
    _helper: Point
    _lcs_to_gcs = None
    _gcs_to_lcs = None

    def __init__(self, position: Point, index: int, center: Point, radius: float, normal: Point) -> None:
        super().__init__(position, index)
        self.center = center
        self.radius = radius
        self.normal = normal
        helper = self._create_helper(center, self.radius, normal, position)
        self._helper = helper
        self._lcs_to_gcs = self._create_lcs_matrix(center, radius, normal, position, helper)
        self._gcs_to_lcs = self._create_gcs_matrix(center, radius, normal, position, helper)

    @staticmethod
    def _create_helper(center: Point, radius: float, normal: Point, position: Point) -> Point:
        """
        Create a helper point on the circle in global coordinates.
        It's local coordinates will be [0, r, 0]
        """
        direction = np.cross(normal, position - center)
        direction /= np.linalg.norm(direction)
        direction *= radius

        return center + direction

    @staticmethod
    def _create_lcs_matrix(center: Point, radius: float, normal: Point, position: Point, helper: Point):
        """
        Create the transformation matrix from global to local coordinates
        """
        # return np.eye(4)
        return np.column_stack((
            np.append(position, 0),
            np.append(helper, 0),
            np.append(normal, 0),
            np.append(center, 1)
        ))
        
    @staticmethod
    def _create_gcs_matrix(center: Point, radius: float, normal: Point, position: Point, helper: Point):
        """
        Create the transformation matrix from local to global coordinates
        """

        # create the two vectors of the coordinate system
        p = position - center
        x = helper - center

        # rename normal for brevitiy
        n = normal

        # create transformation matrix
        return np.column_stack((
            np.append(p, 0),
            np.append(x, 0),
            np.append(n, 0),
            np.append(-center, 1)
            ))
    
    def enforce(self, pt: Point) -> Point:
        # print(f"pt in local coords was: {pt}")

        # points on the circle have z coordinate = 0
        pt[2] = 0

        # points on the circle have a norm of r
        length = np.linalg.norm(pt)
        if abs(length - self.radius) < 0.01 and length > 0.01:
            pt *= (self.radius / length)

        # print(f"pt in local coords is now: {pt}")

        return pt

    def remap_to_circle_coordinates(self, pt: Point) -> Point:
        """
        Takes a point in global coordinates and remaps it to local coordinates
        """

        #TODO: Remove this hack
        pt[2] = pt[2] - self.center[2]
        return pt

        homogenous_pt = self._gcs_to_lcs @ np.append(pt, 1)
        return homogenous_pt[:3]

    def remap_to_global_coordinates(self, pt: Point) -> Point:
        """
        Takes a point in circle-local coordinates and remaps it to global coordinates
        """

        #TODO: Remove this hack
        pt[2] = self.center[2] + pt[2]
        return pt
    
        homogenous_pt = self._lcs_to_gcs @ np.append(pt, 1)
        return homogenous_pt[:3]

    def to_json(self):
        self.position = [self.position[0], self.position[1], self.position[2]]
        self.center = [self.center[0], self.center[1], self.center[2]]
        self.normal = [self.normal[0], self.normal[1], self.normal[2]]
        self._helper = None
        self._lcs_to_gcs = None
        self._gcs_to_lcs = None
        return super().to_json()
    
    @staticmethod    
    def from_json(serialized: str):
        return json.loads(serialized, object_hook=OnCircleBoundaryCondition.from_json_hook)
        
    @staticmethod
    def from_json_hook(json: dict):
        position = np.array(json["position"])
        center = np.array(json["center"])
        normal = np.array(json["normal"])
        return OnCircleBoundaryCondition(position, json["index"], center, json["radius"], normal)

                
if __name__ == "__main__":
    condition = VertexAnchorCondition(np.array([0.0, 0.0, 1.0]), 1)
    serialized = condition.to_json()
    
    print(serialized)
    
    deserialized = VertexAnchorCondition.from_json(serialized)
    
    print(deserialized)
    print(deserialized.position)

    center = np.array([0.0, 0.0, 0.0])
    position = np.array([1.0, 0.0, 0.0])
    normal = np.array([0.0, 0.0, 1.0])

    condition = OnCircleBoundaryCondition(position, 0, center, 1.0, normal)

    serialized = condition.to_json()

    print(serialized)

    deserialized = OnCircleBoundaryCondition.from_json(serialized)

    print(deserialized)
    print(deserialized.center)
    print(deserialized.position)
    print(deserialized.normal)
    print(deserialized._lcs_to_gcs)


    center = np.array([0.0, 0.0, 5.0])
    position = np.array([1.0, 0.0, 5.0])
    normal = np.array([0.0, 0.0, 1.0])
    condition = OnCircleBoundaryCondition(position, 0, center, 1.0, normal)

    print("condition gcs->lcs:")
    print(condition._gcs_to_lcs)

    print("condition lcs->gcs:")
    print(condition._lcs_to_gcs)

    test_pt = np.array([0.0, 0.0, 6.0])
    local = condition.remap_to_circle_coordinates(test_pt)
    print(local)
    global_pt = condition.remap_to_global_coordinates(local)
    print(global_pt)

##############################################################

    center = np.array([0.0, 0.0, 5.0])
    position = np.array([0.0, 0.0, 6.0])
    normal = np.array([1.0, 0.0, 0.0])
    condition = OnCircleBoundaryCondition(position, 0, center, 1.0, normal)

    print("condition gcs->lcs:")
    print(condition._gcs_to_lcs)

    print("condition lcs->gcs:")
    print(condition._lcs_to_gcs)

    test_pt = np.array([0.0, 0.0, 5.0])
    local = condition.remap_to_circle_coordinates(test_pt)
    print(local)
    global_pt = condition.remap_to_global_coordinates(local)
    print(global_pt)
    