# Topic

In the module *S9 - Computational optimization* I take a deeper look at the theory behind minimal surfaces and will develop a simple *polygon mesh based* solver integrated into the *Rhinoceros* and *Grasshopper* software package. This solver will be able to process arbitrary three dimensional polygon meshed, as long as they are triangular and have only **unique** vertices.

## Minimal surfaces

A surface is considered *minimal*, if it's *mean curvature* $c$ is 0 at any given point on the surface. This property also ensures that if we compare a minimal surface to another one spanning the same space, the area $A_{min}$ of the minimal surface will be smaller as the area of the other surface. If we consider a surface to be parametrized over it's $u$ and $v$ domain $D$, this gives:

$$c_{u,v} = 0 , \forall u,v \in D&&

### A simplification

For my solver, I simplify the representation of a surface to that of a *triangulated* polygon mesh, where all it's vertices lie on the target surface. The area of a triangle mesh can be simply calculated by calculating the sum of areas of all it's triangular faces.