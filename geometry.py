import typing
import numpy as np
import numpy.typing as npt

Point = npt.NDArray[np.float64]
def point(x: float, y: float, z: float) -> Point:
    """Helper function to construct a point from it's coordinates"""
    return np.array([x, y, z])

def point_dist(a: Point, b: Point) -> float:
    """
    Calculate the distance between two points with the pythagorean formula
    """
    return np.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2 + (a[2] - b[2])**2)

Triangle = npt.NDArray[np.float64]
def triangle(a: Point, b: Point, c: Point) -> Triangle:
    """Helper function to construct a triangle from it's corner points"""
    return np.array([a, b, c])

def triangle_area(tri: Triangle) -> float:
    """
    Calculate triangle area with herons formula
    """
    ab = point_dist(tri[0], tri[1])
    bc = point_dist(tri[1], tri[2])
    ca = point_dist(tri[2], tri[0])

    s = (ab + bc + ca) / 2.0

    return np.sqrt(s * (s - ab) * (s - bc) * (s - ca))

def triangle_area_cross(tri: Triangle) -> float:
    """
    Improved triangle area function using the cross product.
    Super quick
    """
    jk = tri[2] - tri[1]
    ji = tri[2] - tri[0]

    return 0.5 * np.linalg.norm(np.cross(jk, ji))

def triangle_areas_nested(triangles: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
    jk = triangles[:,:,2] - triangles[:,:,1]
    ji = triangles[:,:,2] - triangles[:,:,0]

    print(jk)
    print(ji)

    # TODO: Make this work on the nested structure coming in.
    # Right now, it computes a single value instead of one for each triangle
    return 0.5 * np.linalg.norm(np.cross(jk, ji))

MeshVertexCollection = npt.NDArray[np.float64]
def mesh_vertex_collection(points):
    return np.array(points)

MeshVertexConnectivity = typing.Dict[int, typing.List[int]]
def get_onering_neighbors_indices(index: int, connectivity: MeshVertexConnectivity) -> npt.NDArray[np.int64]:
    result = []
    for neighbor_indices in connectivity[index]:
        tri = [index]
        tri.extend(neighbor_indices)
        result.append(tri)
    return np.array(result)

def get_onering_neighbors(index: int, vertices: MeshVertexCollection, connectivity: MeshVertexConnectivity) -> npt.NDArray[np.float64]:
    """
    Get the one-ring neighbors around a given vertex.
    This will be a numpy array of Triangles
    """
    result = [vertices[i] for i in [pair for pair in get_onering_neighbors_indices(index, connectivity)]]
    return np.array(result)

MeshFace = npt.NDArray[np.int64]
def mesh_face(a: np.int64, b: np.int64, c: np.int64) -> MeshFace:
    return np.array([a, b, c])
MeshFaceCollection = npt.NDArray[np.int64]
def mesh_face_collection(faces) -> MeshFaceCollection:
    return np.array(faces)

def mesh_faces(vertices: MeshVertexCollection, faces: MeshFaceCollection) -> npt.NDArray[np.float64]:
    result = np.array([[vertices[f[0]], vertices[f[1]], vertices[f[2]]] for f in faces])
    return result
    
    
def mesh_area(vertices: MeshVertexCollection, faces: MeshFaceCollection) -> float:
    return np.sum([triangle_area_cross(f) for f in mesh_faces(vertices, faces)])

if __name__ == "__main__":

    a = point(0.0, 0.0, 0.0)
    b = point(2.0, 0.0, 0.0)
    c = point(1.0, 1.0, 0.0)

    tri = triangle(a, b, c)
    print(tri)

    print(triangle_area_cross(tri))

    connectivity = {
        0: [[1, 2]],
        1: [[2, 0]],
        2: [[0, 1]]
    }

    collection = mesh_vertex_collection([a, b, c])

    face = mesh_face(0, 1, 2)
    faces = mesh_face_collection([face])
    # print(faces)

    # print(mesh_faces(collection, faces))

    # print(mesh_area(collection, faces))

    tri = mesh_faces(collection, faces)
    test_faces = np.array([tri.copy(), tri.copy(), tri.copy()])
    print(test_faces)

    # print(test_faces[:,:,0])
    # print(test_faces[:,:,1])

    print(triangle_areas_nested(test_faces))