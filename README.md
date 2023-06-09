# MinSrfLib

A library to minimize to *surface area* of a given triangular mesh.

![Example minimization, animated](images/moneyshot_ani.gif)

![Example minimization, end frame](images/smoothed_end_frame.png)

![Example minimization, circles](images/otto_circles.png)

## Installation

This application relies on a few pre-existing libraries that must be present on your current python environment. Please refer to their documentation on how to properly install them:

- [ghhops-server-py](https://github.com/mcneel/compute.rhino3d/tree/master/src/ghhops-server-py)
- [Flask](https://flask.palletsprojects.com/en/2.2.x/installation/)
- [Numpy](https://numpy.org/install/)
- [rhinoinside](https://pypi.org/project/rhinoinside/)

Additionally the following applications are used to leverage the functionalities of `MinSrfLib`:

- Rhinoceros *Version 7 SR21(7.21.22208.13001, 2022-07-27)*
- Hops *Version 0.15.1*
- Grasshopper *Build 1.0.0007*

## Usage

To start generating minimal surfaces, follow these steps:

1. Start Rhino and Grasshopper
2. Start the *hops component server* defined in `components.py`
3. Place a *Hops* component on the grasshopper canvas and point it towards the `/minimize` endpoint
4. Load a mesh from rhino, or create one dynamically in grasshopper
5. *(Optionally)* define some *boundary conditions* for simulation to adhere to
6. Connect all inputs to the *Hops* component to start the simulation

### Starting the hops component server

To start the *hops component server* navigate to the `MinSrfLib` folder, activate your python environment and run the `components.py` script.

```sh
conda activate your-python-environment-for-minsrflib
python components.py
```

![Visual aid of how to run the hops component server](images/run-hops-server.png)

### Connecting a hops component to the component server

To connect a hops component to the *hops component server*, you need to point it's *path* property to the corresponding endpoint defined on the server. In the case of the `minimize` function, this endpoint is defined at `http://localhost:5000/minimize`. Other functions will have other endpoint names.

![Placing a new hops component on the gh canvas](images/set-hops-endpoint-01.png)

![Connecting the component to the `minimize` endpoint](images/set-hops-endpoint-02.png)

## Simulation component

To run a simulation, the hops component for the `/minimize` endpoint expects 4 inputs:

- Mesh, the mesh to minimize. This **must** be triangulated and have only **unique** vertices
- Tolerance, the tolerance to use for area comparison. Since the minimzation is iteratively, the area after ever step is compared to the area before that step. If the difference is less than the tolerance value, the calculation is stopped immediately.
- Iterations, the maximum number of iterations
- Boundary conditions, the boundary conditions that should act on individual vertices of the mesh. Typically you would at least define a few *vertex anchors* to not have the simulation collapse on itself.

![A simple minimization simulation](images/simple-minimization-screencap.png)

## Boundary Condition components

In `MinSrfLib`, there are several options to define certain *boundaries* the simulation **must** adhere to:

- Vertex anchors, those anchors will never move during the simulation
- *Partial* vertex anchors, those anchors constrain their vertices in any combination of global $x$, $y$ and $z$ direction
- On circle, will constrain the given vertices to a circle boundary
- On line, will constrain the given vertices to a line **(WIP)**

### Vertex Anchors

To define vertex anchors, point a hops component to the endpoint `http://localhost:5000/vertex_anchor`. The resulting component exposes 5 inputs:

- Point, the point to constrain
- Index, the index of the point as a vertex in the mesh to minimize
- Fix X, if the point can or cannot move in global $X$ direction
- Fix Y, if the point can or cannot move in global $Y$ direction
- Fix Z, if the point can or cannot move in global $Z$ direction

The output of the component is a *json* serialized representation of an instance of the `VertexAnchorCondition` class. The `minimize` component expects a list of those class instances in their *json* serialized form.

![A simple, single vertex anchor, fully constrained](images/vertex_anchor.png)

### Partial Vertex Anchors

Here users have the opportunity to constrain vertices to any combination of the global coordinate axes. This can be useful to keep vertices on a conceptual grid f.e.

![Comparison, inner vertices free / constrained in x direction](images/vertex-x-constrained.png)

As shown in the example, the first simulation has the inner vertices free, which will typically yield better simulation results, while the second (lower) simulation constrained the inner vertices in one direction, keeping the initial grid the vertices layed on intact in the front view.

### On circle

To define a `OnCircle` constraint for a given vertex, point a hops component to the `http://localhost:5000/on_circle_constraint` endpoint. The resulting component exposes 3 inputs:

- Point, the point to constrain
- Index, the index of the point in the mesh to minimize
- Circle, the circle to constrain the point t

When minimizing, it is guaranteed that the vertices will respect the circle boundary on which they can travel. Thus this constraint is a bit softer than the `VertexAnchor`, while still ensuring vertices to stay on a given boundary. The output of the component is a *json* serialized instance of the `OnCircleBoundaryCondition` class.

![A simple, single vertex constrained to be on a circle](images/on_circle_component.png)

### On Line

wip

