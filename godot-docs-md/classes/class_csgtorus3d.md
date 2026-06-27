# CSGTorus3D

**Inherits:** `CSGPrimitive3D` **<** `CSGShape3D` **<** `GeometryInstance3D` **<** `VisualInstance3D` **<** `Node3D` **<** `Node` **<** `Object`

A CSG Torus shape.

## Description

This node allows you to create a torus for use with the CSG system.

**Note:** CSG nodes are intended to be used for level prototyping. Creating CSG nodes has a significant CPU cost compared to creating a `MeshInstance3D` with a `PrimitiveMesh`. Moving a CSG node within another CSG node also has a significant CPU cost, so it should be avoided during gameplay.

## Tutorials

- `Prototyping levels with CSG `

## Property Descriptions

`float` **inner_radius** = `0.5`

- `void (No return value.)` **set_inner_radius**(value: `float`)
- `float` **get_inner_radius**()

The inner radius of the torus.

`Material` **material**

- `void (No return value.)` **set_material**(value: `Material`)
- `Material` **get_material**()

The material used to render the torus.

`float` **outer_radius** = `1.0`

- `void (No return value.)` **set_outer_radius**(value: `float`)
- `float` **get_outer_radius**()

The outer radius of the torus.

`int` **ring_sides** = `6`

- `void (No return value.)` **set_ring_sides**(value: `int`)
- `int` **get_ring_sides**()

The number of edges each ring of the torus is constructed of.

`int` **sides** = `8`

- `void (No return value.)` **set_sides**(value: `int`)
- `int` **get_sides**()

The number of slices the torus is constructed of.

`bool` **smooth_faces** = `true`

- `void (No return value.)` **set_smooth_faces**(value: `bool`)
- `bool` **get_smooth_faces**()

If `true` the normals of the torus are set to give a smooth effect making the torus seem rounded. If `false` the torus will have a flat shaded look.