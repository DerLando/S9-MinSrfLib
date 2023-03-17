from json import JSONEncoder
import typing
import numpy as np
import rhinoinside
rhinoinside.load()
import Rhino.Geometry as rg
from geometry import Triangle, triangle, Point, point, mesh_face, mesh_face_collection, mesh_vertex_collection, MeshFaceCollection, MeshVertexCollection, MeshVertexConnectivity

def convert_point3d(pt: rg.Point3d) -> Point:
    return point(pt.X, pt.Y, pt.Z)

# def convert_to_point3d(pt: Point):
#     return rg.Point3d(pt[0], pt[1], pt[2])

def convert_polyline_to_triangle(pline: rg.Polyline) -> Triangle:
    return triangle(
        convert_point3d(pline[0]),
        convert_point3d(pline[1]),
        convert_point3d(pline[2])
    )

def convert_from_mesh(mesh: rg.Mesh) -> typing.Tuple[MeshVertexCollection, MeshFaceCollection, MeshVertexConnectivity, typing.List[int]]:
    vertices = mesh_vertex_collection([convert_point3d(pt) for pt in mesh.Vertices])
    faces = mesh_face_collection([mesh_face(f.A, f.B, f.C) for f in mesh.Faces])
    connectivity = dict()
    for i in range(mesh.TopologyVertices.Count):
        # get neighbor vertices sorted
        neighbor_indices = mesh.TopologyVertices.ConnectedTopologyVertices(i, True)
        connectivity_pairs = []
        for index, ni in enumerate(neighbor_indices):
            ni_next = neighbor_indices[(index + 1) % len(neighbor_indices)]
            connectivity_pairs.append([ni, ni_next])

        connectivity[i] = connectivity_pairs

    boundary_indices = [i for (i, status) in enumerate(mesh.GetNakedEdgePointStatus()) if status]
    return (vertices, faces, connectivity, boundary_indices)

def convert_to_mesh(
    vertices: MeshVertexCollection,
    faces: MeshFaceCollection
) -> rg.Mesh:

    mesh = rg.Mesh()

    for vertex in vertices:
        mesh.Vertices.Add(vertex[0], vertex[1], vertex[2])

    for face in faces:
        # we have to explicitly convert np.int64 to a python integer,
        # otherwise the rhinocommon call fails
        mesh.Faces.AddFace(int(face[0]), int(face[1]), int(face[2]))

    mesh.Normals.ComputeNormals()
    mesh.Compact()

    return mesh

class NumpyArrayEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return JSONEncoder.default(self, obj)