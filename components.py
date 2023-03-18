import sys
import os
import time
import rhinoinside
import conversion
from geometry import mesh_area, point
import algorithms
from boundary_conditions import OnCircleBoundaryCondition, VertexAnchorCondition, build_boundary_collection

# load ghhops-server-py source from this directory
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import ghhops_server as hs


rhinoinside.load()
# System and Rhino can only be loaded after rhinoinside is initialized
import System  # noqa
import Rhino  # noqa

hops = hs.Hops(app=rhinoinside)

@hops.component(
    "/minimize",
    name="Minimize",
    nickname="MNMZ",
    description="Minimize mesh area",
    category="Mesh",
    subcategory="CPython",
    inputs=[
        hs.HopsMesh("Mesh", "M", "The mesh to minimize"),
        hs.HopsNumber("Tolerance", "T", "The tolerance for minimization"),
        hs.HopsInteger("Max Iterations", "I", "Optional upper limit on iteration count", optional=True, default=-1),
        hs.HopsString("Boundary conditions", "B", "List of vertex boundary conditions to enforce", access=hs.HopsParamAccess.LIST, optional=True, default=None),
    ],
    outputs=[
        hs.HopsMesh("Mesh", "M", "The minimized mesh"),
        hs.HopsNumber("Areas", "A", "The areas at every iteration step", hs.HopsParamAccess.LIST)],
)
def minimize(mesh, tol, iterations, boundary_conditions):
    # TODO: Make anchor indices an input

    start = time.time()

    if iterations == -1:
        iterations = None
    
    vertices, faces, connectivity, boundary_indices = conversion.convert_from_mesh(mesh)

    # if there are no boundary conditions defined, explicitly convert the boundary indices
    # to anchor points
    if boundary_conditions is None:
        # TODO: Use boundary indices here...
        boundary_conditions = dict([(i, VertexAnchorCondition(vertices[i], i)) for i in boundary_indices])
    else:
        conditions = []
        for condition in boundary_conditions:
            if "center" in condition:
                condition = OnCircleBoundaryCondition.from_json(condition)
            else:
                condition = VertexAnchorCondition.from_json(condition)

            conditions.append(condition)

        # boundary_conditions is a flat list, we need to convert it to a dict
        boundary_conditions = build_boundary_collection(conditions)        
    
    # print(boundary_conditions)
    # print(boundary_indices)
    # print("Mesh area is: ")
    # print(mesh_area(vertices, faces))

    optimized, areas = algorithms.minimize_mesh(vertices, faces, connectivity, tol, iterations, boundary_conditions)

    converted = conversion.convert_to_mesh(optimized, faces)

    end = time.time()

    print(f"Minimization took {end - start}ms")

    # print(areas)

    return (converted, areas)

@hops.component(
    "/vertex_anchor",
    name="Vertex Anchor",
    nickname="VANCH",
    description="Define vertex anchors",
    category="Mesh",
    subcategory="CPython",
    inputs=[
        hs.HopsPoint("Point", "P", "The anchor point"),
        hs.HopsInteger("Index", "I", "The vertex index of the anchor point"),
        hs.HopsBoolean("Fix X", "X", "Fix the anchor's x position", optional=True, default=True),
        hs.HopsBoolean("Fix Y", "Y", "Fix the anchor's y position", optional=True, default=True),
        hs.HopsBoolean("Fix Z", "Z", "Fix the anchor's z position", optional=True, default=True),
    ],
    outputs=[hs.HopsString("Data", "D", "Data as json")],
)
def create_vertex_anchor(pt, index, fix_x, fix_y, fix_z):
    condition = VertexAnchorCondition(conversion.convert_point3d(pt), index, fix_x, fix_y, fix_z)

    return condition.to_json()

@hops.component(
    "/on_circle_constraint",
    name="On Circle constraint",
    nickname="OnCrc",
    description="Define a on circle boundary condition",
    category="Mesh",
    subcategory="CPython",
    inputs=[
        hs.HopsPoint("Point", "P", "The anchor point"),
        hs.HopsInteger("Index", "I", "The vertex index of the anchor point"),
        hs.HopsCircle("Circle", "C", "The circle to constrain the point on to"),
    ],
    outputs=[hs.HopsString("Data", "D", "Data as json")],
)
def create_on_circle_condition(pt, index, circle):
    point = conversion.convert_point3d(pt)
    center = conversion.convert_point3d(circle.Plane.Origin)
    normal = conversion.convert_point3d(circle.Plane.Normal)
    condition = OnCircleBoundaryCondition(point, index, center, circle.Radius, normal)

    return condition.to_json()

if __name__ == "__main__":
    hops.start(debug=False)